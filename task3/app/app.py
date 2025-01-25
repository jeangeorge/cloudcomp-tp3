import time

from redis_utils import *
from handler import get_handler, execute_handler
from local_env import *
from context import Context

if __name__ == "__main__":
    redis_client = initialize_redis_client()
    if not redis_client:
        exit(1)

    handler = get_handler()

    if not handler:
        logger.error("[ERROR] No valid serverless function entrypoint found. Exiting.")
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
            output = execute_handler(handler, data, context)
            if output and REDIS_OUTPUT_KEY:
                store_data_in_redis(redis_client, REDIS_OUTPUT_KEY, output)
        time.sleep(REDIS_MONITORING_PERIOD)
