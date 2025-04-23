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
from ..database import engine, Sessionlocal
from ..user.schemas import CreateUser, ResetPasswordRequest, Token

load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')

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

@router.post("/register", status_code=status.HTTP_201_CREATED) 
async def create_user(db: db_dependency, create_user_rq: CreateUser):
    user_id, message = UserService(db).create_user(create_user_rq)
    return {
        "message": message,
        "id": user_id
    }
    
@router.post('/login', response_model=Token, status_code=status.HTTP_201_CREATED)
async def login_for_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: db_dependency
):
    token = UserService(db).login_user(form_data.username, form_data.password)
    return {'access_token': token, 'token_type': 'bearer'}
    
@router.post('/сode/send', status_code=status.HTTP_201_CREATED)
async def create_password_restore_code(user_email: str, db: db_dependency):
    CodeService(db).create_password_restore_code(user_email)
    return {
    "message": f"Code sent on {user_email}"
    }

@router.post('/code/verify/{code}', response_model=Token, status_code=status.HTTP_201_CREATED)
async def auth_with_code(code: str, db: db_dependency):
    token = CodeService(db).auth_with_code(code)
    return {
    'access_token': token, 
    'token_type': 'bearer'
    }

@router.post('/password/reset', status_code=status.HTTP_201_CREATED)
async def reset_password(token: str, reset_data: ResetPasswordRequest, db: db_dependency):
    CodeService(db).reset_password(token, reset_data)
    return {"message": "Password successfully changed"}
    
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