
from typing import Optional
from pydantic import BaseModel, Field

class CreateCategoryRequest(BaseModel):
    name: str = Field(..., max_length=100)
    color: str

class UpdateCategoryRequest(BaseModel):
    name: Optional[str] = Field(..., max_length=100)  
    color: Optional[str]

class CategoryResponseExample(BaseModel):
    id: int
    name: str
    color: str