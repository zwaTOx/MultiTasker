from pydantic import BaseModel

class VerifyCodeRequest(BaseModel):
    temp_token: str
    code: str

class NewPasswordRequest(BaseModel):
    reset_token: str
    new_password: str
    confirm_password: str

