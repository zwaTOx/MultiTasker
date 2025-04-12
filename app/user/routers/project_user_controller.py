import datetime
import os
import uuid
from fastapi import APIRouter, FastAPI, Depends, HTTPException, status, Request, Query
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated, List, Optional

from ...notification.notification_repository import NotificationRepository
from ...user.schemas import UserResponse
from ...models_db import Project
from ..user_repository import UserRepository
from ...database import engine, Sessionlocal
from ...auth.auth import create_access_token, create_invite_project_token, decode_and_verify_invite_token, get_current_user, bcrypt_context
from ...email_controller import send_project_invite
from ..user_project_association_repo import UserProjectAssociation 
from ...project.project_repository import ProjectRepository

router = APIRouter(
    tags=['ProjectUserContoller']
)

def get_db():
    db = Sessionlocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@router.get('/users', response_model=List[UserResponse])
async def get_users(
    user: user_dependency,
    db: db_dependency,
    project_id: Optional[int] = Query(None)
):
    if project_id is not None:
        if not UserProjectAssociation(db).check_user_in_project(user['id'], project_id):
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        project = ProjectRepository(db).get_project(project_id) 
        if project is None:
            raise HTTPException(status_code=404, detail="Проект не найден")
        users = UserProjectAssociation(db).get_users_in_project(project_id)
    else:
        users = UserRepository(db).get_users()
    if not users:
        return []
    result = []
    for user in users:
        user_data = user._asdict()
        if 'user_id' in user_data:
            user_data['id'] = user_data.pop('user_id')  
        result.append(UserResponse(**user_data))
    
    return result
@router.post('/users/{user_id}/invite')
def invite_in_project(request: Request,  
        project_id: int, 
        user: user_dependency, 
        db: db_dependency,
        inv_user_id: int = Query(None),
        user_email: str = Query(None)):
    TEMP_TOKEN_EXPIRE_MINUTES = 10
    if not ProjectRepository(db).check_project_owner(user['id'], project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не являетесь создателем этого проекта"
        )
    invited_user = UserRepository(db).get_user(inv_user_id)
    if not invited_user:
        invited_user = UserRepository(db).create_unverified_user(user_email)
        inv_user_id = invited_user.id
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден"
        )
    existing_assoc = UserProjectAssociation(db).check_user_in_project(inv_user_id, project_id)
    if existing_assoc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь уже является участником проекта"
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
    # NotificationRepository(db).create_notification(inv_user_id, text=\
    #     f'Тебя пригласили в проект "{project.name}"!')
    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"An unexpected error occurred."
            )
    return {
        "message": "Пользователь отправлено приглашение в проект"
    }

@router.post('/users/confirm/{access_token}')
def confirm_invite(access_token: str, db: db_dependency):
    token_data = decode_and_verify_invite_token(access_token)
    if not token_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
        detail="Недействительный или просроченный токен")
    user_id = token_data.get('id')
    project_id = token_data.get('project_id')
    if UserProjectAssociation(db).check_user_in_project(user_id, project_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь уже является участником проекта"
        )
    UserProjectAssociation(db).add_user_in_project(user_id, project_id)
    return {'user_id': user_id,
        "project_id": project_id}

@router.delete('/projects/{project_id}/leave', status_code=status.HTTP_204_NO_CONTENT)
def leave_project(project_id: int, user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Auth failed')
    if not UserProjectAssociation(db).check_user_in_project(user['id'], project_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь не является участником проекта"
        )
    if not ProjectRepository(db).check_project_existing(project_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден"
        )
    UserProjectAssociation(db).leave_project(user['id'], project_id)

@router.delete('/projects/{project_id}/kick/{user_id}', status_code=status.HTTP_204_NO_CONTENT)
def kick_from_project(project_id: int, user_id: int, user: user_dependency, db: db_dependency):
    if not ProjectRepository(db).check_project_owner(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не являетесь владельцем проекта"
        )
    if not ProjectRepository(db).check_project_existing(project_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден"
        )
    if user_id == user['id']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Кикнуть себя из проекта нельзя"
        )
    UserProjectAssociation(db).leave_project(user_id, project_id)
    