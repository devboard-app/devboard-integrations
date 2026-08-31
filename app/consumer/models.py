import uuid
from datetime import datetime, timezone

from app.db import db


class FailedEvent(db.Model):
    __tablename__ = "failed_events"

    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    message_id = db.Column(db.String, nullable=False, unique=True)
    event_type = db.Column(db.String, nullable=True)
    raw_data = db.Column(db.JSON, nullable=False)
    error = db.Column(db.Text, nullable=False)
    failed_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))