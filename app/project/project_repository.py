from operator import and_
from sqlalchemy.orm import Session

from ..project.schemas import CreateProjectResponse, MyProjectResponse
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
    
    def check_project_existing(self, project_id: int) -> bool:
        project = self.get_project(project_id)
        return project is not None
    
    def create_project(self, name, user_id):
        project = db_project(
        name = name,
        user_id = user_id
        )
        self.db.add(project)
        self.db.commit()
        return CreateProjectResponse(
            project_id=project.id,
            project_name=project.name,
            icon_id=project.icon_id,
            project_created_at=project.created_at
        )
    
    def get_project(self, project_id: int):
        project = self.db.query(db_project).filter(
            db_project.id==project_id
        ).first()
        return project
    
    def get_my_projects(self, user_id: int):
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
        print(projects)
        return [MyProjectResponse(
            project_id=project.id,
            project_name=project.name,
            category_id=category_id,
            icon_id=project.icon_id,
            project_created_at=project.created_at
        ) for project, category_id in projects]