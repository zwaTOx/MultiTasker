from typing import Optional
from pydantic import BaseModel, Field

class CategoryResponseSchema(BaseModel):
    id: int
    name: str
    color: str

class CreateCategoryRequest(BaseModel):
    name: str = Field(..., max_length=100)
    color: str

class UpdateCategoryRequest(BaseModel):
    name: Optional[str] = Field(default=None, max_length=100)  
    color: Optional[str] = Field(default=None)

class CategoryResponseExample(BaseModel):
    id: int
    name: str
    color: str