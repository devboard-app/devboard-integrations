import uuid
from datetime import datetime, timezone

from app.db import db


class TeamIntegration(db.Model):
    __tablename__ = "team_integrations"

    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    team_id = db.Column(db.Uuid, nullable=False, unique=True)
    slack_webhook_url = db.Column(db.Text, nullable=True)
    discord_webhook_url = db.Column(db.Text, nullable=True)
    email_notifications = db.Column(db.Boolean, nullable=False, default=False)
    enabled_triggers = db.Column(db.JSON, nullable=False, default=dict)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": str(self.id),
            "team_id": str(self.team_id),
            "slack_webhook_url": self.slack_webhook_url,
            "discord_webhook_url": self.discord_webhook_url,
            "email_notifications": self.email_notifications,
            "enabled_triggers": self.enabled_triggers,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }