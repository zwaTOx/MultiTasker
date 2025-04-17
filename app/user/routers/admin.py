import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, logger, status, Response
from sqlalchemy.orm import Session
from typing import Annotated

from ...user.service.user_service import UserService
from ..user_repository import UserRepository
from ...database import Sessionlocal
from ...auth.auth import get_current_user

router = APIRouter(
    prefix="/admin",
    tags=['Admin']
)

def get_db():
    db = Sessionlocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@router.put('/admin/{user_id}')
async def change_admin(user_id: int, is_admin: bool, user: user_dependency, db: db_dependency):
    try: 
        UserService(db).update_admin(user['id'], user_id, is_admin)
        return {
        "message": "Данные пользователя обновлены"
        }
    except HTTPException as e:
        raise e
    