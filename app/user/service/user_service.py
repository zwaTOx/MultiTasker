from typing import List
from fastapi import HTTPException
from sqlalchemy.orm import Session

from ...project.project_repository import ProjectRepository
from ...user.user_project_association_repo import UserProjectAssociation
from ..schemas import UserResponse
from ..user_repository import UserRepository

class UserService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_users_service(self, user_id: int, project_id: int = None) -> List[UserResponse]:
        if project_id is not None:
            if not UserProjectAssociation(self.db).check_user_in_project(user_id, project_id):
                raise HTTPException(status_code=403, detail="Доступ запрещен")
            project = ProjectRepository(self.db).get_project(project_id) 
            if project is None:
                raise ValueError("Project not found")
            users = UserProjectAssociation(self.db).get_users_in_project(project_id)
        else:
            users = UserRepository(self.db).get_users()
        return users