import importlib
import os
import tempfile
import zipfile
import requests

from logs import logger
from local_env import ZIPFILE_URL, FUNCTION_HANDLER
from logs import logger

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
        return extracted_dir
    except Exception as e:
        logger.error(f"[ERROR] Failed to download or extract ZIP file: {e}")
        return None

def combine_python_files(directory):
    try:
        combined_code = ""
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".py"):
                    with open(os.path.join(root, file), 'r') as f:
                        combined_code += f.read() + "\n"
        return combined_code
    except Exception as e:
        logger.error(f"[ERROR] Failed to combine Python files: {e}")
        return None

def load_combined_script(combined_code, handler_name):
    try:
        temp_script = tempfile.NamedTemporaryFile(delete=False, suffix=".py")
        temp_script.write(combined_code.encode())
        temp_script.close()
        module_spec = importlib.util.spec_from_file_location("combined_module", temp_script.name)
        combined_module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(combined_module)
        os.unlink(temp_script.name)
        return getattr(combined_module, handler_name)
    except Exception as e:
        logger.error(f"[ERROR] Failed to load combined script or handler: {e}")
        return None

def get_handler():
    handler = None

    if ZIPFILE_URL:
        logger.warning("[INFO] Trying to get the handler from the .zip file")
        extracted_dir = download_and_extract_zip(ZIPFILE_URL)
        if extracted_dir:
            combined_code = combine_python_files(extracted_dir)
            if combined_code:
                handler = load_combined_script(combined_code, FUNCTION_HANDLER)
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
