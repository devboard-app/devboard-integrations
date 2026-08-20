import logging
import time

from app import create_app
from app.consumer.handlers import HANDLERS
from app.redis_client import redis_client

STREAM = "devboard:events"
GROUP = "devboard-integrations-group"
CONSUMER = "devboard-integrations-1"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_group():
    try:
        redis_client.xgroup_create(STREAM, GROUP, id="0", mkstream=True)
        logger.info("Consumer group created.")
    except Exception: #noqa
        logger.info("Consumer group already exists.")

def run():
    flask_app = create_app()
    ensure_group()
    logger.info("Consumer started, waiting for events...")

    while True:
        try:
            results = redis_client.xreadgroup(GROUP, CONSUMER, {STREAM: ">"}, count=10, block=5000)
            if not results:
                continue

            for stream, messages in results:
                for message_id, data in messages: #type: ignore
                    event_type = data.get("event")
                    handler = HANDLERS.get(event_type)

                    if handler is None:
                        logger.warning(f"No handler for event: {event_type}")
                        redis_client.xack(STREAM, GROUP, message_id)
                        continue

                    try:
                        with flask_app.app_context():
                            handler(data)
                        redis_client.xack(STREAM, GROUP, message_id)
                    except Exception as e: #noqa
                        logger.error(f"Handler failed for {event_type}: {e}")
        except Exception as e: #noqa
            logger.error(f"Consumer error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    run()