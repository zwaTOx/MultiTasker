
import os
import re
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

load_dotenv()
LOGIN_MASK = os.getenv('LOGIN_MASK')
PASSWORD_MASK = os.getenv('PASSWORD_MASK')

def validate_login(value: str) -> str:
    if not re.match(LOGIN_MASK, value):
        raise ValueError('Invalid login format')
    return value

def validate_password(value: str) -> str:
    if not re.match(PASSWORD_MASK, value):
        raise ValueError('Invalid password format')
    return value


class CreateUser(BaseModel):
    login: str
    password: str
    @field_validator('login')
    def validate_login_field(cls, value):
        return validate_login(value)
    @field_validator('password')
    def validate_password_field(cls, value):
        return validate_password(value)

class ResetPasswordRequest(BaseModel):
    new_password: str
    confirm_password: str
    @field_validator('new_password')
    def validate_password_field(cls, value):
        return validate_password(value)

class Token(BaseModel):
    access_token: str
    token_type: str

class UserData(BaseModel):
    id: int
    login: str
    username: str

class ChangeEmailRequest(BaseModel):
    new_email: str
    @field_validator('new_email')
    def validate_login_field(cls, value):
        return validate_login(value)

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str
    @field_validator('new_password')
    def validate_password_field(cls, value):
        return validate_password(value)

class UpdateUserRequest(BaseModel):
    new_username: Optional[str] = Field(default = None)  
    new_email: Optional[str] = Field(default = None)  
    old_password: Optional[str] = Field(default = None)  
    new_password: Optional[str] = Field(default = None)  
    confirm_password: Optional[str] = Field(default = None) 
    attachment_id: Optional[int] = Field(default = None)  

class UserResponse(BaseModel):
    id: int
    login: str
    username: Optional[str] = Field(default = None)  
    icon_id: Optional[int] = Field(default = None)  
    is_verified: bool  = Field(default = True)  

class ProjectUserResponse(BaseModel):
    user_id: int
    username: Optional[str] = None
    login: str

class AttachmentResponse(BaseModel):
    id: int
    path: str
