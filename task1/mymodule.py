import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Function to calculate the measurement datetime
def get_measurement_datetime(input: dict) ->  datetime.datetime:
    # Get the value present on the 'timestamp' key, fallback to an empty string if not present
    timestamp_string = input.get('timestamp', '')
    
    # If we don't receive a timestamp, just return the current datetime
    if (not timestamp_string):
        return datetime.datetime.now()
    
    # Remove 'Z' to avoid issues
    timestamp_string = timestamp_string.replace('Z', '')
    
    # If a timestamp is present, convert the timestamp to a valid datetime and return    
    # TODO: validate if need to do any extra verification here
    return datetime.datetime.fromisoformat(timestamp_string)

# Function to return the updated CPU history list
def get_updated_history_list(context: object, key: str, cutoff_datetime: datetime) -> list:
    # Make sure that there is something inside context.env
    if "cpu_history" not in context.env:
        context.env["cpu_history"] = {}
    
    # Get the CPU usage history list from env
    cpu_history = context.env["cpu_history"]
    
    # If there is nothing in the env, we can just return an empty list
    if (not cpu_history.get(key)):
        return []
    
    # Instantiate an empty list
    history_list = []
    
    # If there is something in the env, we need to keep only the updated values in the list
    for (measurement_datetime, value) in cpu_history.get(key):
        if (measurement_datetime >= cutoff_datetime):
            history_list.append((measurement_datetime, value))
    
    return history_list

# Function to calculate the CPU average usage value
def get_average_usage(history_list) -> float:
    if not history_list:
        return 0.0
    
    sum_usage = 0.0
    for (_, value) in history_list:
        sum_usage += value
    return sum_usage / len(history_list)
    

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
            
def handler(input: dict, context: object) -> dict[str, float]:
    logger.info(f"[INFO] Handler function called with the following input: {input}")
    result = {
        'percent-network-egress': get_percentage_of_outgoing_network_traffic(input),
        'percent-memory-cache': get_percentage_of_memory_caching_content(input),
        **get_moving_average(input, context)
    }
    logger.info(f"[INFO] Handler function result: {result}")
    return result