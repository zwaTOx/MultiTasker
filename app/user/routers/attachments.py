import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, logger, status, Response
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Annotated

from ..user_repository import UserRepository
from ..attachment_repository import AttachmentRepository
from ...database import engine, Sessionlocal
from ...auth.auth import get_current_user, bcrypt_context
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
    founded_user = UserRepository(db).get_user(user['id'])
    if founded_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    file = uploaded_file.file
    filename = str(uuid.uuid4()) + os.path.splitext(uploaded_file.filename)[1]
    file_path = os.path.join(UPLOAD_DIRECTORY, filename)
    content_type = uploaded_file.content_type
    file_size = 0
    for chunk in uploaded_file.file:
        file_size += len(chunk)
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Файл слишком большой. Максимальный размер: {MAX_FILE_SIZE//(1024*1024)} МБ"
            )
    uploaded_file.file.seek(0)
    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Недопустимый формат файла. Разрешены только JPEG и PNG"
        )
    with open(file_path, 'wb') as f:
        f.write(file.read())
    attachment = AttachmentRepository(db).add_attachment(filename)
    return {"message": "Файл успено загружен",
            "attachment_id": attachment.id}

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
    if project_id is not None:
        project = ProjectRepository(db).get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        if project.icon_id is None:
            return get_default_project_icon()
        attachment = AttachmentRepository(db).get_attachment_by_id(project.icon_id)
        if not attachment:
            raise HTTPException(status_code=404, detail="Project attachment not found")
        file_path = os.path.join(UPLOAD_DIRECTORY, attachment.path)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Project icon file not found")
        return FileResponse(file_path)

    #user_id
    target_user_id = user_id if user_id is not None else user['id']
    founded_user = UserRepository(db).get_user(target_user_id)
    if not founded_user:
        raise HTTPException(status_code=404, detail="User not found")

    if founded_user.icon_id is None:
        base_dir = os.path.dirname(UPLOAD_DIRECTORY)
        default_icon_path = os.path.join(base_dir, "defaults", DEFAULT_USER_ICON)
        if not os.path.exists(default_icon_path):
            raise HTTPException(status_code=404, detail="Default icon not found")
        return FileResponse(default_icon_path)

    attachment = AttachmentRepository(db).get_attachment_by_id(founded_user.icon_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    file_path = os.path.join(UPLOAD_DIRECTORY, attachment.path)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Icon file not found on server")

    return FileResponse(file_path)

def get_default_user_icon():
    base_dir = os.path.dirname(UPLOAD_DIRECTORY)
    default_icon_path = os.path.join(base_dir, "defaults", DEFAULT_USER_ICON)
    if not os.path.exists(default_icon_path):
        raise HTTPException(status_code=404, detail="Default user icon not found")
    return FileResponse(default_icon_path)

def get_default_project_icon():
    base_dir = os.path.dirname(UPLOAD_DIRECTORY)
    default_icon_path = os.path.join(base_dir, "defaults", DEFAULT_PROJECT_ICON)
    if not os.path.exists(default_icon_path):
        raise HTTPException(status_code=404, detail="Default project icon not found")
    return FileResponse(default_icon_path)

@router.delete('/', status_code=status.HTTP_204_NO_CONTENT)
async def delete_icon(
    user: user_dependency, 
    db: db_dependency,
    project_id: int = Query(None, description="ID проекта")
):
    if project_id is not None:
        project = ProjectRepository(db).get_project(project_id)
        if project is None:
            raise HTTPException(status_code=404, detail="Project not found")
        if project.user_id != user['id']:
            raise HTTPException(status_code=403, detail="Access Denied")
        if project.icon_id is None:
            raise HTTPException(status_code=404, detail="Project icon not found")
        attachment = AttachmentRepository(db).get_attachment_by_id(project.icon_id)
        if attachment is None:
            raise HTTPException(status_code=404, detail="Attachment not found")
        if not AttachmentRepository(db).delete_attachment(attachment_id=project.icon_id):
            raise HTTPException(status_code=404, detail="Failed to delete attachment")
        return
    founded_user = UserRepository(db).get_user(user['id'])
    if not founded_user:
        raise HTTPException(status_code=404, detail="User not found")
    if founded_user.icon_id is None:
        raise HTTPException(status_code=404, detail="User icon not found")
    attachment = AttachmentRepository(db).get_attachment_by_id(founded_user.icon_id)
    if attachment is None:
        raise HTTPException(status_code=404, detail="Attachment not found")
    if not AttachmentRepository(db).delete_attachment(attachment.id):
        raise HTTPException(status_code=404, detail="Failed to delete attachment")
    return
        
