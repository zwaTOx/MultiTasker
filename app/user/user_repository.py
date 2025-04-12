from sqlalchemy.orm import Session
from ..models_db import User as db_User

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user(self, user_id: int):
        user = self.db.query(db_User).filter(db_User.id==user_id).first()
        return user
    
    def get_users(self):
        users = self.db.query(db_User.id, db_User.login, db_User.username).all()
        return users
    
    def get_user_by_email(self, email: str):
        user = self.db.query(db_User).filter(db_User.login==email).first()
        return user
    
    def update_user_icon(self, user: db_User, filename: str):
        user.icon = filename
        self.db.commit()
        return user
    
    def delete_user_icon(self, user: db_User):
        user.icon = None
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def create_unverified_user(self, user_email: str):
        existing_user = self.db.query(db_User).filter(db_User.login == user_email).first()
        if existing_user:
            return existing_user
        new_user_model = db_User(
            login = user_email,
            is_verified = False
        )
        self.db.add(new_user_model)
        self.db.commit()
        return new_user_model
    
    def check_admin_perms(self, user_id):
        user = self.db.query(db_User).filter(db_User.id==user_id).first()
        return user.is_admin