import datetime

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