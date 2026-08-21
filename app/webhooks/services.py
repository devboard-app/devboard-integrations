from uuid import UUID

import httpx

from app.integrations.services import get_integration


def send_discord_notification(team_id: UUID, event_type: str, message: str):
    integration = get_integration(team_id)
    if integration is None:
        return
    
    if integration.discord_webhook_url is not None and integration.enabled_triggers.get("discord", {}).get(event_type, False):
        httpx.post(integration.discord_webhook_url, json={"content": message})

def send_slack_notification(team_id: UUID, event_type: str, text: str):
    integration = get_integration(team_id)
    if integration is None:
        return
    if integration.slack_webhook_url is not None and integration.enabled_triggers.get("slack", {}).get(event_type, False):
        httpx.post(integration.slack_webhook_url, json={"text": text})