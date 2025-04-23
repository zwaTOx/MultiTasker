from typing import List

from fastapi import HTTPException
from ...exceptions import ProjectNotFound
from ...user.user_repository import UserRepository
from ...project.project_repository import ProjectRepository
from ...project.schemas import CreateProjectRequest, MoveProjectRequest, UpdateProjectRequest
from ...project.schemas import ProjectResponse, MyProjectResponse, ProjectWithMembershipResponse
from ...user.user_project_association_repo import UserProjectAssociation
from ...category.category_repository import CategoryRepository

class ProjectService:
    def __init__(self, db):
        self.db = db

    def get_projects(self, user_id: int, category_id: int) -> List[ProjectWithMembershipResponse]:
        if category_id:
            CategoryRepository(self.db).get_category(user_id, category_id)
            projects = UserProjectAssociation(self.db).get_accessed_projects_by_category(user_id, category_id)
        else:
            projects = UserProjectAssociation(self.db).get_accessed_projects(user_id)
        return projects
    
    def move_project_in_category_service(self, user_id: int, project_id: int,
        request: MoveProjectRequest):
        category = CategoryRepository(self.db).get_category(user_id, request.category_id)
        ProjectRepository(self.db).check_project_existing(project_id)
        UserProjectAssociation(self.db).change_project_category(user_id, project_id, category.id)
        
    def get_my_projects_service(self, user_id: int) -> List[MyProjectResponse]:
        projects = ProjectRepository(self.db).get_my_projects(user_id)
        return projects
    
    def create_project_service(self, user_id, project_data: CreateProjectRequest, 
        category_id: int = None) -> ProjectResponse:
        if category_id is not None:
            category = CategoryRepository(self.db).get_category(user_id, category_id)
        project = ProjectRepository(self.db).create_project(project_data.name, user_id)
        UserProjectAssociation(self.db).create_project(user_id, project.id, category.id)
        return project
    
    def update_project_service(self, user_id: int, project_id: int,
        project_data: UpdateProjectRequest):
        is_admin = UserRepository(self.db).check_admin_perms(user_id)
        if is_admin:
            project = ProjectRepository(self.db).get_project(project_id)
        else:
            project = ProjectRepository(self.db).get_project(project_id, user_id)
        ProjectRepository(self.db).update_project(project.id, project_data)

    def delete_project_service(self, user_id: int, project_id: int):
        is_admin = UserRepository(self.db).check_admin_perms(user_id)
        ProjectRepository(self.db).delete_project(user_id, project_id, is_admin)
        