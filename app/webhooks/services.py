import logging
import re
from uuid import UUID

import httpx

from app.config import settings
from app.integrations.repository import (
    get_integration_by_team,
    get_repo_link_by_github_repo,
    record_linked_commit,
)
from app.redis_client import redis_client

SYSTEM_ACTOR_ID = "00000000-0000-0000-0000-000000000000"

logger = logging.getLogger(__name__)
def send_discord_notification(team_id: UUID, event_type: str, message: str):
    integration = get_integration_by_team(team_id)
    if integration is None:
        return
    
    if integration.discord_webhook_url is not None and integration.enabled_triggers.get("discord", {}).get(event_type, False):
        try:
            httpx.post(integration.discord_webhook_url, json={"content": message}, timeout=3.0)
        except httpx.HTTPError:
            logger.exception(f"Failed to send Discord notification for team {team_id}")

def send_slack_notification(team_id: UUID, event_type: str, text: str):
    integration = get_integration_by_team(team_id)
    if integration is None:
        return
    
    if integration.slack_webhook_url is not None and integration.enabled_triggers.get("slack", {}).get(event_type, False):
        try:
            httpx.post(integration.slack_webhook_url, json={"text": text}, timeout=3.0)
        except httpx.HTTPError:
            logger.exception(f"Failed to send Slack notification for team {team_id}")

TICKET_KEY_PATTERN = re.compile(r"\b([A-Z][A-Z0-9]{1,9}-\d+)\b", re.IGNORECASE)

def extract_ticket_keys(commit_message: str) -> set[str]:
    return {key.upper() for key in TICKET_KEY_PATTERN.findall(commit_message)} 

def handle_github_push(payload: dict) -> None:
    repo = payload["repository"]["full_name"]
    link = get_repo_link_by_github_repo(repo)
    commits = payload.get("commits", [])

    if link is None:
        logger.info(f"Push for unlinked repo {repo}, ignoring")
        return

    for commit in commits:
        ticket_keys = set(extract_ticket_keys(commit["message"]))
        for key in ticket_keys:
            try:
                ticket = lookup_ticket(link.project_id, key)
                if ticket is None:
                    continue
                if not record_linked_commit(repo, commit["id"], UUID(ticket["id"])):
                    logger.info(f"Commit {commit['id']} already linked to {key}, skipping")
                    continue
                publish_commit_linked(ticket["id"], key, str(link.project_id), commit, repo)
            except Exception:
                logger.exception(f"Failed to link commit {commit["id"]} to {key}")

def lookup_ticket(project_id, key: str) -> dict | None:
    response = httpx.get(
        f"{settings.DEVBOARD_WORK_URL}/api/internal/projects/{project_id}/tickets/{key}/",
        headers={"X-Service-Key": settings.INTERNAL_API_KEY},
        timeout=3.0,
    )
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()

def publish_commit_linked(ticket_id: str, key: str, project_id: str, commit: dict, repo: str) -> None:
    redis_client.xadd("devboard:events", {
        "event": "ticket.commit_linked",
        "actor_id": SYSTEM_ACTOR_ID,
        "ticket_id": ticket_id,
        "ticket_key": key,
        "project_id": project_id,
        "commit_sha": commit["id"],
        "commit_url": commit["url"],
        "commit_message": commit["message"],
        "repo": repo,
    })