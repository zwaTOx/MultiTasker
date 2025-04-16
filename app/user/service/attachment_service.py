
from fastapi import HTTPException, UploadFile
from fastapi.responses import FileResponse

from ...project.project_repository import ProjectRepository
from ...user.attachment_repository import AttachmentRepository
from ...user.user_repository import UserRepository
import os
import uuid

UPLOAD_DIRECTORY = r'C:\Users\Пользователь\Documents\Python\projects\MultiTasker\data\attachments'
DEFAULT_USER_ICON = 'user_icon.png'
DEFAULT_PROJECT_ICON = 'project.png'
ALLOWED_MIME_TYPES = ["image/jpeg", "image/png"]
MAX_FILE_SIZE = 50 * 1024 * 1024

class AttachmentService:
    def __init__(self, db):
        self.db = db
    def post_attachment_service(self, user_id: int, uploaded_file: UploadFile) -> int:
        founded_user = UserRepository(self.db).get_user(user_id)
        if founded_user is None:
            raise ValueError('User not found')
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
        attachment = AttachmentRepository(self.db).add_attachment(filename)
        print(type(attachment.id))
        return attachment.id

    def get_user_icon(self, user_id):
        founded_user = UserRepository(self.db).get_user(user_id)
        if founded_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        if founded_user.icon_id is None:
            return self.get_default_user_icon()
        attachment = AttachmentRepository(self.db).get_attachment_by_id(founded_user.icon_id)
        if not attachment:
            raise HTTPException(status_code=404, detail="Attachment not found")
        return os.path.join(UPLOAD_DIRECTORY, attachment.path)

    def get_project_icon(self, project_id):
        project = ProjectRepository(self.db).get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        if project.icon_id is None:
            return self.get_default_project_icon()
        attachment = AttachmentRepository(self.db).get_attachment_by_id(project.icon_id)
        if not attachment:
            raise HTTPException(status_code=404, detail="Project attachment not found")
        return os.path.join(UPLOAD_DIRECTORY, attachment.path)
    
    def get_default_user_icon(self):
        base_dir = os.path.dirname(UPLOAD_DIRECTORY)
        default_icon_path = os.path.join(base_dir, "defaults", DEFAULT_USER_ICON)
        if not os.path.exists(default_icon_path):
            raise HTTPException(status_code=404, detail="Default user icon not found")
        return default_icon_path

    def get_default_project_icon(self):
        base_dir = os.path.dirname(UPLOAD_DIRECTORY)
        default_icon_path = os.path.join(base_dir, "defaults", DEFAULT_PROJECT_ICON)
        if not os.path.exists(default_icon_path):
            raise HTTPException(status_code=404, detail="Default project icon not found")
        return default_icon_path
    
    def delete_icon(self, user_id: int, project_id: int):
        if project_id is not None:
            project = ProjectRepository(self.db).get_project(project_id)
            if project is None:
                raise ValueError("Project not found")
            if project.owner_id != user_id:
                raise HTTPException(status_code=403, detail="Access Denied")
            if project.icon_id is None:
                raise ValueError("Project icon not found")
            attachment = AttachmentRepository(self.db).get_attachment_by_id(project.icon_id)
            if attachment is None:
                raise ValueError("Attachment not found")
            if not AttachmentRepository(self.db).delete_attachment(attachment_id=project.icon_id):
                raise HTTPException(status_code=500, detail="Failed to delete attachment")
            return
        founded_user = UserRepository(self.db).get_user(user_id)
        if not founded_user:
            raise ValueError("User not found")
        if founded_user.icon_id is None:
            raise ValueError("User icon not found")
        attachment = AttachmentRepository(self.db).get_attachment_by_id(founded_user.icon_id)
        if attachment is None:
            raise ValueError("Attachment not found")
        if not AttachmentRepository(self.db).delete_attachment(attachment.id):
            raise HTTPException(status_code=500, detail="Failed to delete attachment")
        return