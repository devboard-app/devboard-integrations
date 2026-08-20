from uuid import UUID

from app.db import db
from app.integrations.models import TeamIntegration


def get_integration_by_team(team_id: UUID) -> TeamIntegration | None:
    return db.session.execute(
        db.select(TeamIntegration).where(TeamIntegration.team_id == team_id)
    ).scalars().first()

def create_integration(team_id: UUID, data: dict) -> TeamIntegration:
    integration = TeamIntegration(team_id=team_id, slack_webhook_url=data.get("slack_webhook_url"), discord_webhook_url=data.get("discord_webhook_url"), email_notifications=data.get("email_notifications", False), enabled_triggers=data.get("enabled_triggers", {}),) # type:ignore
    db.session.add(integration)
    db.session.commit()
    return integration

def update_integration(integration: TeamIntegration, data: dict) -> TeamIntegration:
    for key, value in data.items():
        if hasattr(integration, key):
            setattr(integration, key, value)
    db.session.commit()
    return integration

