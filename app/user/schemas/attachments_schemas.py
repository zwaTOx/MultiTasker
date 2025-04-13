
from pydantic import BaseModel


class AttachmentResponse(BaseModel):
    id: str
    path: str
