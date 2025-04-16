
from datetime import timedelta, datetime, timezone
import os
from jose import JWTError, jwt
from dotenv import load_dotenv
from fastapi import HTTPException, status

from ..user.schemas import ResetPasswordRequest
from ..user.user_repository import UserRepository
from ..email_controller import send_recovery_code
from ..auth.code_repository import CodeRepository

load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES'))
TEMP_TOKEN_EXPIRE_MINUTES = int(os.getenv('TEMP_TOKEN_EXPIRE_MINUTES'))

class CodeService:
    def __init__(self, db):
        self.db = db
    
    @staticmethod
    def create_invite_project_token(project_id: int, id: int, expires_delta: timedelta):
        encode = {'project_id': project_id, 'id': id}
        expires = datetime.utcnow() + expires_delta
        encode.update({'exp': expires})
        return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)
    

    @staticmethod
    def decode_and_verify_invite_token(token: str):
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            current_time = datetime.now(timezone.utc)
            exp_timestamp = payload.get("exp")
            if exp_timestamp:
                exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
                if current_time > exp_datetime:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Токен истек"
                    )
            return payload
        except JWTError as e:
            if isinstance(e, jwt.ExpiredSignatureError):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Токен истек"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Недопустимый токен"
                )

    @staticmethod
    def create_access_token(login: str, id: str, expires_delta: timedelta):
        encode = {'login': login, 'id': id}
        expires = datetime.utcnow() + expires_delta
        encode.update({'exp': expires})
        return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

    def create_password_restore_code(self, user_email: str):
        code = CodeRepository.generate_code()
        result = send_recovery_code(
            email=user_email,
            code=code
        )
        if not result:
            raise HTTPException(
                status_code=500, detail=f"An unexpected error occurred.")
        CodeRepository(self.db).commit_code(user_email, code)

    def auth_with_code(self, code: str) -> str:
        is_valid, user_id = CodeRepository(self.db).verify_code(code)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired code"
            )
        user = UserRepository(self.db).get_user(user_id)
        if not user:
            ValueError("User not found")
        token = self.create_access_token(
            user.login, 
            user.id, 
            timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        CodeRepository(self.db).delete_user_codes(user_id)
        return token
    
    def reset_password(self, token: str, reset_data: ResetPasswordRequest):
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if not payload or "login" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format"
            )
        user = UserRepository(self.db).get_user_by_email(payload['login'])
        if not user:
            raise ValueError("User not found")
        if reset_data.new_password != reset_data.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords don't match"
            )
        UserRepository(self.db).reset_user_password(user.id, reset_data.new_password)