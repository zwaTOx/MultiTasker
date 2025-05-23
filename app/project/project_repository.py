from operator import and_
from typing import List
from sqlalchemy.orm import Session

from ..exceptions import AttachmentNotFound, ProjectNotFound
from ..user.attachment_repository import AttachmentRepository
from ..project.schemas import UpdateProjectRequest
from ..project.schemas import ProjectResponse, MyProjectResponse
from ..models_db import Project as db_project, UserProjectAssociation
from ..user.user_repository import UserRepository

class ProjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def check_project_owner(self, user_id: int, project_id) -> bool:
        project = self.db.query(db_project).filter(
            db_project.user_id==user_id,
            db_project.id==project_id
        ).first()
        user = UserRepository(self.db).get_user(user_id)
        return project is not None or user.is_admin
    
    def check_project_existing(self, project_id: int):
        project = self.get_project(project_id)
        if project is None:
            raise ProjectNotFound(project_id)
    
    def create_project(self, name, user_id) -> ProjectResponse:
        project = db_project(
        name = name,
        user_id = user_id
        )
        self.db.add(project)
        self.db.commit()
        return ProjectResponse(
            id=project.id,
            name=project.name,
            icon_id=project.icon_id,
            created_at=project.created_at,
            owner_id=project.user_id
        )
    
    def get_project(self, project_id: int, user_id: int = None) -> ProjectResponse:
        query = self.db.query(db_project).filter(db_project.id == project_id)
        if user_id is not None:
            query = query.filter(db_project.user_id == user_id)
        project = query.first()
        if project is None:
            raise ProjectNotFound(project_id)
        return ProjectResponse(
            id=project.id,
            name=project.name,
            icon_id=project.icon_id,
            created_at=project.created_at,
            owner_id=project.user_id
        )
    
    def get_my_projects(self, user_id: int) -> List[MyProjectResponse]:
        projects = (
        self.db.query(
            db_project,
            UserProjectAssociation.category_id
        )
        .outerjoin(  
            UserProjectAssociation,
            and_(
                UserProjectAssociation.project_id == db_project.id,
                UserProjectAssociation.user_id == user_id
            )
        )
        .filter(
            db_project.user_id == user_id  
        )
        .all()
        )
        return [MyProjectResponse(
            project_id=project.id,
            project_name=project.name,
            category_id=category_id,
            icon_id=project.icon_id,
            project_created_at=project.created_at
        ) for project, category_id in projects]
    
    def update_project(self, project_id: int, project_data: UpdateProjectRequest):
        project = self.db.query(db_project).filter(db_project.id == project_id).first()
        if project_data.name is not None:
            project.name = project_data.name
        if project_data.icon_id is not None:
            AttachmentRepository(self.db).check_attachment_exist(project_data.icon_id)
            project.icon_id = project_data.icon_id 
        self.db.commit()
        self.db.refresh(project)

    def delete_project(self, user_id: int, project_id: int, is_admin: bool = False) -> bool:
        if is_admin:
            project = self.db.query(db_project).filter(db_project.id == project_id).first()
        else:
            project = self.db.query(db_project).filter(
                db_project.id == project_id,
                db_project.user_id == user_id
            ).first()
        if project is None:
            raise ProjectNotFound(project_id)
        self.db.delete(project)
        self.db.commit()
        