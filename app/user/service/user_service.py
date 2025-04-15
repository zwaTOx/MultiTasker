from typing import List
from fastapi import HTTPException, status
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
        return users or []
    
    def leave_project(self, user_id: int, project_id: int):
        if not UserProjectAssociation(self.db).check_user_in_project(user_id, project_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь не является участником проекта"
            )
        if not ProjectRepository(self.db).check_project_existing(project_id):
            raise ValueError('Project not found')
        UserProjectAssociation(self.db).leave_project(user_id, project_id)

    def kick_user_from_project(self, req_id: int, user_id, project_id: int):
        if not ProjectRepository(self.db).check_project_owner(req_id, project_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Вы не являетесь владельцем проекта"
            )
        if not ProjectRepository(self.db).check_project_existing(project_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Проект не найден"
            )
        if user_id == req_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Кикнуть себя из проекта нельзя"
            )
        UserProjectAssociation(self.db).leave_project(user_id, project_id)