import redis
import json

from logs import logger
from local_env import REDIS_PORT, REDIS_HOST, REDIS_INPUT_KEY, REDIS_OUTPUT_KEY

def initialize_redis_client():
    if not REDIS_INPUT_KEY:
        logger.error("[ERROR] Environment variable 'REDIS_INPUT_KEY' must be set.")
        return None
    if not REDIS_OUTPUT_KEY:
        logger.warning("[WARNING] Environment variable 'REDIS_OUTPUT_KEY' is not set. Output will not be stored in Redis.")
    try:
        return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, charset="utf-8", decode_responses=True)
    except redis.RedisError as e:
        logger.error(f"[ERROR] Failed to connect to Redis: {e}")
        return None

def fetch_data_from_redis(redis_client, key):
    try:
        data = redis_client.get(key)
        if data:
            return json.loads(data)
        logger.info(f"[INFO] No data found for key: {key}")
    except redis.RedisError as e:
        logger.error(f"[ERROR] Redis error while fetching data for key '{key}': {e}")
    except json.JSONDecodeError as e:
        logger.error(f"[ERROR] Error decoding JSON for key '{key}': {e}")
    return None

def store_data_in_redis(redis_client, key, data):
    try:
        redis_client.set(key, json.dumps(data))
        logger.info(f"[INFO] Data stored in Redis under key: {key}")
    except redis.RedisError as e:
        logger.error(f"[ERROR] Redis error while storing data for key '{key}': {e}")
    except TypeError as e:
        logger.error(f"[INFO] Error serializing data for key '{key}': {e}")