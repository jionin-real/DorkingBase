import argparse
import socket
import os
import webbrowser
from socketserver import TCPServer
from config import DEFAULT_HOST, DEFAULT_PORT, DEFAULT_DIRECTORY, START_FILE
from handlers import RequestHandler

def run_server(host, port, directory):
    handler = lambda *args, **kwargs: RequestHandler(*args, directory=directory, **kwargs)
    
    try:
        with TCPServer((host, port), handler) as httpd:
            print(f"Serving {directory} at http://{host}:{port}")
            webbrowser.open(f'http://{host}:{port}/')
            httpd.serve_forever()
            
    except PermissionError:
        print(f"Error: Port {port} requires elevated permissions")
    except socket.error as e:
        print(f"Server error: {e}")
    except KeyboardInterrupt:
        print("\nServer is shutting down gracefully...")

def check_start_file(directory):
    if not os.path.exists(os.path.join(directory, START_FILE)):
        print(f"Warning: {START_FILE} not found in {directory}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple HTTP Server")
    parser.add_argument('-p', '--port', type=int, default=DEFAULT_PORT, help="Port to serve on")
    parser.add_argument('--host', type=str, default=DEFAULT_HOST, help="Host to serve on")
    
    args = parser.parse_args()
    check_start_file(DEFAULT_DIRECTORY)  
    run_server(args.host, args.port, DEFAULT_DIRECTORY)  