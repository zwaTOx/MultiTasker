from typing import List, Optional
from sqlalchemy import desc
from sqlalchemy.orm import Session
from ..models_db import Notification

class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_notifications(self, user_id: int) -> List[Notification]:
        query = self.db.query(Notification)\
            .filter(Notification.user_id == user_id)\
            .order_by(desc(Notification.date))
        return query.all()

    def create_notification(self, user_id: int, text: str):
        notification = Notification(
            user_id=user_id,
            text=text
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification
    
    def mark_as_read(self, notification_id: int) -> Optional[Notification]:
        notification = self.db.query(Notification)\
            .filter(Notification.id == notification_id)\
            .first()
        if notification:
            notification.is_read = True 
            self.db.commit()
            self.db.refresh(notification)
        return notification
