from typing import List

from ...project.project_repository import ProjectRepository
from ...project.models import MoveProjectRequest
from ...project.schemas import ProjectWithMembershipResponse
from ...user.user_project_association_repo import UserProjectAssociation
from ...category.category_repository import CategoryRepository

class ProjectService:
    def __init__(self, db):
        self.db = db

    def get_projects_service(self, user_id: int, category_id: int) -> List[ProjectWithMembershipResponse]:
        if category_id:
            category = CategoryRepository(self.db).get_category(user_id, category_id)
            if category is None:
               raise ValueError('Category not found')
            projects = UserProjectAssociation(self.db).get_accessed_projects_by_category(user_id, category_id)
        else:
            projects = UserProjectAssociation(self.db).get_accessed_projects(user_id)
        return projects
    
    def move_project_in_category_service(self, user_id: int, project_id: int,
        request: MoveProjectRequest):
        category = CategoryRepository(self.db).get_category(user_id, request.category_id)
        if category is None:
            raise ValueError('Category not found')
        if not ProjectRepository(self.db).check_project_existing(project_id):
            raise ValueError('Project not found')
        if not UserProjectAssociation(self.db).check_user_in_project(user_id, project_id):
            raise PermissionError('You are not a member of this project')
        if not UserProjectAssociation(self.db).change_project_category(user_id, project_id, request.category_id):
            raise RuntimeError('Failed to change category')