from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.integrations import repository
from app.integrations.models import RepoLink, TeamIntegration


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



def create_repo_link(team_id: UUID, project_id: UUID, github_repo: str) -> RepoLink:
    existing = repository.get_repo_link_by_github_repo(github_repo)
    if existing:
        raise ValueError("This repository is already linked to a project.")
    try:
        return repository.create_repo_link(team_id, project_id, github_repo)
    except IntegrityError:
        raise ValueError("This repository is already linked to a project.")

def delete_repo_link(team_id: UUID, repo_link_id: UUID) -> None:
    link = repository.get_repo_link_by_id(repo_link_id)
    if link is None or link.team_id != team_id:
        raise ValueError("Repo link not found for this team.")
    repository.delete_repo_link(link)