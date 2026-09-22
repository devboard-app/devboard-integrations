import logging
import re
import time
from uuid import UUID

import httpx

from app import work_client
from app.integrations.repository import (
    delete_linked_commit,
    get_integration_by_team,
    get_repo_link_by_github_repo,
    record_linked_commit,
)
from app.redis_client import redis_client

SYSTEM_ACTOR_ID = "00000000-0000-0000-0000-000000000000"

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3
RETRY_DELAY_SECONDS = [2, 4]  # between attempts 1->2 and 2->3


def _post_with_retry(url: str, json_payload: dict, label: str) -> None:
    """POST with retry on transient failures (timeouts, connection errors,
    5xx). Runs on the background consumer, not a user-facing request, so the
    delay only costs queue throughput -- never a client waiting on it. A 4xx
    is the webhook rejecting the request itself (bad URL, bad payload) and
    won't be fixed by retrying, so it fails immediately instead.
    """
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = httpx.post(url, json=json_payload, timeout=3.0)
            response.raise_for_status()
            return
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500:
                logger.exception(f"{label} rejected the request, not retrying")
                return
            if attempt == MAX_ATTEMPTS:
                logger.exception(f"{label} failed after {attempt} attempts")
                return
            logger.warning(f"{label} failed (attempt {attempt}, {e.response.status_code}), retrying")
            time.sleep(RETRY_DELAY_SECONDS[attempt - 1])
        except httpx.TransportError:
            if attempt == MAX_ATTEMPTS:
                logger.exception(f"{label} failed after {attempt} attempts")
                return
            logger.warning(f"{label} failed (attempt {attempt}), retrying")
            time.sleep(RETRY_DELAY_SECONDS[attempt - 1])


def send_discord_notification(team_id: UUID, event_type: str, message: str):
    integration = get_integration_by_team(team_id)
    if integration is None:
        return

    if integration.discord_webhook_url is not None and integration.enabled_triggers.get("discord", {}).get(event_type, False):
        _post_with_retry(integration.discord_webhook_url, {"content": message}, f"Discord notification for team {team_id}")

def send_slack_notification(team_id: UUID, event_type: str, text: str):
    integration = get_integration_by_team(team_id)
    if integration is None:
        return

    if integration.slack_webhook_url is not None and integration.enabled_triggers.get("slack", {}).get(event_type, False):
        _post_with_retry(integration.slack_webhook_url, {"text": text}, f"Slack notification for team {team_id}")

TICKET_KEY_PATTERN = re.compile(r"\b([A-Z][A-Z0-9]{1,9}-\d+)\b", re.IGNORECASE)

def extract_ticket_keys(commit_message: str) -> set[str]:
    return {key.upper() for key in TICKET_KEY_PATTERN.findall(commit_message)} 

def handle_github_push(payload: dict) -> bool:
    repo = payload["repository"]["full_name"]
    link = get_repo_link_by_github_repo(repo)
    commits = payload.get("commits", [])

    if link is None:
        logger.info(f"Push for unlinked repo {repo}, ignoring")
        return True

    all_linked = True
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
                try:
                    publish_commit_linked(ticket["id"], key, str(link.project_id), commit, repo)
                except Exception:
                    logger.exception(f"Failed to publish commit_linked for {commit['id']} / {key}, undoing link")
                    delete_linked_commit(repo, commit["id"], UUID(ticket["id"]))
                    all_linked = False
            except Exception:
                logger.exception(f"Failed to link commit {commit["id"]} to {key}")
                all_linked = False
    return all_linked

def lookup_ticket(project_id, key: str) -> dict | None:
    response = work_client.get_internal(f"/api/internal/projects/{project_id}/tickets/{key}/")
    if response is None:
        logger.warning(f"Work service unavailable looking up ticket {key} in project {project_id}")
        return None
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