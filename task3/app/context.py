import os

from datetime import datetime
from logs import logger

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
