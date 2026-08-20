import uuid
from datetime import datetime, timezone

from app.db import db


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    recipient_id = db.Column(db.Uuid, nullable=False)
    type = db.Column(db.String, nullable=False)
    message = db.Column(db.Text, nullable=False)
    read = db.Column(db.Boolean, nullable=False, default=False)
    link = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
        "id": str(self.id),
        "type": self.type,
        "message": self.message,
        "read": self.read,
        "link": self.link,
        "created_at": self.created_at.isoformat(),
        }