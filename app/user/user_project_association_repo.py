from typing import Any, Dict, List, Optional
from sqlalchemy import literal
from sqlalchemy.orm import Session

from ..user.schemas import UserResponse
from ..project.schemas import ProjectWithMembershipResponse
from ..task.schemas import TaskFilters
from ..models_db import UserProjectAssociation as db_UPA
from ..models_db import Project as db_project
from ..models_db import User as db_user
from ..task.models import Task
from ..user.user_repository import UserRepository

class UserProjectAssociation:
    def __init__(self, db: Session):
        self.db = db

    def check_user_in_project(self, user_id: int, project_id: int) -> bool:
        inviting_user_assoc = self.db.query(db_UPA).filter(
            db_UPA.user_id == user_id,
            db_UPA.project_id == project_id
        ).first()   
        return inviting_user_assoc is not None or UserRepository(self.db).check_admin_perms(user_id)

    def add_user_in_project(self, user_id: int, project_id: int):
        new_association = db_UPA(
            user_id=user_id, 
            project_id=project_id)
        self.db.add(new_association)
        self.db.commit()
    
    def create_project(self, user_id: int, project_id: int, category_id: int):
        new_association = db_UPA(
            user_id=user_id, 
            project_id=project_id,
            category_id=category_id)
        self.db.add(new_association)
        self.db.commit()

    def leave_project(self, user_id, project_id):
        project_user_assoc = self.db.query(db_UPA).filter(
            db_UPA.user_id == user_id,
            db_UPA.project_id == project_id
        ).first() 
        self.db.delete(project_user_assoc)
        self.db.commit()
    
    def get_users_in_project(self, project_id) -> List[UserResponse]:
        users = self.db.query(
            db_UPA.user_id,
            db_user.username,
            db_user.login,
            db_user.icon_id,
            db_user.is_verified
        ).join(
            db_user, db_UPA.user_id == db_user.id
        ).filter(
            db_UPA.project_id==project_id
        ).all()
        return [UserResponse(
            id=user.user_id,
            login=user.login,
            username=user.username,
            icon_id=user.icon_id,
            is_verified=user.is_verified
        ) for user in users]

    def get_accessed_projects(self, user_id: int) -> List[Dict[str, Any]]:
        if not UserRepository(self.db).check_admin_perms(user_id):
            projects = self.db.query(
                db_project.id,
                db_project.name,
                db_UPA.category_id,
                db_project.user_id,
                db_project.created_at,
                db_UPA.joined_at
            ).join(
                db_project,
                db_UPA.project_id == db_project.id
            ).filter(
                db_UPA.user_id == user_id
            ).all()
        else:
            projects = self.db.query(
                db_project.id,
                db_project.name,
                literal(None).label('category_id'), 
                db_project.user_id,
                db_project.created_at,
                literal(None).label('joined_at')   
            ).all()
        print(projects)
        return [ProjectWithMembershipResponse(
            project_id=project.id,
            project_name=project.name,
            category_id=project.category_id,
            owner_id=project.user_id,
            project_created_at=project.created_at,
            user_joined_at=project.joined_at
        ) for project in projects]
        # for project in projects:
        #     result.append({
        #         "project_id": project.id,
        #         "project_name": project.name,
        #         "category_id": project.category_id,
        #         "owner_id": project.user_id,
        #         "project_created_at": project.created_at,
        #         "user_joined_at": project.joined_at
        #     })
        # return result

    def get_accessed_projects_by_category(self, user_id: int, category_id: int):
        projects = self.db.query(
            db_project.id,
            db_project.name,
            db_UPA.category_id,
            db_project.user_id,
            db_project.created_at,
            db_UPA.joined_at
        ).join(
            db_project,
            db_UPA.project_id == db_project.id
        ).filter(
            db_UPA.user_id == user_id,
            db_UPA.category_id==category_id
        ).all()
        result = []
        for project in projects:
            result.append({
                "project_id": project.id,
                "project_name": project.name,
                "category_id": project.category_id,
                "owner_id": project.user_id,
                "project_created_at": project.created_at.isoformat() if project.created_at else None,
                "user_joined_at": project.joined_at.isoformat() if project.joined_at else None
            })
        return result
        

    def change_project_category(self, user_id: int, project_id: int, category_id: int|None) -> bool:
        association = (
        self.db.query(db_UPA)
        .filter(
            db_UPA.user_id == user_id,
            db_UPA.project_id == project_id
        )
        .first()
        )

        if association:
            association.category_id = category_id
            self.db.commit()
            return True
        return False