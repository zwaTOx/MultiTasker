
from fastapi import Depends, HTTPException, status
from typing import Optional

from ...project.project_repository import ProjectRepository
from ...user.user_project_association_repo import UserProjectAssociation
from ...task.repositories.task_repository import TaskRepository
#from models import db_Task
from ..schemas import TaskDetailResponse, TaskFilters

class TaskService:
    def __init__(self, db):
        self.db = db
    
    def get_task_service(self, task_id: int, user_id: int) -> Optional[TaskDetailResponse]:
        task = TaskRepository(self.db).get_task(task_id)
        
        if task is None:
            raise ValueError("Task not found")
            
        if not UserProjectAssociation(self.db).check_user_in_project(user_id, task.project_id):
            raise PermissionError("Access denied to project")
            
        project = ProjectRepository(self.db).get_project(task.project_id)
        if project is None:
            raise ValueError("Project not found")
        return task
    
    def get_tasks_service(self, user_id, filters: TaskFilters = Depends()):
        tasks = TaskRepository(self.db).get_accessed_tasks_filter(user_id, filters)
        return tasks