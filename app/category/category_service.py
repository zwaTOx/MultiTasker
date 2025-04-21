from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..category.schemas import UpdateCategoryRequest
from ..category.category_repository import CategoryRepository
from ..exceptions import CategoryNotFound

class CategoryService:
    def __init__(self, db: Session):
        self.db = db

    def create_category(self, name: str, color: str, user_id: int) -> int:
        return CategoryRepository(self.db).create_category(name, color, user_id)
    
    def get_categories(self, user_id):
        categories = CategoryRepository(self.db).get_categories(user_id)
        return categories
    
    def update_category(self, user_id, category_id, update_data: UpdateCategoryRequest):
        category = CategoryRepository(self.db).get_category(user_id, category_id)
        if not category:
            raise CategoryNotFound(category_id, user_id)
        updated_category = CategoryRepository(self.db).update_category(category.id, user_id, update_data)
        return updated_category
    
    def delete_category(self, user_id, category_id):
        db_category = CategoryRepository(self.db).get_category(user_id, category_id)
        if not db_category:
            raise CategoryNotFound(category_id, user_id)
        CategoryRepository(self.db).delete_category(user_id, category_id)