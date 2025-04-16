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

from ..user.service.user_service import UserService
from ..auth.code_service import CodeService
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
    try:
        user_id, message = UserService(db).create_user(create_user_rq)
        return {
            "message": message,
            "id": user_id
        }
    except HTTPException as e:
        raise e
    
@router.post('/login', response_model=Token)
async def login_for_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: db_dependency
):
    # user = auth_user(form_data.username, form_data.password, db)
    # if not user:
    #     raise HTTPException(status_code=401, detail='Could not validate user.')
    # if user.is_verified is False:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="User with this email is not verified"
    #     )
    # token = CodeService(db).create_access_token(user.login, user.id, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    # return {'access_token': token, 'token_type': 'bearer'}
    try:
        token = UserService(db).login_user(form_data.username, form_data.password)
        return {'access_token': token, 'token_type': 'bearer'}
    except HTTPException as e:
        raise e
    
@router.post('/сode/send')
async def create_password_restore_code(user_email: str, db: db_dependency):
    try:
        CodeService(db).create_password_restore_code(user_email)
        return {
        "message": f"Code sent on {user_email}"
        }
    except RuntimeError as e:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=str(e)
        )
    except HTTPException as e:
        raise e

@router.post('/code/verify/{code}', response_model=Token)
async def auth_with_code(code: str, db: db_dependency):
    try:
        token = CodeService(db).auth_with_code(code)
        return {
        'access_token': token, 
        'token_type': 'bearer'
        }
    except ValueError as e:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, 
            detail=str(e)
        )
    except HTTPException as e:
        raise e

@router.post('/password/reset')
async def reset_password(token: str, reset_data: ResetPasswordRequest, db: db_dependency):
    try:
        CodeService(db).reset_password(token, reset_data)
        return {"message": "Password successfully changed"}
    except ValueError as e:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, 
            detail=str(e)
        )
    except HTTPException as e:
        raise e

# def create_access_token(login: str, id: str, expires_delta: timedelta):
#     encode = {'login': login, 'id': id}
#     expires = datetime.utcnow() + expires_delta
#     encode.update({'exp': expires})
#     return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

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