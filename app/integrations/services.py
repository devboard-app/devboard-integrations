from urllib.parse import urlparse
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.exceptions import (
    IntegrationAlreadyExistsException,
    IntegrationNotFoundException,
    InvalidWebhookUrlException,
    RepoLinkAlreadyExistsException,
    RepoLinkNotFoundException,
)
from app.integrations import repository
from app.integrations.models import RepoLink, TeamIntegration

ALLOWED_HOSTS = {
    "slack": {"hooks.slack.com"},
    "discord": {"discord.com", "discordapp.com"},
}

def _validate_webhook_url(url: str | None, provider: str) -> None:
    if url is None:
        return
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS[provider]:
        raise InvalidWebhookUrlException()

def get_integration_or_404(team_id: UUID) -> TeamIntegration:
    integration = repository.get_integration_by_team(team_id)
    if integration is None:
        raise IntegrationNotFoundException()
    return integration

def create_integration(team_id: UUID, data: dict) -> TeamIntegration:
    existing = repository.get_integration_by_team(team_id)
    if existing:
        raise IntegrationAlreadyExistsException()
    _validate_webhook_url(data.get("slack_webhook_url"), "slack")
    _validate_webhook_url(data.get("discord_webhook_url"), "discord")
    return repository.create_integration(team_id, data)

def update_integration(team_id: UUID, data: dict) -> TeamIntegration:
    integration = repository.get_integration_by_team(team_id)
    if not integration:
        raise IntegrationNotFoundException()
    _validate_webhook_url(data.get("slack_webhook_url"), "slack")
    _validate_webhook_url(data.get("discord_webhook_url"), "discord")
    return repository.update_integration(integration, data)



def create_repo_link(team_id: UUID, project_id: UUID, github_repo: str) -> RepoLink:
    existing = repository.get_repo_link_by_github_repo(github_repo)
    if existing:
        raise RepoLinkAlreadyExistsException()
    try:
        return repository.create_repo_link(team_id, project_id, github_repo)
    except IntegrityError:
        raise RepoLinkAlreadyExistsException()

def delete_repo_link(team_id: UUID, repo_link_id: UUID) -> None:
    link = repository.get_repo_link_by_id(repo_link_id)
    if link is None or link.team_id != team_id:
        raise RepoLinkNotFoundException()
    repository.delete_repo_link(link)