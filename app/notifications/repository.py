from uuid import UUID

from app.db import db
from app.notifications.models import Notification


def get_notifications_by_user(recipient_id: UUID) -> list[Notification]:
    return list(db.session.execute(
        db.select(Notification)
        .where(Notification.recipient_id == recipient_id)
        .order_by(Notification.created_at.desc())
    ).scalars().all())

def get_notification_by_id(notification_id: UUID) -> Notification | None:
    return db.session.get(Notification, notification_id)

def create_notification(recipient_id: UUID, type: str, message: str, link: str | None) -> Notification:
    notification = Notification(recipient_id=recipient_id, type=type, message=message, link=link) #type: ignore
    db.session.add(notification)
    db.session.commit()
    return notification

def mark_as_read(notification: Notification) -> Notification:
    notification.read = True
    db.session.commit()
    return notification

def mark_all_as_read(recipient_id: UUID) -> None:
    db.session.execute(
        db.update(Notification)
        .where(Notification.recipient_id == recipient_id)
        .values(read=True)
    )
    db.session.commit()

def delete_notification(notification: Notification) -> None:
    db.session.delete(notification)
    db.session.commit()