from datetime import datetime
import os
import re
from typing import List, Literal, Optional
from dotenv import load_dotenv
from fastapi import Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Enum
from ..models_db import User

load_dotenv()
EMAIL_MASK = os.getenv('LOGIN_MASK')

IndicatorType = Literal['red', 'orange', 'yellow', 'green']
StatusType = Literal['Назначена', 'В работе', 'Выполнена']
SortByType = Literal['created_at', 'last_change', 'deadline']
SortOrderType = Literal['asc', 'desc']

def validate_login(value: str) -> str:
    if not re.match(EMAIL_MASK, value):
        raise ValueError('Invalid login format')
    return value

class TaskCreateRequest(BaseModel):
    name: str = Field(max_length=100) 
    description: Optional[str] = Field(default=None, max_length=10000) 
    deadline: datetime
    indicator: Optional[IndicatorType] = Field(default=None)
    performer_id: Optional[int] = Field(default=None) 
    parent_task_id: Optional[int] = Field(default=None) 

class TaskUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None, max_length=10000) 
    deadline: Optional[datetime] = Field(default=None)
    performer_email: Optional[str] = Field(default=None)
    indicator: Optional[IndicatorType] = Field(default=None)
    status: Optional[StatusType] = Field(default=None)

    @field_validator('performer_email')
    def validate_login_field(cls, value):
        return validate_login(value)
    
class TaskResponseSchema(BaseModel):
    name: str
    indicator: str
    description: Optional[str]
    author_email: str
    author_name: Optional[str] 

class TaskDetailResponse(BaseModel):
    id: int
    name: str
    status: str
    indicator: Optional[str] = Field(None)
    created_at: datetime
    last_change: datetime
    deadline: Optional[datetime] = Field(None)
    description: Optional[str] = Field(None)
    author_id: int
    author_name: Optional[str] = Field(None) 
    author_email: Optional[str] = Field(None)
    performer_id: Optional[int] = Field(None)
    performer_name: Optional[str] = Field(None)
    performer_email: Optional[str] = Field(None)
    project_id: int
    project_name: str
    parent_task_id: Optional[int] = Field(None)

# class StatusType(str, Enum):
#     ASSIGNED = "Назначенные"
#     IN_PROGRESS = "В работе"
#     COMPLETED = "Выполненные"
#     CANCELLED = "Отмененные"

# class IndicatorType(str, Enum):
#     LOW = "Низкий"
#     MEDIUM = "Средний"
#     HIGH = "Высокий"

# class TaskFilters(BaseModel):
#     name: Optional[str] = None
#     project_id: Optional[int] = None
#     parent_task_id: Optional[int] = None
#     status: Optional[List[StatusType]] = Query(None)
#     indicator: Optional[List[IndicatorType]] = Query(None)
#     on_me: Optional[bool] = False,
#     sort_by: Optional[str] = None 

class TaskFilters:
    def __init__(
        self,
        name: Optional[str] = None,
        project_id: Optional[int] = None,
        parent_task_id: Optional[int] = None,
        owner_id: Optional[int] = None,
        status: Optional[List[StatusType]] = Query(None),
        indicator: Optional[list[IndicatorType]] = Query(None),
        on_me: Optional[bool] = False,
        sort_by: Optional[SortByType] = None,
        sort_order: Optional[SortOrderType] = "asc"
    ):
        self.name = name
        self.project_id = project_id
        self.parent_task_id = parent_task_id
        self.owner_id = owner_id
        self.status = status
        self.indicator = indicator
        self.on_me = on_me
        self.sort_by = sort_by
        self.sort_order = sort_order

class TaskItemResponse(BaseModel):
    id: int
    name: str
    status: StatusType
    indicator: Optional[IndicatorType] = None
    created_at: Optional[datetime] = None 
    last_change: Optional[datetime] = None  
    deadline: Optional[datetime] = None 
    description: Optional[str] = None
    project_id: int


    