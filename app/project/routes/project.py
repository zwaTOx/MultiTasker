from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Annotated

from ..project_repository import ProjectRepository
from ...user.user_project_association_repo import UserProjectAssociation
from ...auth.auth import get_current_user
from ...models_db import Category as db_category
from ...database import engine, Sessionlocal
from ..models import MoveProjectRequest

router = APIRouter(
    prefix="/projects",
    tags=['Project']
)

def get_db():
    db = Sessionlocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@router.get('/')
async def get_projects(user: user_dependency, db: db_dependency, 
    category_id: int = Query(None)):
    if category_id:
        category = db.query(db_category).filter(db_category.user_id==user['id'], 
        db_category.id==category_id).first()
        if category is None:
            raise HTTPException(status_code=404 ,detail = 'Category not found')
        projects = UserProjectAssociation(db).get_accessed_projects_by_category(user['id'], category_id)
        return projects
    projects = UserProjectAssociation(db).get_accessed_projects(user['id'])
    return projects

@router.put('/{project_id}')
async def move_project_in_category(project_id: int, request: MoveProjectRequest, 
    user: user_dependency, db: db_dependency):  
    category = db.query(db_category).filter(db_category.user_id==user['id'], 
        db_category.id==request.category_id).first()
    if category is None:
        raise HTTPException(status_code=404 ,detail = 'Category not found')
    if not ProjectRepository(db).check_project_existing(project_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Проект не найден"
        )
    if not UserProjectAssociation(db).check_user_in_project(user['id'], project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Пользователь не является участником проекта"
        )
    if not UserProjectAssociation(db).change_project_category(user['id'], project_id, request.category_id):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось изменить категорию"
        )
    return {"detail": "Категория проекта успешно изменена"}
