# src/database/redis.py
import os
import logging
import redis

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

_client: redis.Redis | None = None

def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(REDIS_URL, decode_responses=True)
        try:
            _client.ping()
            logger.info(f"[redis] connected: {REDIS_URL}")
        except Exception as e:
            logger.error(f"[redis] connect failed: {e}")
            raise
    return _client

def get_pubsub() -> redis.client.PubSub:
    return get_redis().pubsub()
