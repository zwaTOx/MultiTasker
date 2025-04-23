from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Annotated, List

from ...project.schemas import ProjectWithMembershipResponse
from ...project.service.project_service import ProjectService
from ...auth.auth import get_current_user
from ...database import engine, Sessionlocal
from ..schemas import MoveProjectRequest

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

@router.get('/', response_model=List[ProjectWithMembershipResponse])
async def get_projects(user: user_dependency, db: db_dependency, 
    category_id: int = Query(None)):
    projects = ProjectService(db).get_projects(user['id'], category_id)
    return projects


@router.put('/{project_id}')
async def move_project_in_category(project_id: int, request: MoveProjectRequest, 
    user: user_dependency, db: db_dependency):  
    ProjectService(db).move_project_in_category(user['id'], project_id, request)
    return {"detail": "Project category successfully changed"}
