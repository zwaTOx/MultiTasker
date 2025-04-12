
from typing import Optional
from pydantic import BaseModel, Field


class CreateProjectRequest(BaseModel):
    name: str = Field(max_length=100) 

class UpdateProjectRequest(BaseModel):
    name: Optional[str] = Field(default=None) 
    icon_id: Optional[int] = Field(default=None) 

class MoveProjectRequest(BaseModel):
    category_id: Optional[int] = None