from fastapi import HTTPException
from sqlalchemy.orm import Session

from ...user.schemas import UpdateUserRequest
from ...user.user_repository import UserRepository

class ProfileService:
    def __init__(self, db: Session):
        self.db = db
    
    def update_profile(self, user_id: int, user_data: UpdateUserRequest):
        founded_user = UserRepository(self.db).get_user(user_id)
        if not founded_user:
            raise HTTPException(status_code=404, detail="User not found")
        UserRepository(self.db).update_user(user_id, user_data)
        if all([user_data.old_password, user_data.new_password, user_data.confirm_password]):
            if user_data.new_password != user_data.confirm_password:
                raise HTTPException(status_code=400, detail="Новый пароль и подтверждение пароля не совпадают")
            if not UserRepository(self.db).update_user_password(user_id, user_data.old_password, user_data.new_password):
                raise HTTPException(status_code=400, detail="Новый пароль и подтверждение пароля не совпадают")
