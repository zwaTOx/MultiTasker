import datetime
from fastapi import APIRouter, FastAPI, Depends, HTTPException, status, Request, Query
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated, List, Optional

from ...user.service.user_service import UserService
from ...notification.notification_repository import NotificationRepository
from ...user.schemas import UserResponse
from ...models_db import Project
from ..user_repository import UserRepository
from ...database import engine, Sessionlocal
from ...auth.auth import get_current_user, bcrypt_context
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
    users = UserService(db).get_users_service(user['id'], project_id)
    return users

@router.post('/users/{user_id}/invite', status_code=status.HTTP_201_CREATED)
def invite_in_project(request: Request,  
        project_id: int, 
        user: user_dependency, 
        db: db_dependency,
        inv_user_id: int = Query(None),
        user_email: str = Query(None)):
    UserService(db).invite_user(user, request, project_id, inv_user_id, user_email)
    return {
        "message": "Пользователь отправлено приглашение в проект"
    }

@router.post('/users/confirm/{access_token}', status_code=status.HTTP_201_CREATED)
def confirm_invite(access_token: str, db: db_dependency):
    user_id, project_id = UserService(db).confirm_invite(access_token)
    return {'user_id': user_id,
        "project_id": project_id
    }

@router.delete('/projects/{project_id}/leave', status_code=status.HTTP_204_NO_CONTENT)
def leave_project(project_id: int, user: user_dependency, db: db_dependency):
    UserService(db).leave_project(user['id'], project_id)

@router.delete('/projects/{project_id}/kick/{user_id}', status_code=status.HTTP_204_NO_CONTENT)
def kick_from_project(project_id: int, user_id: int, user: user_dependency, db: db_dependency):
    UserService(db).kick_user_from_project(user['id'], user_id, project_id)
