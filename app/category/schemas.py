from pydantic import BaseModel

class CategoryResponseSchema(BaseModel):
    id: int
    name: str
    color: str