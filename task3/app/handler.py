import importlib
import os
import tempfile
import zipfile
import requests
import sys

from logs import logger
from local_env import ZIPFILE_URL, FUNCTION_HANDLER

def download_and_extract_zip(zip_url):
    try:
        response = requests.get(zip_url, stream=True)
        response.raise_for_status()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_zip:
            temp_zip.write(response.content)
            temp_zip_path = temp_zip.name
        extracted_dir = tempfile.mkdtemp()
        with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
            zip_ref.extractall(extracted_dir)
        os.unlink(temp_zip_path)
        logger.error(f"[ERROR] Extracted dir found: {extracted_dir}")
        return extracted_dir
    except Exception as e:
        logger.error(f"[ERROR] Failed to download or extract ZIP file: {e}")
        return None

def dynamic_import_from_dir(directory, handler_name):
    try:
        sys.path.insert(0, directory)
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".py") and not file.startswith("__init__"):
                    module_name = file[:-3]
                    module = importlib.import_module(module_name)
                    if hasattr(module, handler_name):
                        return getattr(module, handler_name)
    except Exception as e:
        logger.error(f"[ERROR] Failed to dynamically import handler: {e}")
    finally:
        if directory in sys.path:
            sys.path.remove(directory)
    return None

def get_handler():
    handler = None

    if ZIPFILE_URL:
        logger.warning("[INFO] Trying to get the handler from the .zip file")
        extracted_dir = download_and_extract_zip(ZIPFILE_URL)
        if extracted_dir:
            handler = dynamic_import_from_dir(extracted_dir, FUNCTION_HANDLER)
            return handler
                
    if not handler:
        logger.warning("[INFO] Falling back to usermodule.py")
        usermodule_spec = importlib.util.find_spec('usermodule')
        if usermodule_spec:
            usermodule = importlib.util.module_from_spec(usermodule_spec)
            usermodule_spec.loader.exec_module(usermodule)
            handler = getattr(usermodule, FUNCTION_HANDLER, None)
            return handler
    
    return None

def execute_handler(handler, data, context):
    try:
        return handler(data, context)
    except Exception as e:
        logger.error(f"[ERROR] Error in user-defined handler: {e}")
        return None
