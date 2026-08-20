from redis import Redis

from app.config import settings

redis_client = Redis.from_url(settings.REDIS_URL, decode_response=True)
