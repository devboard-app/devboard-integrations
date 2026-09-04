import logging
import time

from app import create_app
from app.consumer.dead_letter import record_failed_event
from app.consumer.handlers import HANDLERS
from app.redis_client import redis_client

STREAM = "devboard:events"
GROUP = "devboard-integrations-group"
CONSUMER = "devboard-integrations-1"

MAX_ATTEMPTS = 3
RECLAIM_IDLE_MS = 60_000

logger = logging.getLogger(__name__)

def ensure_group():
    try:
        redis_client.xgroup_create(STREAM, GROUP, id="0", mkstream=True)
        logger.info("Consumer group created.")
    except Exception: #noqa
        logger.info("Consumer group already exists.")

def run():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    flask_app = create_app()
    ensure_group()
    logger.info("Consumer started, waiting for events...")

    while True:
        try:
            claimed = []
            cursor = "0-0"
            for _ in range(50):
                cursor, batch, _ = redis_client.xautoclaim(
                    STREAM, GROUP, CONSUMER,
                    min_idle_time=RECLAIM_IDLE_MS, start_id=cursor, count=100,
                )
                claimed.extend(batch)
                if cursor == "0-0":
                    break
            else:
                logger.warning("Reclaim scan hit the iteration cap, continuing anyway")

            if claimed:
                logger.warning(f"Reclaimed {len(claimed)} pending messages")

            attempts = {
                entry["message_id"]: int(entry["times_delivered"])
                for entry in redis_client.xpending_range(STREAM, GROUP, min="-", max="+", count=100)
            } if claimed else {}

            results = redis_client.xreadgroup(GROUP, CONSUMER, {STREAM: ">"}, count=10, block=5000)
            all_messages = claimed + (results[0][1] if results else []) #type: ignore

        
            for message_id, data in all_messages: #type: ignore
                event_type = data.get("event")
                handler = HANDLERS.get(event_type)

                if handler is None:
                    logger.warning(f"No handler for event: {event_type}")
                    redis_client.xack(STREAM, GROUP, message_id)
                    continue
                if attempts.get(message_id, 1) > MAX_ATTEMPTS:
                    with flask_app.app_context():
                        record_failed_event(message_id, data, "max attempts exceeded")
                        redis_client.xack(STREAM, GROUP, message_id)
                        logger.error(f"Gave up on {message_id} after {attempts[message_id]} attempts")
                        continue
                try:
                    with flask_app.app_context():
                        handler(data)
                    redis_client.xack(STREAM, GROUP, message_id)
                except Exception as e: 
                    logger.error(f"Handler failed for {event_type}: {e}", exc_info=True) #noqa
        except Exception as e: #noqa
            logger.error(f"Consumer error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    run()