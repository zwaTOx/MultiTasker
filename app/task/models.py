

from datetime import datetime, timezone
from sqlalchemy.orm import relationship
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from ..database import Base

class Task(Base):
    __tablename__ = 'task'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    description = Column(String) 
    indicator = Column(String) #Индикатор важности: red, orange, yellow, green
    status = Column(String, default='Назначена') #Назначена, В работе, Выполнена
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_change = Column(DateTime, default=lambda: datetime.now(timezone.utc)) 
    deadline = Column(DateTime) 

    owner_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    performer_id = Column(Integer, ForeignKey('user.id', ondelete="SET NULL"))
    project_id = Column(Integer, ForeignKey('project.id'))
    parent_task_id = Column(Integer, ForeignKey('task.id', ondelete="SET NULL"))

    # M:1
    task_performer = relationship('User', foreign_keys=[performer_id], back_populates='tasks_performed')
    task_owner = relationship("User", foreign_keys=[owner_id], back_populates='tasks_owned')
    project = relationship('Project', back_populates='tasks')
    parent_task = relationship("Task", remote_side=[id], back_populates="subtasks")

    # 1:M
    subtasks = relationship("Task", back_populates="parent_task", cascade="all, delete-orphan")
