import datetime
import os
from typing import List
from dotenv import load_dotenv
from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from ...auth.code_service import CodeService
from ...email_controller import send_project_invite
from ...project.project_repository import ProjectRepository
from ...user.user_project_association_repo import UserProjectAssociation
from ..schemas import CreateUser, UserResponse
from ..user_repository import UserRepository
from ...exceptions import ProjectNotFound, UserNotFound

load_dotenv()
TEMP_TOKEN_EXPIRE_MINUTES = int(os.getenv('TEMP_TOKEN_EXPIRE_MINUTES'))
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES'))

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

class UserService:
    def __init__(self, db: Session):
        self.db = db

    def create_user(self, create_user_rq: CreateUser) -> tuple[int, str]:
        try:
            existing_user = UserRepository(self.db).get_user_by_email(create_user_rq.login)
        except UserNotFound:
            new_user = UserRepository(self.db).create_user(create_user_rq.login, create_user_rq.password)
            return new_user.id, "User successfully created"
        if existing_user and existing_user.is_verified is True:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        UserRepository(self.db).reset_user_password(create_user_rq.password)
        UserRepository(self.db).verify_user(create_user_rq.login)
        return existing_user.id, "User verified successfully"
        

    def login_user(self, username, password) -> str:
        user = UserRepository(self.db).auth_user(username, password)
        if user.is_verified is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email is not verified"
            )
        token = CodeService(self.db).create_access_token(user.login, user.id, 
            datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        return token

    def get_users_service(self, user_id: int, project_id: int = None) -> List[UserResponse]:
        if project_id is not None:
            if not UserProjectAssociation(self.db).check_user_in_project(user_id, project_id):
                raise HTTPException(status_code=403, detail="Access is denied")
            project = ProjectRepository(self.db).get_project(project_id) 
            users = UserProjectAssociation(self.db).get_users_in_project(project.id)
        else:
            users = UserRepository(self.db).get_users()
        return users or []
    
    def invite_user(self, user: dict, 
        request: Request,
        project_id: int, 
        inv_user_id: int = None, 
        user_email: str = None):
        if not ProjectRepository(self.db).check_project_owner(user['id'], project_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to add a user to the project."
            )
        try:
            invited_user = UserRepository(self.db).get_user(inv_user_id)
        except UserNotFound:
            invited_user = UserRepository(self.db).create_unverified_user(user_email)
            inv_user_id = invited_user.id
        project = ProjectRepository(self.db).get_project(project_id)
        existing_assoc = UserProjectAssociation(self.db).check_user_in_project(inv_user_id, project_id)
        if existing_assoc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The user is already a member of the project"
            )
        access_token = CodeService(self.db).create_invite_project_token(project_id=project_id, 
            id=inv_user_id, 
            expires_delta=datetime.timedelta(minutes=TEMP_TOKEN_EXPIRE_MINUTES)
        )
        url = f"{request.base_url}/users/invite?access_token={access_token}"
        result = send_project_invite(recipient_email=invited_user.login, 
            inviter_name=user['login'], 
            url=url, 
            expire_in_minutes=TEMP_TOKEN_EXPIRE_MINUTES,
            project_name=project.name)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"Couldn't send email"
                )

    def confirm_invite(self, access_token: str) -> tuple[int, int]:
        token_data =  CodeService(self.db).decode_and_verify_invite_token(access_token)
        if not token_data:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid or expired token")
        user_id = token_data.get('id')
        project_id = token_data.get('project_id')
        if UserProjectAssociation(self.db).check_user_in_project(user_id, project_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The user is already a member of the project"
            )
        UserProjectAssociation(self.db).add_user_in_project(user_id, project_id)
        return user_id, project_id

    def leave_project(self, user_id: int, project_id: int):
        if not UserProjectAssociation(self.db).check_user_in_project(user_id, project_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The user is not a member of the project"
            )
        project = ProjectRepository(self.db).get_project(project_id)
        if user_id == project.owner_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You are the owner of the project. The project must be deleted in order to leave it."
            )
        UserProjectAssociation(self.db).leave_project(user_id, project_id)

    def kick_user_from_project(self, req_id: int, user_id, project_id: int):
        if not ProjectRepository(self.db).check_project_owner(req_id, project_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not the owner of the project or admin"
            )
        ProjectRepository(self.db).check_project_existing(project_id)
        if not UserProjectAssociation(self.db).check_user_in_project(user_id, project_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The user is not in the project"
            )
        if user_id == req_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You can't kick yourself out of the project"
            )
        UserProjectAssociation(self.db).leave_project(user_id, project_id)

    def update_admin(self, user_id: int, upd_user_id: int, is_admin: bool):
        if not UserRepository(self.db).check_admin_perms(user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access is denied"
            )
        target_user = UserRepository(self.db).get_user(upd_user_id)
        UserRepository(self.db).update_admin(target_user.id, is_admin)