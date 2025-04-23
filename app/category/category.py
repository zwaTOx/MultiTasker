from pydantic import BaseModel
from fastapi import APIRouter, FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated, List

from ..category.category_service import CategoryService
from ..models_db import Category as db_Category
from ..database import engine, Sessionlocal
from ..auth.auth import get_current_user
from .schemas import CategoryResponseExample, CreateCategoryRequest, UpdateCategoryRequest

router = APIRouter(
    prefix="/my/categories",
    tags=['Category']
)

def get_db():
    db = Sessionlocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_category(category: CreateCategoryRequest, user: user_dependency, db: db_dependency):
    category_id = CategoryService(db).create_category(category.name, category.color, user['id'])
    return {
        "message": "Category created successfully",
        "category_id": category_id
    }

@router.get('/', response_model=List[CategoryResponseExample])
async def get_categories(user: user_dependency, db: db_dependency):
    categories = CategoryService(db).get_categories(user['id'])
    return categories

@router.put("/{category_id}")
async def update_category(category_id: int, update_data: UpdateCategoryRequest, 
    user: user_dependency, db: db_dependency):
    updated_category = CategoryService(db).update_category(user['id'], category_id, update_data)
    return updated_category

@router.delete('/{category_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: int, user: user_dependency, db: db_dependency):
    CategoryService(db).delete_category(user['id'], category_id)
    