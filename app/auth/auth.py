from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

from .code_repository import CodeRepository
from ..email_controller import send_recovery_code
from ..database import engine, Sessionlocal
from ..user.schemas import CreateUser, ResetPasswordRequest, Token
from ..user.user_repository import UserRepository
from ..models_db import User

load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES'))
TEMP_TOKEN_EXPIRE_MINUTES = int(os.getenv('TEMP_TOKEN_EXPIRE_MINUTES'))

router = APIRouter(
    tags=['Auth']
)

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='login')

def get_db():
    db = Sessionlocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@router.post("/register") 
async def create_user(db: db_dependency, create_user_rq: CreateUser):
    existing_user = UserRepository(db).get_user_by_email(create_user_rq.login)
    if existing_user and existing_user.is_verified is True:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    if existing_user and existing_user.is_verified is False:
        existing_user.hashed_password = bcrypt_context.hash(create_user_rq.password)
        existing_user.is_verified = True
        db.commit()
        db.refresh(existing_user)
        return {
            "message": "Password updated successfully",
            "email": existing_user.login
        }
    new_user_model = User(
        login = create_user_rq.login,
        hashed_password = bcrypt_context.hash(create_user_rq.password)
    )
    db.add(new_user_model)
    db.commit()
    return {
        "message": "User created successfully",
        "id": new_user_model.login
    }

@router.post('/login', response_model=Token)
async def login_for_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: db_dependency
):
    user = auth_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=401, detail='Could not validate user.')
    if user.is_verified is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email is not verified"
        )
    token = create_access_token(user.login, user.id, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {'access_token': token, 'token_type': 'bearer'}

@router.post('/сode/send')
async def create_password_restore_code(request: Request, user_email: str, db: db_dependency):
    code = CodeRepository.generate_code()
    result = send_recovery_code(
        email=user_email,
        code=code
    )
    if not result:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred.")
    CodeRepository(db).commit_code(user_email, code)
    return {
        "message": f"Code sended on {user_email}"
        }

@router.post('/code/verify/{code}', response_model=Token)
async def auth_with_code(code: str, db: db_dependency):
    is_valid, user_id = CodeRepository(db).verify_code(code)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный или просроченный код"
        )
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    token = create_access_token(
        user.login, 
        user.id, 
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    CodeRepository(db).delete_user_codes(user_id)
    return {
        'access_token': token, 
        'token_type': 'bearer'
    }

@router.post('/password/reset')
async def reset_password(token: str, reset_data: ResetPasswordRequest, db: db_dependency):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    if not payload or "login" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный формат токена"
        )
    user = db.query(User).filter(User.login == payload["login"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    if reset_data.new_password != reset_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пароли не совпадают"
        )
    user.hashed_password = bcrypt_context.hash(reset_data.new_password)
    db.commit()
    return {"message": "Password successfully changed"}

def create_access_token(login: str, id: str, expires_delta: timedelta):
    encode = {'login': login, 'id': id}
    expires = datetime.utcnow() + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

def create_invite_project_token(project_id: int, id: int, expires_delta: timedelta):
    encode = {'project_id': project_id, 'id': id}
    expires = datetime.utcnow() + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

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

def auth_user(login: str, password: str, db: db_dependency) -> User | bool:
    user = db.query(User).filter(User.login == login).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):  
        return False
    return user

async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        login: str = payload.get('login')
        user_id: int = payload.get('id')
        if login is None or user_id is None:
            raise HTTPException(status_code=401, detail='Could not validate user.')
        return {'login': login, 'id': user_id}
    except JWTError:
        raise HTTPException(status_code=401, detail='Could not validate user.')


# if __name__ == '__main__':
    # assert validate_login('example@test.ru') == True #testest
    # assert validate_login('redfx') == False