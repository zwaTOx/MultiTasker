
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from ..database import Base


class PasswordResetCode(Base):
    __tablename__ = 'password_reset_codes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    code = Column(String(6), nullable=False, index=True)  
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))