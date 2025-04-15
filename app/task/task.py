from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Annotated, List, Optional

from ..task.service.task_service import TaskService
from ..auth.auth import get_current_user
from ..database import engine, Sessionlocal
from .schemas import TaskCreateRequest, TaskDetailResponse, TaskFilters, TaskItemResponse, TaskResponseSchema, TaskUpdateRequest
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
            "message": "Task updated successfully", 
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
    try: 
        TaskService(db).delete_task_service(user['id'], task_id)
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
