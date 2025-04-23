from typing import List
from sqlalchemy.orm import Session

from ..category.schemas import UpdateCategoryRequest
from ..category.schemas import CategoryResponseSchema
from ..models_db import Category as db_category
from ..exceptions import CategoryNotFound

class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def _get_category(self, category_id: int, user_id: int = None) -> db_category:
        if user_id is not None:
            category = self.db.query(db_category).filter(db_category.user_id==user_id, 
        db_category.id==category_id).first()
        else:
            category = self.db.query(db_category).filter(db_category.id==category_id).first()
        if not category:
            raise CategoryNotFound(category_id, user_id)
        return category

    def get_category(self, user_id: int, category_id: int) -> CategoryResponseSchema:
        category = self._get_category(category_id, user_id)
        if not db_category:
            raise CategoryNotFound(category_id, user_id)
        return CategoryResponseSchema(
            id = category_id,
            name = category.name,
            color = category.color
        )
    
    def get_categories(self, user_id: int) -> List[CategoryResponseSchema]:
        categories = self.db.query(db_category).filter(db_category.user_id==user_id).all()
        return [CategoryResponseSchema(
            id = category.id,
            name = category.name,
            color = category.color
        ) for category in categories]
    
    def create_category(self, name: str, color: str, user_id) -> int:
        category = db_category(
            name=name,
            color=color,
            user_id=user_id
        )
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category.id
    
    def update_category(self, category_id, user_id, data: UpdateCategoryRequest) -> CategoryResponseSchema|None:
        category = self._get_category(category_id, user_id)
        if data.name is not None:
            category.name = data.name
        if data.color is not None:
            category.color = data.color
        self.db.commit()
        self.db.refresh(category)
        
        return CategoryResponseSchema(
            id=category.id,
            name=category.name,
            color=category.color
    )

    def delete_category(self, user_id: int, category_id: int):
        category = self._get_category(category_id, user_id)
        self.db.delete(category)
        self.db.commit()
