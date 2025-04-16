import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, logger, status, Response
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated

from ...user.service.attachment_service import AttachmentService
from ..user_repository import UserRepository
from ..attachment_repository import AttachmentRepository
from ...database import engine, Sessionlocal
from ...auth.auth import get_current_user
from ...project.project_repository import ProjectRepository

router = APIRouter(
    prefix="/files",
    tags=['FilesController']
)

def get_db():
    db = Sessionlocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

UPLOAD_DIRECTORY = r'C:\Users\Пользователь\Documents\Python\projects\MultiTasker\data\attachments'
DEFAULT_USER_ICON = 'user_icon.png'
DEFAULT_PROJECT_ICON = 'project.png'
ALLOWED_MIME_TYPES = ["image/jpeg", "image/png"]
MAX_FILE_SIZE = 50 * 1024 * 1024

@router.post('/')
async def post_attachment(uploaded_file: UploadFile, user: user_dependency, db: db_dependency):
    try:
        attachment_id = AttachmentService(db).post_attachment_service(user['id'], uploaded_file)
        return {"message": "Файл успено загружен",
             "attachment_id": attachment_id}
    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, 
            detail=str(e)
        )

@router.get('/icon', response_class=FileResponse)
async def get_icon(
    user: user_dependency,
    db: db_dependency,
    response: Response = None,
    user_id: int = Query(None, description="ID пользователя"),
    project_id: int = Query(None, description="ID проекта"),
):
    response.headers.update({
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    })
    if all([user_id, project_id]):
        raise HTTPException(
            status_code=400,
            detail="Должен быть указан ровно один параметр: user_id ИЛИ project_id"
        )
    try:
        if project_id is not None:
            file_path = AttachmentService(db).get_project_icon(project_id)
        else:
            if user_id is None:
                file_path = AttachmentService(db).get_user_icon(user_id)
            else: 
                file_path = AttachmentService(db).get_user_icon(user['id'])
    except HTTPException as e:
        raise e
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Icon file not found on server")
    return FileResponse(file_path)

@router.delete('/', status_code=status.HTTP_204_NO_CONTENT)
async def delete_icon(
    user: user_dependency, 
    db: db_dependency,
    project_id: int = Query(None, description="ID проекта")
):
    try:
        AttachmentService(db).delete_icon(user['id'], project_id)
    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, 
            detail=str(e)
        )
        
