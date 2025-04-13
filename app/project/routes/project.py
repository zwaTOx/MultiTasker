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
    try: 
        projects = ProjectService(db).get_projects_service(user['id'], category_id)
        return projects
    except ValueError as e:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, 
            detail=str(e)
        )

@router.put('/{project_id}')
async def move_project_in_category(project_id: int, request: MoveProjectRequest, 
    user: user_dependency, db: db_dependency):  
    try:
        ProjectService(db).move_project_in_category_service(user['id'], project_id, request)
        return {"detail": "Project category successfully changed"}
    except ValueError as e:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, 
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )     
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 
    # category = db.query(db_category).filter(db_category.user_id==user['id'], 
    #     db_category.id==request.category_id).first()
    # if category is None:
    #     raise HTTPException(status_code=404 ,detail = 'Category not found')
    # if not ProjectRepository(db).check_project_existing(project_id):
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail="Проект не найден"
    #     )
    # if not UserProjectAssociation(db).check_user_in_project(user['id'], project_id):
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Пользователь не является участником проекта"
    #     )
    # if not UserProjectAssociation(db).change_project_category(user['id'], project_id, request.category_id):
    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail="Не удалось изменить категорию"
    #     )
    # return {"detail": "Категория проекта успешно изменена"}
