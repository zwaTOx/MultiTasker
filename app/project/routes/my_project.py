from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Annotated, List

from ...project.schemas import MyProjectResponse
from ...project.service.project_service import ProjectService
from ...user.user_repository import UserRepository
from ..project_repository import ProjectRepository
from ...user.user_project_association_repo import UserProjectAssociation
from ...auth.auth import get_current_user
from ...models_db import Project as db_project
from ...models_db import Category as db_category
from ...database import engine, Sessionlocal
from ..models import CreateProjectRequest, UpdateProjectRequest

router = APIRouter(
    prefix="/my/projects",
    tags=['MyProject']
)

def get_db():
    db = Sessionlocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@router.get('/', response_model=List[MyProjectResponse])
async def get_my_projects(user: user_dependency, db: db_dependency):
    projects = ProjectService(db).get_my_projects_service(user['id'])
    return projects

@router.post('/')
async def create_project(
        project_data: CreateProjectRequest, 
        user: user_dependency, 
        db: db_dependency,
        category_id: int = Query(None)):
    try:
        project = ProjectService(db).create_project_service(user['id'], project_data, category_id)
        return {"message": "Project created successfully", 
            "project_id": project.id}
    except ValueError as e:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, 
            detail=str(e)
        )    
            
@router.put('/{project_id}')
async def update_project(project_id: int, project_data: UpdateProjectRequest, user: user_dependency, db: db_dependency):
    is_admin = UserRepository(db).check_admin_perms(user['id'])
    if is_admin:
        project = db.query(db_project).filter(db_project.id == project_id).first()
    else:
        project = db.query(db_project).filter(
            db_project.id == project_id,
            db_project.user_id == user['id']
        ).first()
    if not project:
        raise HTTPException(status_code=404, detail='Project not found')
    if project_data.name is not None:
        project.name = project_data.name
    if project_data.icon_id is not None:
        project.icon_id = project_data.icon_id
    db.commit()
    db.refresh(project)
    return {"message": "Project updated successfully", 
            "category": {"id": project.id, "name": project.name, "icon_id": project.icon_id}}

@router.delete('/', status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id, user: user_dependency, db: db_dependency):
    is_admin = UserRepository(db).check_admin_perms(user['id'])
    if is_admin:
        project = db.query(db_project).filter(db_project.id == project_id).first()
    else:
        project = db.query(db_project).filter(
            db_project.id == project_id,
            db_project.user_id == user['id']
        ).first()
    if project is None:
        raise HTTPException(status_code=404 ,detail = 'Project not found')
    db.delete(project)
    db.commit()
    return {"message": f"Project {project_id} deleted successfully"}
