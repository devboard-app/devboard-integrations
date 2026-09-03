from uuid import UUID

from flask import Blueprint, jsonify

from app.auth import jwt_required
from app.notifications import services

notifications_bp = Blueprint("notifications", __name__)

@notifications_bp.get("/api/notifications/")
@jwt_required
def get_notifications(user_id: UUID):
    notifications = services.get_user_notifications(user_id)
    return jsonify([n.to_dict() for n in notifications])

@notifications_bp.patch("/api/notifications/read-all/")
@jwt_required
def mark_all_as_read(user_id: UUID):
    services.mark_all_notifications_read(user_id)
    return jsonify({"message": "All notifications marked as read"})

@notifications_bp.patch("/api/notifications/<uuid:notification_id>/")
@jwt_required
def mark_as_read(user_id: UUID, notification_id: UUID):
    notification = services.mark_notification_read(notification_id, user_id)
    return jsonify(notification.to_dict())

@notifications_bp.delete("/api/notifications/<uuid:notification_id>/")
@jwt_required
def delete_notification(user_id: UUID, notification_id: UUID):
    services.delete_user_notification(notification_id, user_id)
    return "",204