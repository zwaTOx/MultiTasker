from datetime import datetime, timedelta
from random import randint
from sqlalchemy.orm import Session

from app.exceptions import UserNotFound
from .models import PasswordResetCode as db_ResetCode
from ..models_db import User

class CodeRepository:
    def __init__(self, db: Session):
        self.db = db

    def commit_code(self, user_email: str, code: str):
        user = self.db.query(User).filter(User.login == user_email).first()
        self.delete_expired_codes()
        if not user:
            raise UserNotFound()
        self.delete_user_codes(user.id)
        data = db_ResetCode(
            user_id=user.id,  
            code=code
        )
        self.db.add(data)
        self.db.commit()
    
    def delete_user_codes(self, user_id):
        self.db.query(db_ResetCode).filter(
            db_ResetCode.user_id == user_id
        ).delete()
        self.db.commit()

    def verify_code(self, code: str) -> tuple[bool, int | None]:
        reset_code = self.db.query(db_ResetCode).filter(
            db_ResetCode.code == code
        ).first()

        if not reset_code:
            return (False, None)
        
        current_time = datetime.utcnow()
        code_expiration_time = reset_code.created_at + timedelta(minutes=10)
        
        if current_time > code_expiration_time:
            self.db.delete(reset_code)
            self.db.commit()
            return (False, None)
        return (True, reset_code.user_id)

    def delete_expired_codes(self, expiration_minutes: int = 10):
        expiration_time = datetime.utcnow() - timedelta(minutes=expiration_minutes)
        self.db.query(db_ResetCode).filter(
            db_ResetCode.created_at < expiration_time
        ).delete()
        self.db.commit()

    @staticmethod
    def generate_code() -> str:
        code = str(randint(0, 999999)).zfill(6)
        return code
