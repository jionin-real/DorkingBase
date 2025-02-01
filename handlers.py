import os
import json
from http.server import SimpleHTTPRequestHandler
from http import HTTPStatus
from urllib.parse import urlparse, unquote
from utils import (
    validate_filename,
    read_json_file,
    write_json_file,
    get_dorks_path
)

class RequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.base_directory = kwargs.pop('directory', os.getcwd())
        super().__init__(*args, directory=self.base_directory, **kwargs)

    def do_GET(self):
        if self.path == '/':
            self.path = '/Start.html'
            return super().do_GET()
        
        if self.path == '/files':
            return self.handle_get_files()
        
        if self.path.startswith('/file/'):
            return self.handle_get_file()
        
        super().do_GET()

    def do_POST(self):
        if self.path.startswith('/file/'):
            return self.handle_post_file()
        self.send_error(HTTPStatus.NOT_FOUND, "Endpoint not found")

    def do_DELETE(self):
        if self.path.startswith('/file/'):
            self.handle_delete_file()
        elif self.path.startswith('/dork/'):
            self.handle_delete_dork()
        else:
            self.send_error(HTTPStatus.NOT_FOUND, "Endpoint not found")

    def do_PUT(self):
        if self.path.startswith('/dork/'):
            self.handle_update_dork()
        else:
            self.send_error(HTTPStatus.NOT_FOUND, "Endpoint not found")

    # API Handlers
    def handle_get_files(self):
        dorks_dir = get_dorks_path(self.base_directory)
        if not os.path.exists(dorks_dir):
            os.makedirs(dorks_dir, exist_ok=True)
        
        files = [f for f in os.listdir(dorks_dir) if f.endswith('.json')]
        self.send_json_response(files)

    def handle_get_file(self):
        filename = self._get_valid_filename()
        if not filename:
            return

        file_path = os.path.join(get_dorks_path(self.base_directory), filename)
        content = read_json_file(file_path)
        
        if content is None:
            self.send_error(HTTPStatus.NOT_FOUND, "File not found or invalid format")
            return
        
        self.send_json_response(content)

    def handle_post_file(self):
        filename = self._get_valid_filename()
        if not filename:
            return

        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data)
        except json.JSONDecodeError:
            self.send_error(HTTPStatus.BAD_REQUEST, "Invalid JSON")
            return

        dorks_dir = get_dorks_path(self.base_directory)
        os.makedirs(dorks_dir, exist_ok=True)
        file_path = os.path.join(dorks_dir, filename)

        existing_data = read_json_file(file_path) or []
        max_id = max((item.get('id', 0) for item in existing_data), default=0)

        if isinstance(data, dict):
            data['id'] = max_id + 1
            existing_data.append(data)
        elif isinstance(data, list):
            for item in data:
                max_id += 1
                item['id'] = max_id
            existing_data.extend(data)
        else:
            self.send_error(HTTPStatus.BAD_REQUEST, "Invalid data format")
            return

        write_json_file(file_path, existing_data)
        self.send_response_only(HTTPStatus.OK)
        self.end_headers()

    def handle_delete_file(self):
        filename = self._get_valid_filename()
        if not filename:
            return

        file_path = os.path.join(get_dorks_path(self.base_directory), filename)
        if not os.path.exists(file_path):
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return

        try:
            os.remove(file_path)
            self.send_response_only(HTTPStatus.OK)
            self.end_headers()
        except Exception as e:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(e))

    def handle_delete_dork(self):
        parts = self.path.split('/')
        if len(parts) != 4:
            self.send_error(HTTPStatus.BAD_REQUEST, "Invalid URL format")
            return

        filename = validate_filename(parts[2])
        dork_id = parts[3]
        file_path = os.path.join(get_dorks_path(self.base_directory), filename)

        data = read_json_file(file_path)
        if data is None:
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return

        new_data = [d for d in data if str(d.get('id')) != dork_id]
        
        if len(new_data) == len(data):
            self.send_error(HTTPStatus.NOT_FOUND, "Dork not found")
            return

        write_json_file(file_path, new_data)
        self.send_response_only(HTTPStatus.OK)
        self.end_headers()

    def handle_update_dork(self):
        parts = self.path.split('/')
        if len(parts) != 4:
            self.send_error(HTTPStatus.BAD_REQUEST, "Invalid URL format")
            return

        filename = validate_filename(parts[2])
        dork_id = parts[3]
        file_path = os.path.join(get_dorks_path(self.base_directory), filename)

        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            update_data = json.loads(post_data)
        except json.JSONDecodeError:
            self.send_error(HTTPStatus.BAD_REQUEST, "Invalid JSON")
            return

        data = read_json_file(file_path)
        if data is None:
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return

        updated = False
        for item in data:
            if str(item.get('id')) == dork_id:
                item.update({
                    'name': update_data.get('name', item['name']),
                    'dork': update_data.get('dork', item['dork'])
                })
                updated = True
                break

        if not updated:
            self.send_error(HTTPStatus.NOT_FOUND, "Dork not found")
            return

        write_json_file(file_path, data)
        self.send_response_only(HTTPStatus.OK)
        self.end_headers()

    # Helpers
    def _get_valid_filename(self):
        filename = os.path.basename(self.path.split('/file/')[-1])
        return validate_filename(filename)

    def send_json_response(self, data):
        self.send_response(HTTPStatus.OK)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())