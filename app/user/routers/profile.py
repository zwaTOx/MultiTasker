import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, logger, status, Response
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated

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

# @router.get('/me/{user_id}')
# async def get_user_info(user_id: int, user: user_dependency, db: db_dependency):
#     pass

@router.put('/me')
async def update_user(user_data: UpdateUserRequest, user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Auth Failed")
    founded_user = UserRepository(db).get_user(user['id'])
    if not founded_user:
        raise HTTPException(status_code=404, detail="User not found")
    updated_fields = []
    if user_data.attachment_id is not None:
        founded_user.icon_id = user_data.attachment_id
        updated_fields.append("icon_id")
    if user_data.new_username is not None:
        founded_user.username = user_data.new_username
        updated_fields.append("username")
    if user_data.new_email is not None:
        founded_user.login = user_data.new_email
        updated_fields.append("email")
    if all([user_data.old_password, user_data.new_password, user_data.confirm_password]):
        if not bcrypt_context.verify(user_data.old_password, founded_user.hashed_password):
            raise HTTPException(status_code=400, detail="Старый пароль неверен")
        if user_data.new_password != user_data.confirm_password:
            raise HTTPException(status_code=400, detail="Новый пароль и подтверждение пароля не совпадают")
        founded_user.hashed_password = bcrypt_context.hash(user_data.new_password)
        updated_fields.append("password")
    if not updated_fields:
        raise HTTPException(
            status_code=400,
            detail="Не указаны данные для обновления"
        )
    db.commit()
    db.refresh(founded_user)
    return {
        "message": "Данные пользователя обновлены",
        "updated_fields": updated_fields
    }
        

# @router.post('/username/{new_username}', response_model=dict)
# async def set_name(new_username: str, user: user_dependency, db: db_dependency):
#     if user is None:
#         raise HTTPException(status_code=401, detail="Auth Failed")
#     db_user = db.query(User).filter(User.id == user['id']).first()
#     if not db_user:
#         raise HTTPException(status_code=404, detail="User not found")
#     db_user.username = new_username
#     db.commit()
#     db.refresh(db_user)

#     return {"message": "Username updated successfully", "username": db_user.username}

# @router.put('/email/{new_email}')
# async def change_email(email_data: ChangeEmailRequest, user: user_dependency, db: db_dependency):
#     if user is None:
#         raise HTTPException(status_code=401, detail='Auth Failed')
#     db_user = db.query(User).filter(User.id == user['id']).first()
#     if not db_user:
#         raise HTTPException(status_code=404, detail="User not found")
#     db_user.login = email_data.new_email
#     db.commit()
#     db.refresh(db_user)
#     return {"message": "email updated successfully", "login": db_user.login}



# @router.put('/password')
# async def change_password(change_ps_request: ChangePasswordRequest, user: user_dependency, db: db_dependency):
#     if user is None:
#         raise HTTPException(status_code=401, detail="Auth Failed")
    
#     db_user = db.query(User).filter(User.id == user['id']).first()
#     if not db_user:
#         raise HTTPException(status_code=404, detail="User not found")
#     if not bcrypt_context.verify(change_ps_request.old_password, db_user.hashed_password):
#         raise HTTPException(status_code=400, detail="Старый пароль неверен")
#     if change_ps_request.new_password != change_ps_request.confirm_password:
#         raise HTTPException(status_code=400, detail="Новый пароль и подтверждение пароля не совпадают")
    
#     db_user.hashed_password = bcrypt_context.hash(change_ps_request.new_password)
#     db.commit()
#     db.refresh(db_user)
#     return {"message": "Password updated successfully"}

#аватар

    