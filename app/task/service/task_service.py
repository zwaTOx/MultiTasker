
from fastapi import Depends, HTTPException, status
from typing import Optional

from ...user.user_repository import UserRepository
from ...project.project_repository import ProjectRepository
from ...user.user_project_association_repo import UserProjectAssociation
from ...task.repositories.task_repository import TaskRepository
#from models import db_Task
from ..schemas import TaskCreateRequest, TaskDetailResponse, TaskFilters, TaskUpdateRequest

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
    
    def create_task_service(self, user_id: int, project_id: int, task_data: TaskCreateRequest):
        if not UserProjectAssociation(self.db).check_user_in_project(user_id, project_id):
            raise PermissionError("Access denied to project")
        performer_user = UserRepository(self.db).get_user(task_data.performer_id)
        if performer_user is None:
            #Отправить письмо на email
            task_data.performer_id = user_id
        project = ProjectRepository(self.db).get_project(project_id)
        if project is None:
            raise ValueError("Project not found")
        task_id = TaskRepository(self.db).create_task(project_id, task_data, user_id)
        return task_id
    
    def update_task_service(self, user_id, task_id: int, task_data: TaskUpdateRequest):
        task = TaskRepository(self.db).get_task(task_id)
        if not UserProjectAssociation(self.db).check_user_in_project(user_id, task.project_id):
            raise PermissionError("Access denied to task")
        if task is None:
            raise ValueError("Task not found")
        is_task_owner = (task.author_id==user_id)
        is_project_owner = ProjectRepository(self.db).check_project_owner(user_id, task.project_id)
        if not (is_task_owner or is_project_owner):
            raise PermissionError("Insufficient permissions")
        task_id = TaskRepository(self.db).update_task(task.id, task_data)
        return task_id