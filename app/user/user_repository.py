from typing import List
from fastapi import HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from ..user.schemas import UpdateUserRequest, UserResponse
from ..models_db import User as db_User
from ..exceptions import UserNotFound

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def _get_user_by_id(self, user_id: int) -> db_User:
        user = self.db.query(db_User).filter(db_User.id==user_id).first()
        if user is None:
            raise UserNotFound(user_id)
        return user
    
    def _get_user_by_email(self, email: str) -> db_User:
        user = self.db.query(db_User).filter(db_User.login==email).first()
        if user is None:
            raise UserNotFound()
        return user

    def create_user(self, login: str, password: str) -> UserResponse:
        user = db_User(
            login = login,
            hashed_password = bcrypt_context.hash(password)
        )
        self.db.add(user)
        self.db.commit()
        return UserResponse(
            id = user.id,
            login=user.login,
            username=user.username,
            icon_id=user.icon_id,
            is_verified=user.is_verified
        )

    def auth_user(self, login: str, password: str) -> UserResponse:
        user = self._get_user_by_email(login)
        if not bcrypt_context.verify(password, user.hashed_password):  
            raise HTTPException(status_code=401, detail='Could not validate user.')
        return UserResponse(
            id = user.id,
            login=user.login,
            username=user.username,
            icon_id=user.icon_id,
            is_verified=user.is_verified
        )

    def get_user(self, user_id: int) -> UserResponse:
        user = self._get_user_by_id(user_id)
        return UserResponse(
            id = user.id,
            login=user.login,
            username=user.username,
            icon_id=user.icon_id,
            is_verified=user.is_verified,
            is_admin=user.is_admin
        )
    
    def get_users(self) -> List[UserResponse]:
        users = self.db.query(db_User).all()
        return [UserResponse(
            id=user.id,
            login=user.login,
            username=user.username,
            icon_id=user.icon_id,
            is_verified=user.is_verified
        ) for user in users]
    
    def get_user_by_email(self, email: str) -> UserResponse:
        user = self._get_user_by_email(email)
        if user is None:
            raise UserNotFound
        return UserResponse(
            id=user.id,
            login=user.login,
            username=user.username,
            icon_id=user.icon_id,
            is_verified=user.is_verified)
    
    def create_unverified_user(self, user_email: str):
        existing_user = self.db.query(db_User).filter(db_User.login == user_email).first()
        if existing_user:
            return existing_user
        new_user_model = db_User(
            login = user_email,
            is_verified = False
        )
        self.db.add(new_user_model)
        self.db.commit()
        return new_user_model
    
    def check_admin_perms(self, user_id):
        user = self._get_user_by_id(user_id)
        return user.is_admin
    
    def update_user(self, user_id: int, user_data: UpdateUserRequest):
        user = self._get_user_by_id(user_id)
        if user_data.new_username is not None:
            user.username = user_data.new_username
        if user_data.new_email is not None:
            user.login = user_data.new_email
        if user_data.attachment_id is not None:
            user.icon_id = user_data.attachment_id
        self.db.commit()
        self.db.refresh(user)

    def update_user_password(self, user_id: int, password: str, new_password: str) -> bool:
        user = self._get_user_by_id(user_id)
        if not bcrypt_context.verify(password, user.hashed_password):
            return False
        user.hashed_password = bcrypt_context.hash(new_password)
        self.db.commit()
        self.db.refresh(user)
        return True

    def reset_user_password(self, user_id: int, new_password: str):
        user = self._get_user_by_id(user_id)
        user.hashed_password = bcrypt_context.hash(new_password)
        self.db.commit()
        self.db.refresh(user)

    def verify_user(self, email: str):
        user = self._get_user_by_email(email)
        user.is_verified = True
        self.db.commit()
        self.db.refresh(user)

    def update_admin(self, user_id: int, is_admin: bool):
        user = self._get_user_by_id(user_id)
        user.is_admin = is_admin
        self.db.commit()
        self.db.refresh(user)
