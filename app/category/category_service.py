from sqlalchemy.orm import Session

from ..category.category_repository import CategoryRepository

class CategoryService:
    def __init__(self, db: Session):
        self.db = db

    def create_category(self, name: str, color: str, user_id: int) -> int:
        return CategoryRepository(self.db).create_category(name, color, user_id)
    
    def get_categories(self, user_id):
        categories = CategoryRepository(self.db).get_categories(user_id)
        return categories