import os
from sqlalchemy.orm import Session

from ..exceptions import AttachmentNotFound
from ..user.schemas import AttachmentResponse
from ..database import Sessionlocal
from ..models_db import Attachment as db_Attachment
from ..models_db import User as db_User
from ..models_db import Project as db_Project

UPLOAD_DIRECTORY = r'C:\Users\Пользователь\Documents\Python\projects\MultiTasker\data\attachments'

class AttachmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def add_attachment(self, path: str) -> AttachmentResponse:
        new_attachment = db_Attachment(path=path)
        self.db.add(new_attachment)
        self.db.commit()
        self.db.refresh(new_attachment)
        return AttachmentResponse(
            id = new_attachment.id,
            path = new_attachment.path
        )
    
    def get_attachment_by_id(self, attachment_id: int) -> db_Attachment:
        attachment = self.db.query(db_Attachment).filter(db_Attachment.id == attachment_id).first()
        if attachment is None:
            raise AttachmentNotFound(attachment_id)
        return attachment
    
    def delete_attachment(self, attachment_id: int):
        attachment = self.get_attachment_by_id(attachment_id)
        self.db.delete(attachment)
        self.db.commit()
        file_path = os.path.join(UPLOAD_DIRECTORY, attachment.path)
        if os.path.exists(file_path):
                os.remove(file_path)
    
    def update_user_icon(self, user_id: int, attachment_id: int) -> db_User|None:
        user = self.db.query(db_User).filter(db_User.id == user_id).first()
        if not user:
            return None
        user.icon_id = attachment_id
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update_project_icon(self, project_id: int, attachment_id: int) -> bool:
        project = self.db.query(db_Project).filter(db_Project.id == project_id).first()
        if not project:
            return False
        project.icon_id = attachment_id
        self.db.commit()
        return True

    def check_attachment_exist(self, attach_id):
        attach = self.db.query(db_Attachment).filter(db_Attachment.id == attach_id).first()
        if attach is None:
            raise AttachmentNotFound(attach_id)