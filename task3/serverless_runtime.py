import os
import json
import redis
import datetime
import time

# Context class definition
class Context:
    def __init__(self, host, port, input_key, output_key):
        self.host = host
        self.port = port
        self.input_key = input_key
        self.output_key = output_key
        self.function_getmtime = datetime.datetime.now().isoformat() 
        self.last_execution = None
        self.env = {}

REDIS_HOST = os.getenv("REDIS_HOST", "192.168.121.187")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_INPUT_KEY = os.getenv("REDIS_INPUT_KEY", "metrics")
REDIS_OUTPUT_KEY = os.getenv("REDIS_OUTPUT_KEY", "jeanevangelista-proj3-output")
MONITORING_PERIOD = int(os.getenv("MONITORING_PERIOD", "5"))

# Initialize redis object
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# Initialize the context object
context = Context(
    host=REDIS_HOST,
    port=REDIS_PORT,
    input_key=REDIS_INPUT_KEY,
    output_key=REDIS_OUTPUT_KEY,
)

# Function to update context timestamps
def update_context(context, function_path):
    context.last_execution = datetime.datetime.now().isoformat()
    try:
        context.function_getmtime = datetime.datetime.fromtimestamp(
            os.path.getmtime(function_path)
        ).isoformat()
    except FileNotFoundError:
        context.function_getmtime = "Unknown"

# Function to call the user's handler
def call_handler():
    # Fetch data from Redis
    data_json = r.get(context.input_key)
    
    # Exit no data was found
    if not data_json:
        print(f"No data found in Redis for key: {context.input_key}.")
        return

    # Parse the data
    input_data = json.loads(data_json)

    # Try to import the user's module
    try:
        import usermodule
        handler = usermodule.handler
    except ImportError as error:
        print(f"Error importing usermodule: {error}")
        return

    # Try to call the handler function
    try:
        result = handler(input_data, context)
        
        # Check if the handlr is returning a valid dict
        if not isinstance(result, dict):
            print("Handler did not return a valid dictionary.")
            return
        
        # Stores in Redis
        r.set(context.output_key, json.dumps(result))
        print(f"Stored result in Redis at key: {context.output_key}")

    except Exception as e:
        print(f"Error while executing handler: {e}")

    # Update the context after execution
    update_context(context, "/app/usermodule.py")

# Main runtime loop
if __name__ == "__main__":
    print("Starting serverless runtime...")
    while True:
        call_handler()
        time.sleep(MONITORING_PERIOD)
