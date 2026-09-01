from uuid import UUID

from app.notifications.services import create_notification
from app.webhooks.services import send_discord_notification, send_slack_notification


def handle_ticket_assigned(data: dict) -> None:
    create_notification(
        recipient_id=data["recipient_id"],
        type="assignment",
        message=f"You have been assigned to ticket {data['ticket_key']}.",
        link=f"/tickets/{data['ticket_id']}",
    )

def handle_status_changed(data: dict) -> None:
    create_notification(
        recipient_id=data["recipient_id"],
        type="status_change",
        message=f"Ticket {data['ticket_key']} status has changed.",
        link=f"/tickets/{data['ticket_id']}",
    )

def handle_comment_created(data: dict) -> None:
    recipient_id = data.get("recipient_id")
    if recipient_id is None:
        return
    create_notification(
        recipient_id=recipient_id,
        type="comment",
        message=f"New comment on ticket {data['ticket_key']}.",
        link=f"/tickets/{data['ticket_id']}",
    )

def handle_mention(data: dict) -> None:
    create_notification(
        recipient_id=data["recipient_id"],
        type="mention",
        message=f"You were mentioned in a comment on ticket {data['ticket_key']}.",
        link=f"/tickets/{data['ticket_id']}",
    )

def handle_sprint_started(data: dict) -> None:
    send_discord_notification(
        team_id=UUID(data["team_id"]),
        event_type="sprint.started",
        message=f"🚀 Sprint '{data["sprint_name"]}' has started!",
    )
    send_slack_notification(
        team_id=UUID(data["team_id"]),
        event_type="sprint.started",
        text=f"🚀 Sprint '{data["sprint_name"]}' has started!",
    )

def handle_sprint_completed(data: dict) -> None:
    send_discord_notification(
        team_id=UUID(data["team_id"]),
        event_type="sprint.completed",
        message=f"✅ Sprint '{data["sprint_name"]}' has been completed!",
    )
    send_slack_notification(
        team_id=UUID(data["team_id"]),
        event_type="sprint.completed",
        text=f"✅ Sprint '{data["sprint_name"]}' has been completed!",
    )

HANDLERS ={
    "ticket.assigned": handle_ticket_assigned,
    "ticket.status_changed": handle_status_changed,
    "comment.created": handle_comment_created,
    "comment.mentioned": handle_mention,
    "sprint.started": handle_sprint_started,
    "sprint.completed": handle_sprint_completed,
}