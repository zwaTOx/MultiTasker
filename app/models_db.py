from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, autoincrement=True)
    login = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    username = Column(String)
    icon_id = Column(Integer, ForeignKey('attachment.id', ondelete="SET NULL"))
    is_verified = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)

    #1:1
    icon_attachment = relationship("Attachment", foreign_keys=[icon_id], passive_deletes=True)

    # 1:M
    notifications = relationship('Notification', back_populates='user', cascade="all, delete-orphan")
    categories = relationship('Category', back_populates='user', cascade="all, delete-orphan")
    projects = relationship('Project', back_populates='owner', cascade="all, delete-orphan")
    tasks_owned = relationship('Task', back_populates='task_owner', foreign_keys='Task.owner_id')
    tasks_performed = relationship('Task', back_populates='task_performer', foreign_keys='Task.performer_id')
    project_associations = relationship(
        "UserProjectAssociation", back_populates="user", cascade="all, delete-orphan"
    )

class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    color = Column(String)
    user_id = Column(Integer, ForeignKey('user.id'))

    # M:1
    user = relationship("User", back_populates="categories")
    # 1:M
    projects = relationship('UserProjectAssociation', back_populates='category', cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = 'project'
    id = Column(Integer, primary_key=True, autoincrement=True)
    icon_id = Column(Integer, ForeignKey('attachment.id', ondelete="SET NULL"))
    name = Column(String)
    user_id = Column(Integer, ForeignKey('user.id'))
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    #1:1
    icon_attachment = relationship("Attachment", foreign_keys=[icon_id])
    # M:1
    owner = relationship('User', back_populates='projects')
    # 1:M
    tasks = relationship('Task', back_populates='project', cascade="all, delete-orphan")
    user_associations = relationship(
        "UserProjectAssociation", back_populates="project_associations", cascade="all, delete-orphan")

class UserProjectAssociation(Base):
    __tablename__ = 'user_project_association'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    project_id = Column(Integer, ForeignKey('project.id'), primary_key=True)
    category_id = Column(Integer, ForeignKey('category.id', ondelete="SET NULL"))
    joined_at = Column(DateTime, default=datetime.now(timezone.utc))

    user = relationship('User', back_populates='project_associations')
    project_associations = relationship('Project', back_populates='user_associations')
    category = relationship('Category', back_populates='projects')


class Attachment(Base):
    __tablename__ = 'attachment'
    id = Column(Integer, primary_key=True, autoincrement=True)
    path = Column(String, unique=True)

    users = relationship("User", back_populates="icon_attachment")
    projects = relationship("Project", back_populates="icon_attachment")

class Notification(Base):
    __tablename__ = 'notification'
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, default=datetime.now(timezone.utc))
    text = Column(String)
    is_read = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey('user.id'))

    user = relationship('User', back_populates='notifications')

