from fastapi import HTTPException, status

class CategoryNotFound(HTTPException):
    def __init__(self, category_id: int = None, user_id: int = None):
        detail = "Category not found"
        if category_id and user_id:
            detail = f"Category with id {category_id} for user {user_id} not found"
        if category_id:
            detail = f"Category with id {category_id} not found"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )

