from logs import logger
from metrics import get_percentage_of_outgoing_network_traffic, get_percentage_of_memory_caching_content, get_moving_average
            
def handler(input: dict, context: object) -> dict[str, float]:
    logger.info(f"[INFO] Handler function called with the following input: {input}")
    result = {
        'percent-network-egress': get_percentage_of_outgoing_network_traffic(input),
        'percent-memory-cache': get_percentage_of_memory_caching_content(input),
        **get_moving_average(input, context)
    }
    logger.info(f"[INFO] Handler function result: {result}")
    return result