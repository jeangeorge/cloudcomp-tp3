import datetime

from logs import logger
from utils import get_average_usage, get_measurement_datetime, get_updated_history_list

# Function to calculate the percentage of outgoing network traffic
def get_percentage_of_outgoing_network_traffic(input: dict) -> float:
    # Get the input values, fallback to 0 if not present
    bytes_sent = input.get('net_io_counters_eth0-bytes_sent', 0)
    bytes_received = input.get('net_io_counters_eth0-bytes_recv', 0)
    
    # Calculate thhe total
    bytes_total = bytes_sent + bytes_received
    
    # If the total is 0, we return 0 to avoid division by 0
    if (bytes_total == 0):
        logger.warning("[WARNING] Total bytes is 0, avoiding division by zero.")
        return 0

    # Return the percentage value
    result = (bytes_sent / bytes_total) * 100.0
    logger.info(f"[INFO] Percentage of outgoing network traffic: {result}")
    return result

# Function to calculate the percentage of memory caching content
def get_percentage_of_memory_caching_content(input: dict) -> float:
    # Get the input values, fallbacking to 0 or 1 if not present
    memory_cached = input.get('virtual_memory-cached', 0)
    memory_buffers = input.get('virtual_memory-buffers', 0)
    memory_total = input.get('virtual_memory-total', 1)
    
    # Return the percentage value
    result = ((memory_cached + memory_buffers) / memory_total) * 100.0
    logger.info(f"[INFO] Percentage of memory caching content: {result}")
    return result

def get_moving_average(input: dict, context: object) -> dict[str, float]:
    # Create empty result dict to store the moving average for each CPU
    result = {}
    
    # Get the measurement datetime, will be the timestemp received as input converted to a datime or the current datetime
    measurement_datetime = get_measurement_datetime(input)
    
    # Calculate the cutoff datetime, we  will use this above to keep only valid measurements in the context.env
    cutoff_datetime = measurement_datetime - datetime.timedelta(seconds=60) 
    
    # Iterate on keys that starts with 'cpu_percent-'
    for key in input.keys():
        if key.startswith('cpu_percent-'):
            # Get the CPU usage value received as input or fallback to 0
            cpu_usage = input.get(key, 0.0)
            
            # Get the updated CPU usage history list (a list of CPU usages with measurements that happened at the last minute)
            history_list = get_updated_history_list(context, key, cutoff_datetime)
            
            # Add the current CPU usage to the lsit
            history_list.append((measurement_datetime, cpu_usage))
            
            # Calculate the moving average value itself
            average_usage = get_average_usage(history_list)
            
            # Update the list in the env
            context.env["cpu_history"][key] = history_list
            
            # Update the list in the result dict
            _, cpu_number = key.split("-", 1)
            metric_name = f'avg-util-cpu{cpu_number}-60sec'
            result[metric_name] = average_usage
            logger.info(f"[INFO] Computed {metric_name}: {average_usage}")

    return result