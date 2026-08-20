from app.notifications.services import create_notification


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
    create_notification(
        recipient_id=data["recipient_id"],
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

HANDLERS ={
    "ticket.assigned": handle_ticket_assigned,
    "ticket.status_changed": handle_status_changed,
    "comment.created": handle_comment_created,
    "comment.mention": handle_mention,
}