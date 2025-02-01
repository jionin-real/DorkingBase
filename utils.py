import os
import json
from http import HTTPStatus
from config import DORKS_DIR

def get_dorks_path(base_dir):
    
    return os.path.join(base_dir, DORKS_DIR)

def validate_filename(filename):

    if not filename.endswith('.json'):
        return None
    if '..' in filename or '/' in filename or '\\' in filename:
        return None
    return filename

def read_json_file(path):

    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def write_json_file(path, data):

    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error writing file: {e}")
        return False