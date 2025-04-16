import datetime
from typing import List
from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from ...email_controller import send_project_invite
from ...auth.auth import create_invite_project_token, decode_and_verify_invite_token

from ...project.project_repository import ProjectRepository
from ...user.user_project_association_repo import UserProjectAssociation
from ..schemas import UserResponse
from ..user_repository import UserRepository


class UserService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_users_service(self, user_id: int, project_id: int = None) -> List[UserResponse]:
        if project_id is not None:
            if not UserProjectAssociation(self.db).check_user_in_project(user_id, project_id):
                raise HTTPException(status_code=403, detail="Доступ запрещен")
            project = ProjectRepository(self.db).get_project(project_id) 
            if project is None:
                raise ValueError("Project not found")
            users = UserProjectAssociation(self.db).get_users_in_project(project_id)
        else:
            users = UserRepository(self.db).get_users()
        return users or []
    
    def invite_user(self, user: dict, 
        request: Request,
        project_id: int, 
        inv_user_id: int = None, 
        user_email: str = None):
        TEMP_TOKEN_EXPIRE_MINUTES = 10
        if not ProjectRepository(self.db).check_project_owner(user['id'], project_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to add a user to the project."
            )
        invited_user = UserRepository(self.db).get_user(inv_user_id)
        if not invited_user:
            invited_user = UserRepository(self.db).create_unverified_user(user_email)
            inv_user_id = invited_user.id
        project = ProjectRepository(self.db).get_project(project_id)
        if not project:
            raise ValueError("Project not found")
        existing_assoc = UserProjectAssociation(self.db).check_user_in_project(inv_user_id, project_id)
        if existing_assoc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The user is already a member of the project"
            )
        access_token = create_invite_project_token(project_id=project_id, 
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
        token_data = decode_and_verify_invite_token(access_token)
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
                detail="Пользователь не является участником проекта"
            )
        if not ProjectRepository(self.db).check_project_existing(project_id):
            raise ValueError('Project not found')
        UserProjectAssociation(self.db).leave_project(user_id, project_id)

    def kick_user_from_project(self, req_id: int, user_id, project_id: int):
        if not ProjectRepository(self.db).check_project_owner(req_id, project_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Вы не являетесь владельцем проекта"
            )
        if not ProjectRepository(self.db).check_project_existing(project_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Проект не найден"
            )
        if not UserProjectAssociation(self.db).check_user_in_project(user_id, project_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователя нет в проекте"
            )
        if user_id == req_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Кикнуть себя из проекта нельзя"
            )
        UserProjectAssociation(self.db).leave_project(user_id, project_id)