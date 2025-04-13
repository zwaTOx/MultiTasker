from datetime import datetime
from typing import Optional
from pydantic import BaseModel

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