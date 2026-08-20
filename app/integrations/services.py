from uuid import UUID

from app.integrations import repository
from app.integrations.models import TeamIntegration


def get_integration(team_id: UUID) -> TeamIntegration | None:
    return repository.get_integration_by_team(team_id)

def create_integration(team_id: UUID, data: dict) -> TeamIntegration:
    existing = repository.get_integration_by_team(team_id)
    if existing:
        raise ValueError("Integration settings already exist for this team.")
    return repository.create_integration(team_id, data)

def update_integration(team_id: UUID, data: dict) -> TeamIntegration:
    integration = repository.get_integration_by_team(team_id)
    if integration is None:
        raise ValueError("Integration settings not found for this team.")
    return repository.update_integration(integration, data)

