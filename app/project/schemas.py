from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class ProjectWithMembershipResponse(BaseModel):
    project_id: int
    project_name: str
    category_id: Optional[int] = None
    owner_id: int
    project_created_at: datetime
    user_joined_at: Optional[datetime]

class MyProjectResponse(BaseModel):
    project_id: int
    project_name: str
    category_id: Optional[int] = None
    icon_id: Optional[int]
    project_created_at: datetime

class ProjectResponse(BaseModel):
    id: int
    name: str
    icon_id: Optional[int]
    created_at: datetime

class CreateProjectRequest(BaseModel):
    name: str = Field(max_length=100) 

class UpdateProjectRequest(BaseModel):
    name: Optional[str] = Field(default=None) 
    icon_id: Optional[int] = Field(default=None) 

class MoveProjectRequest(BaseModel):
    category_id: Optional[int] = None