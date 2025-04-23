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

class UserNotFound(HTTPException):
    def __init__(self, user_id: int = None):
        detail = "User not found"
        if user_id:
            detail = f"User with id {user_id} not found"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )

class ProjectNotFound(HTTPException):
    def __init__(self, project_id: int = None):
        detail = "Project not found"
        if project_id:
            detail = f"Project with id {project_id} not found"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )

class AttachmentNotFound(HTTPException):
    def __init__(self, attachment_id: int = None):
        detail = "Attachment not found"
        if attachment_id:
            detail = f"Attachment with id {attachment_id} not found"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )

class TaskNotFound(HTTPException):
    def __init__(self, task_id: int = None):
        detail = "Task not found"
        if task_id:
            detail = f"Attachment with id {task_id} not found"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )