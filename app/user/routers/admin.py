import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, logger, status, Response
from sqlalchemy.orm import Session
from typing import Annotated

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
    if not UserRepository(db).check_admin_perms(user['id']):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен"
        )

    target_user = UserRepository(db).get_user(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    target_user.is_admin = is_admin
    db.commit()
    db.refresh(target_user)
    return {
        "message": "Данные пользователя обновлены"
    }