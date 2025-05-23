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
from ..schemas import CreateProjectRequest, UpdateProjectRequest

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
    projects = ProjectService(db).get_my_projects(user['id'])
    return projects

@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_project(
        project_data: CreateProjectRequest, 
        user: user_dependency, 
        db: db_dependency,
        category_id: int = Query(None)):
    project = ProjectService(db).create_project(user['id'], project_data, category_id)
    return {"message": "Project created successfully", 
        "project_id": project.id}

@router.put('/{project_id}')
async def update_project(
        project_id: int, 
        project_data: UpdateProjectRequest, 
        user: user_dependency, 
        db: db_dependency):
    ProjectService(db).update_project(user['id'], project_id, project_data)
    return {"message": f"Project {project_id} updated successfully"}


@router.delete('/', status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
        project_id: int, 
        user: user_dependency, 
        db: db_dependency):
    ProjectService(db).delete_project(user['id'], project_id)
    return {"message": f"Project {project_id} deleted successfully"}
