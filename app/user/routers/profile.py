import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, logger, status, Response
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated

from ..service.profile_service import ProfileService
from ..schemas import ChangePasswordRequest, ChangeEmailRequest, UpdateUserRequest
from ...models_db import User
from ..user_repository import UserRepository
from ..attachment_repository import AttachmentRepository
from ...database import engine, Sessionlocal
from ...auth.auth import get_current_user, bcrypt_context
from ...project.project_repository import ProjectRepository

router = APIRouter(
    tags=['Profile']
)

def get_db():
    db = Sessionlocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@router.put('/me')
async def update_user(user_data: UpdateUserRequest, user: user_dependency, db: db_dependency):
    ProfileService(db).update_profile(user['id'], user_data)
    return {
        "message": "User updated successfully",
    }
        