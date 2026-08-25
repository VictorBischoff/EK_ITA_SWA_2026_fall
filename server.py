#!/usr/bin/env python3
"""
Simple HTTP server for the Software Architecture course frontend.

This server serves the static files (index.html, README.md files, etc.) 
so students can view the course materials in a web browser.

Usage:
    python server.py [port]
    
    Default port: 8000
    
    Then open: http://localhost:8000

Requirements:
    - Python 3.7+
    - No additional dependencies required
"""

import http.server
import socketserver
import argparse
import os
import sys
import json
import signal
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'scripts'))
from auto_update import update_from_upstream

# Custom request handler to serve index.html for root path
class CourseHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        # Handle API endpoint for updating from upstream
        if self.path == '/api/update':
            return self.handle_update()
        
        # If root path, serve index.html
        if self.path == '/' or self.path == '/index.html':
            self.path = '/index.html'
        
        # Try to serve the file normally
        try:
            # Check if file exists
            file_path = Path(self.translate_path(self.path))
            
            # For directory paths, try to find index.html
            if file_path.is_dir():
                index_path = file_path / 'index.html'
                if index_path.exists():
                    self.path = self.path.rstrip('/') + '/index.html'
                    return super().do_GET()
            
            # For markdown files, serve with correct content type
            if file_path.suffix == '.md':
                self.send_response(200)
                self.send_header('Content-type', 'text/markdown; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                with open(file_path, 'rb') as f:
                    self.wfile.write(f.read())
                return
            
            # For all other files, use default handler with CORS
            return super().do_GET()
            
        except FileNotFoundError:
            # Serve index.html for any 404 (SPA routing)
            if self.path.startswith('/'):
                self.path = '/index.html'
                return self.do_GET()
            else:
                self.send_error(404, f"File {self.path} not found")

    def translate_path(self, path):
        # Fix for paths with query strings or fragments
        path = path.split('?')[0].split('#')[0]
        return super().translate_path(path)
    
    def handle_update(self):
        """Handle the /api/update endpoint to pull latest changes from upstream.

        Restricted to localhost: the server is commonly bound to 0.0.0.0 so
        classmates on the same LAN can view the site, but a GET request that
        triggers a git merge should not be triggerable by anyone but the
        person running the server. Never pushes (fetch + merge only) - use
        scripts/auto_update.py --push for that, deliberately out-of-band.
        """
        client_ip = self.client_address[0]
        if client_ip not in ('127.0.0.1', '::1'):
            response = {'success': False, 'message': 'Forbidden: /api/update is only available from localhost.'}
            self.send_response(403)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(response, indent=2).encode('utf-8'))
            return

        result = update_from_upstream(repo_dir=Path(__file__).parent, push=False)
        response = {'success': result['success'], 'message': result['message']}
        self.send_response(200 if result['success'] else 500)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response, indent=2).encode('utf-8'))
    
    def end_headers(self):
        # Add CORS headers for all responses
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()


class GracefulTCPServer(socketserver.TCPServer):
    """TCPServer that shuts down cleanly on SIGINT/SIGTERM."""
    allow_reuse_address = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._shutdown_request = False

    def serve_forever(self, poll_interval=0.5):
        self._shutdown_request = False
        try:
            while not self._shutdown_request:
                self.handle_request()
        finally:
            self.server_close()

    def shutdown(self):
        self._shutdown_request = True
        # Send a dummy request to unblock the blocking handle_request() call
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.server_address[0], self.server_address[1]))
            s.close()
        except OSError:
            pass


def signal_handler(signum, frame):
    """Handle Ctrl+C / termination signals gracefully."""
    print(f"\n\nReceived signal {signum}, shutting down server...")
    sys.exit(0)


def run_server(port=8000, bind='0.0.0.0'):
    """Start the HTTP server."""
    Handler = CourseHandler

    # Register signal handlers for graceful shutdown before binding the socket
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal

    # Retry with backoff if the port is already in use, instead of failing immediately
    max_retries = 3
    retry_delay = 1
    httpd = None
    for attempt in range(max_retries):
        try:
            httpd = GracefulTCPServer((bind, port), Handler)
            break
        except OSError as e:
            if e.errno == 48 or e.errno == 98:  # Address already in use (macOS / Linux)
                if attempt < max_retries - 1:
                    print(f"Port {port} is in use, retrying in {retry_delay}s... ({attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                print(f"\nError: Port {port} is already in use by another process.")
                print(f"Try running: lsof -i :{port} to find and stop it, or use --port to pick another one.")
                sys.exit(1)
            else:
                raise

    print(f"\n{'='*60}")
    print(f"  Software Architecture Course Server")
    print(f"{'='*60}")
    print(f"  Course: ITA Software Architecture Fall 2026")
    print(f"  EK Business Academy Copenhagen")
    print(f"{'='*60}")
    print(f"  Server running at: http://localhost:{port}")
    print(f"  Local network:    http://{bind}:{port}")
    print(f"{'='*60}")
    print(f"  Press Ctrl+C to stop the server")
    print(f"{'='*60}\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\nServer stopped by user.")
    finally:
        httpd.server_close()
        print("Server socket closed.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Run a web server for the Software Architecture course frontend'
    )
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=8000,
        help='Port to serve on (default: 8000)'
    )
    parser.add_argument(
        '--bind', '-b',
        default='0.0.0.0',
        help='Address to bind to (default: 0.0.0.0)'
    )
    
    args = parser.parse_args()
    run_server(args.port, args.bind)
