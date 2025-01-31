import http.server
import socketserver
import webbrowser
import os

PORT = 8000

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        if self.path == '/':
            self.path = '/Start.html'
        return super().do_GET()

def run_server():
    handler_object = MyHttpRequestHandler

    with socketserver.TCPServer(("", PORT), handler_object) as httpd:
        print(f"Serving at port {PORT}")
        webbrowser.open(f'http://localhost:{PORT}/')
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
