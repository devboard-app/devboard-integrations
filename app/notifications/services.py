from uuid import UUID

from app.exceptions import NotificationNotFoundException
from app.notifications import repository
from app.notifications.models import Notification


def get_user_notifications(recipient_id: UUID) -> list[Notification]:
    return repository.get_notifications_by_user(recipient_id)

def mark_notification_read(notification_id: UUID, recipient_id: UUID) -> Notification:
    notification = repository.get_notification_by_id(notification_id)
    if notification is None or notification.recipient_id != recipient_id:
        raise NotificationNotFoundException()
    return repository.mark_as_read(notification)

def mark_all_notifications_read(recipient_id: UUID) -> None:
    repository.mark_all_as_read(recipient_id)

def delete_user_notification(notification_id: UUID, recipient_id: UUID) -> None:
    notification = repository.get_notification_by_id(notification_id)
    if notification is None or notification.recipient_id != recipient_id:
        raise NotificationNotFoundException()
    repository.delete_notification(notification)

def create_notification(recipient_id: UUID, type: str, message: str, link: str | None) -> Notification:
    return repository.create_notification(recipient_id, type, message, link)

