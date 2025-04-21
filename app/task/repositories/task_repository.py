from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session, joinedload, aliased

from ..schemas import TaskCreateRequest, TaskDetailResponse, TaskFilters, TaskItemResponse, TaskUpdateRequest
from ..models import Task as db_Task
from ...models_db import Project, User, UserProjectAssociation
from ...user.user_repository import UserRepository

User_owner = aliased(User)
User_performer = aliased(User)

class TaskRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_task(self, task_id: int) -> TaskDetailResponse|None:
        result = (
        self.db.query(
            db_Task,
            User.id.label('owner_id'),
            User.login.label('owner_email'),
            User.username.label('owner_name'),
            User_performer.id.label('performer_id'),
            User_performer.login.label('performer_email'),
            User_performer.username.label('performer_name'),
            Project.name.label('project_name')
        )
        .filter(db_Task.id == task_id)
        .join(User, db_Task.owner_id == User.id)  
        .outerjoin(User_performer, db_Task.performer_id == User_performer.id)  
        .join(Project, db_Task.project_id == Project.id)  
        .first()
        )
        if not result:
            return None
        task, owner_id, owner_email, owner_name, performer_id, performer_email, performer_name, project_name = result
        task.owner_id = owner_id
        task.owner_email = owner_email
        task.owner_name = owner_name
        task.performer_id = performer_id
        task.performer_email = performer_email if performer_email else None
        task.performer_name = performer_name if performer_name else None
        task.project_name = project_name
        return TaskDetailResponse(
            id=task.id,
            name=task.name,
            status=task.status,
            indicator=task.indicator,
            created_at=task.created_at,
            last_change=task.last_change,
            deadline=task.deadline,
            description=task.description,
            author_id=task.owner_id,
            author_name=task.owner_name,
            author_email=task.owner_email,
            performer_id=task.performer_id,
            performer_name=task.performer_name,
            performer_email=task.performer_email,
            project_id=task.project_id,
            project_name=task.project_name,
            parent_task_id=task.parent_task_id
        )

    # def get_user_tasks(self, user_id: str) -> list[db_Task]:
    #     tasks = self.db.query(
    #         db_Task.id,
    #         db_Task.name,
    #         db_Task.indicator,  
    #         db_Task.description,  
    #         User.login.label('author_email'), 
    #         User.username.label('author_name')  
    #     ).join(
    #         User, db_Task.owner_id == User.id 
    #     ).join(Project, db_Task.project_id == Project.id
    #     ).join(UserProjectAssociation,
    #         (Project.id == UserProjectAssociation.project_id) &
    #         (UserProjectAssociation.user_id == User.id)
    #     ).filter(
    #         (db_Task.performer_id == user_id) &
    #         (User.id == user_id)
    #     ).all()
    #     return tasks

    def get_project_tasks(self, project_id):
        tasks = self.db.query(
            db_Task.id,
            db_Task.name,
            db_Task.indicator,  
            db_Task.description,  
            User.login.label('author_email'), 
            User.username.label('author_name') 
        ).join(
            User,  
            db_Task.owner_id == User.id  
        ).filter(db_Task.project_id == project_id).all()
        return tasks
    
    def get_owner_task(self, task_id: int, user_id) -> db_Task:
        if not UserRepository(self.db).check_admin_perms(user_id):
            return self.db.query(db_Task).filter(db_Task.id==task_id).first()
        task = self.db.query(db_Task).filter(db_Task.id==task_id,
        db_Task.owner_id==user_id).first()
        return task
    
    def get_accessed_tasks_filter(self, user_id: int, 
        filters: Optional[TaskFilters] = None) -> List[TaskItemResponse]:
        if not UserRepository(self.db).check_admin_perms(user_id):
            query = self.db.query(db_Task).join(
            UserProjectAssociation,
            UserProjectAssociation.project_id == db_Task.project_id
            ).filter(
                UserProjectAssociation.user_id == user_id
            )
        else:
            query = self.db.query(db_Task)
        if filters:
            if filters.status:
                query = query.filter(db_Task.status.in_(filters.status))
            if filters.name:
                query = query.filter(db_Task.name.ilike(f"%{filters.name}%"))
            if filters.project_id:
                query = query.filter(db_Task.project_id == filters.project_id)
            if filters.indicator:
                query = query.filter(db_Task.indicator.in_(filters.indicator))
            if filters.on_me:
                query = query.filter(db_Task.performer_id == user_id)
            if filters.owner_id: 
                query = query.filter(db_Task.owner_id == filters.owner_id)
            if filters.parent_task_id:
                query = query.filter(db_Task.parent_task_id == filters.parent_task_id)
            if filters.sort_by:
                sort_field = None
                if filters.sort_by == "created_at":
                    sort_field = db_Task.created_at
                elif filters.sort_by == "last_change":
                    sort_field = db_Task.last_change
                elif filters.sort_by == "deadline":
                    sort_field = db_Task.deadline
                if sort_field:
                    if filters.sort_order == "desc":
                        query = query.order_by(desc(sort_field))
                    else:
                        query = query.order_by(asc(sort_field))
        tasks = query.all()
        return [
            TaskItemResponse(
                id=task.id,
                name=task.name,
                status=task.status,
                indicator=task.indicator,
                created_at=task.created_at,
                last_change=task.last_change,
                deadline=task.deadline,
                description=task.description,
                project_id=task.project_id,
                owner_id=task.owner_id,
                performer_id=task.performer_id,
                parent_task_id=task.parent_task_id
            ) for task in tasks
        ]
    
    def create_task(self, project_id: int, task_data: TaskCreateRequest, user_id: int) -> int:
        task = db_Task(
            name=task_data.name,
            description=task_data.description,
            deadline=task_data.deadline,
            indicator=task_data.indicator,
            owner_id=user_id,
            performer_id=task_data.performer_id,
            project_id=project_id,
            parent_task_id=task_data.parent_task_id
        )
        self.db.add(task)
        self.db.commit()
        return task.id

    def update_task(self, task_id: int, task_data: TaskUpdateRequest) -> int:
        task = self.db.query(db_Task).filter(db_Task.id == task_id).first()
        if task_data.name is not None:
            task.name = task_data.name
        if task_data.description is not None:
            task.description = task_data.description
        if task_data.deadline is not None:
            task.deadline = task_data.deadline
        if task_data.performer_id is not None:
            task.performer_id = task_data.performer_id
        if task_data.indicator is not None:
            task.indicator = task_data.indicator
        if task_data.status:
            task.status = task_data.status
        task.last_change = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(task)
        return task.id
    
    def delete_task(self, task_id: int):
        task = self.db.query(db_Task).filter(db_Task.id == task_id).first()
        self.db.delete(task)
        self.db.commit()