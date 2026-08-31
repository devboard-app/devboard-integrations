import logging

from sqlalchemy.exc import IntegrityError

from app.consumer.models import FailedEvent
from app.db import db

logger = logging.getLogger(__name__)


def record_failed_event(message_id: str, data: dict, error: str) -> None:
    db.session.add(FailedEvent(message_id=message_id, event_type=data.get("event"), raw_data=data, error=error)) # type:ignore
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        logger.info(f"{message_id} was already dead-lettered")