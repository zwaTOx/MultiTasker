from ...project.schemas import ProjectWithMembershipResponse
from ...user.user_project_association_repo import UserProjectAssociation
from ...category.category_repository import CategoryRepository

class ProjectService:
    def __init__(self, db):
        self.db = db

    def get_projects_service(self, user_id: int, category_id: int):
        if category_id:
            category = CategoryRepository(self.db).get_category(user_id, category_id)
            if category is None:
               raise ValueError('Category not found')
            projects = UserProjectAssociation(self.db).get_accessed_projects_by_category(user_id, category_id)
        else:
            projects = UserProjectAssociation(self.db).get_accessed_projects(user_id)
        return projects