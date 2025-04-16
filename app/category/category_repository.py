from typing import List
from sqlalchemy.orm import Session

from ..category.schemas import CategoryResponseSchema
from ..models_db import Category as db_category

class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_category(self, user_id: int, category_id: int) -> CategoryResponseSchema|None:
        category = self.db.query(db_category).filter(db_category.user_id==user_id, 
        db_category.id==category_id).first()
        if category is None:
            return None
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
    
    def create_category(db: Session, name: str, color: str, user_id) -> int:
        db_category = db_category(
            name=name,
            color=color,
            user_id=user_id
        )
        db.add(db_category)
        db.commit()
        db.refresh(db_category)
        return db_category.id