
from fastapi import HTTPException
from ..email_controller import send_recovery_code
from ..auth.code_repository import CodeRepository


class CodeService:
    def __init__(self, db):
        self.db = db
        
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