from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Annotated, List, Optional
from datetime import datetime, timedelta, timezone

from ..task.service.task_service import TaskService
from ..project.project_repository import ProjectRepository 
from ..auth.auth import get_current_user
from ..user.user_project_association_repo import UserProjectAssociation
from ..models_db import User as db_user
from ..models_db import Project as db_project
from ..database import engine, Sessionlocal
from .schemas import TaskCreateRequest, TaskDetailResponse, TaskFilters, TaskItemResponse, TaskResponseSchema, TaskUpdateRequest
from .repositories.task_repository import TaskRepository
from ..user.user_repository import UserRepository
from pydantic import BaseModel

router = APIRouter(
    prefix="/tasks",
    tags=['Task']
)

def get_db():
    db = Sessionlocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@router.get('/', response_model = List[TaskItemResponse]) 
async def get_tasks_v2(user: user_dependency, db: db_dependency,
    filters: TaskFilters = Depends()):
    tasks = TaskService(db).get_tasks_service(user['id'], filters)
    return tasks

@router.get('/{task_id}', response_model=TaskDetailResponse)
async def get_task(task_id: int, user: user_dependency, db: db_dependency):
    try:
        task = TaskService(db).get_task_service(task_id, user['id'])
        return task
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

@router.post('/{project_id}')
async def create_task(project_id: int, task_data: TaskCreateRequest, 
    user: user_dependency, db: db_dependency):
    try:
        task_id = TaskService(db).create_task_service(user['id'], project_id, task_data)
        return {
            "message": "Task created successfully", 
            "task_id": task_id
            }
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

@router.put('/{task_id}')
async def update_task(task_id: int, task_data: TaskUpdateRequest, user: user_dependency, db: db_dependency):
    try:
        task_id = TaskService(db).update_task_service(user['id'], task_id, task_data)
        return {
            "message": "Task created successfully", 
            "task_id": task_id
            }
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

@router.delete('/{task_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id, user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Auth failed')
    task = TaskRepository(db).get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail='Task not found')
    if not UserProjectAssociation(db).check_user_in_project(user['id'], task.project_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Вы не являетесь участником этого проекта")
    is_task_owner = (task.owner_id == user['id'])
    is_project_owner = ProjectRepository(db).check_project_owner(user['id'], task.project_id)
    if not (is_task_owner or is_project_owner):
        raise HTTPException(
            status_code=403,
            detail="Недостаточно прав для удаления задачи"
        )
    TaskRepository(db).delete_task(task)
    return {"message": f"Task {task_id} deleted successfully"}