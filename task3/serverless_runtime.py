import os
import json
import time
import logging
import redis
from datetime import datetime
import importlib.util

REDIS_HOST = os.getenv('REDIS_HOST', '192.168.121.187')
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_INPUT_KEY = os.getenv('REDIS_INPUT_KEY')
REDIS_OUTPUT_KEY = os.getenv('REDIS_OUTPUT_KEY')
INTERVAL_TIME = int(os.getenv('INTERVAL', 5))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Context:
    def __init__(self, host, port, input_key, output_key):
        self.host = host
        self.port = port
        self.input_key = input_key
        self.output_key = output_key
        try:
            tmp = os.path.getmtime("/opt/usermodule.py")
            self.function_getmtime = datetime.fromtimestamp(tmp).strftime('%Y-%m-%d %H:%M:%S')
        except FileNotFoundError:
            logger.warning("[INFO] usermodule.py not found; function_getmtime set to 'Unknown'.")
            self.function_getmtime = "Unknown"
        self.last_execution = None
        self.env = {}

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

def load_user_module():
    module_spec = importlib.util.find_spec('usermodule')
    if module_spec is None:
        logger.error("[ERROR] 'usermodule' not found.")
        return None
    usermodule = importlib.util.module_from_spec(module_spec)
    try:
        module_spec.loader.exec_module(usermodule)
        return usermodule
    except Exception as e:
        logger.error(f"[ERROR] Error loading 'usermodule': {e}")
        return None

def fetch_data_from_redis(redis_client, key):
    try:
        data = redis_client.get(key)
        if data:
            return json.loads(data)
        logger.info(f"[INFO]  No data found for key: {key}")
    except redis.RedisError as e:
        logger.error(f"[ERROR] Redis error while fetching data for key '{key}': {e}")
    except json.JSONDecodeError as e:
        logger.error(f"[ERROR]  Error decoding JSON for key '{key}': {e}")
    return None

def store_data_in_redis(redis_client, key, data):
    try:
        redis_client.set(key, json.dumps(data))
        logger.info(f"[INFO] Data stored in Redis under key: {key}")
    except redis.RedisError as e:
        logger.error(f"[ERROR] Redis error while storing data for key '{key}': {e}")
    except TypeError as e:
        logger.error(f"[INFO] Error serializing data for key '{key}': {e}")

def execute_handler(usermodule, data, context):
    try:
        return usermodule.handler(data, context)
    except Exception as e:
        logger.error(f"[ERROR] Error in user-defined handler: {e}")
        return None

if __name__ == "__main__":
    redis_client = initialize_redis_client()
    if not redis_client:
        exit(1)

    usermodule = load_user_module()
    if not usermodule:
        exit(1)

    logger.info("[INFO] Starting serverless function execution...")
    context = Context(
        host=REDIS_HOST,
        port=REDIS_PORT,
        input_key=REDIS_INPUT_KEY,
        output_key=REDIS_OUTPUT_KEY
    )

    while True:
        data = fetch_data_from_redis(redis_client, REDIS_INPUT_KEY)
        if data:
            output = execute_handler(usermodule, data, context)
            if output and REDIS_OUTPUT_KEY:
                store_data_in_redis(redis_client, REDIS_OUTPUT_KEY, output)
        time.sleep(INTERVAL_TIME)
