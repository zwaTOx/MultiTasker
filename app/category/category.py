from pydantic import BaseModel
from fastapi import APIRouter, FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated, List

from ..category.category_service import CategoryService
from ..models_db import Category as db_Category
from ..database import engine, Sessionlocal
from ..auth.auth import get_current_user
from .models import CategoryResponseExample, CreateCategoryRequest, UpdateCategoryRequest

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

@router.post("/")
async def create_category(category: CreateCategoryRequest, user: user_dependency, db: db_dependency):
    category_id = CategoryService(db).create_category(category.name, category.color, user['id'])
    return {
        "message": "Category created successfully",
        "category_id": category_id
    }

@router.get('/',
    response_model=List[CategoryResponseExample])
async def get_categories(user: user_dependency, db: db_dependency):
    categories = CategoryService(db).get_categories(user['id'])
    return categories

@router.put("/{category_id}", 
    responses={
        200: {"description": "Category updated successfully"},
        401: {"description": "Unauthorized"},
        404: {"description": "Category not found"}
    })
async def update_category(category_id: int, update_data: UpdateCategoryRequest, user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Auth Failed")
    db_category = db.query(db_Category).filter(db_Category.id==category_id,
        db_Category.user_id==user['id']).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    if update_data.name is not None:
        db_category.name = update_data.name
    if update_data.color is not None:
        db_category.color = update_data.color
    db.commit()
    db.refresh(db_category)
    return {"id": db_category.id, "name": db_category.name, "color": db_category.color}

@router.delete('/{category_id}', status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Category deleted successfully"},
        401: {"description": "Unauthorized"},
        404: {"description": "Category not found"}
    })
async def delete_category(category_id: int, user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Auth Failed")
    db_category = db.query(db_Category).filter(db_Category.id==category_id,
        db_Category.user_id==user['id']).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(db_category)
    db.commit()
    