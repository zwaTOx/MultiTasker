from fastapi.staticfiles import StaticFiles
import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
from fastapi.middleware.cors import CORSMiddleware
#import auth, profile, Category.category, Project.project

from .database import engine, Sessionlocal, Base
from .auth.auth import get_current_user
from .auth.auth import router as auth_router
from .user.routers.profile import router as profile_router
from .category.category import router as category_router
from .project.routes.my_project import router as my_project_router
from .project.routes.project import router as project_router
from .task.task import router as task_router
from .user.routers.project_user_controller import router as project_user_controller_router
from .user.routers.attachments import router as file_router
from .user.routers.admin import router as admin_router

app = FastAPI()
Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = Sessionlocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(file_router)
app.include_router(project_user_controller_router)
app.include_router(category_router)
app.include_router(my_project_router)
app.include_router(project_router)
app.include_router(task_router)
app.include_router(admin_router)

@app.get("/")
async def get_user(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Auth Failed")
    return user

# @app.get("/users/{user_id}")
# async def get_user_by_id(user_id: int, db: db_dependency):
#     user = db.query(User).filter(User.id == user_id).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#     return {
#         "id": user.id,
#         "login": user.login,
#         "username": user.username,
#     }

if __name__ == '__main__':
    config = uvicorn.Config(app, port=8000, reload=True)
    server = uvicorn.Server(config)
    server.run()