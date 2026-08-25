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
import subprocess
import json
import signal
from pathlib import Path

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
    
    def handle_update(self):
        """Handle the /api/update endpoint to pull from upstream."""
        repo_dir = Path(__file__).parent
        
        try:
            # Step 1: Get current branch
            current_branch = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=repo_dir,
                capture_output=True,
                text=True
            )
            
            # Step 2: Stash any local changes
            stash_result = subprocess.run(
                ['git', 'stash', 'push', '-m', 'Auto-stash before upstream update'],
                cwd=repo_dir,
                capture_output=True,
                text=True
            )
            stashed = stash_result.returncode == 0
            
            # Step 3: Fetch from upstream
            fetch_result = subprocess.run(
                ['git', 'fetch', 'upstream'],
                cwd=repo_dir,
                capture_output=True,
                text=True
            )
            
            if fetch_result.returncode != 0:
                response = {
                    'success': False,
                    'message': 'Failed to fetch from upstream',
                    'error': fetch_result.stderr or fetch_result.stdout,
                    'step': 'fetch'
                }
                self.send_response(500)
                self._send_json(response)
                return
            
            # Step 4: Checkout master if not already there
            if current_branch.stdout.strip() != 'master':
                checkout_result = subprocess.run(
                    ['git', 'checkout', 'master'],
                    cwd=repo_dir,
                    capture_output=True,
                    text=True
                )
                if checkout_result.returncode != 0:
                    response = {
                        'success': False,
                        'message': 'Failed to checkout master branch',
                        'error': checkout_result.stderr or checkout_result.stdout,
                        'step': 'checkout'
                    }
                    self.send_response(500)
                    self._send_json(response)
                    return
            
            # Step 5: Merge from upstream/master
            merge_result = subprocess.run(
                ['git', 'merge', 'upstream/master', '--no-edit', '-m', 'Auto-merge upstream changes'],
                cwd=repo_dir,
                capture_output=True,
                text=True
            )
            
            if merge_result.returncode != 0:
                response = {
                    'success': False,
                    'message': 'Failed to merge upstream changes',
                    'error': merge_result.stderr or merge_result.stdout,
                    'step': 'merge'
                }
                self.send_response(500)
                self._send_json(response)
                return
            
            # Step 6: Try to push to origin (may fail if no push permissions)
            push_result = subprocess.run(
                ['git', 'push', 'origin', 'master'],
                cwd=repo_dir,
                capture_output=True,
                text=True
            )
            
            # Reapply stashed changes
            if stashed:
                subprocess.run(
                    ['git', 'stash', 'pop'],
                    cwd=repo_dir,
                    capture_output=True,
                    text=True
                )
            
            # Return to original branch if not master
            if current_branch.stdout.strip() != 'master':
                subprocess.run(
                    ['git', 'checkout', current_branch.stdout.strip()],
                    cwd=repo_dir,
                    capture_output=True,
                    text=True
                )
            
            # Prepare successful response
            response = {
                'success': True,
                'message': 'Successfully updated from upstream',
                'fetch': fetch_result.stdout.strip(),
                'merge': merge_result.stdout.strip(),
                'push': push_result.stdout.strip() if push_result.returncode == 0 else 'Push failed (may need permissions)',
                'stashed': stashed
            }
            self.send_response(200)
            
        except Exception as e:
            response = {
                'success': False,
                'message': 'Internal server error',
                'error': str(e),
                'step': 'exception'
            }
            self.send_response(500)
        
        self._send_json(response)
    
    def _send_json(self, data):
        """Helper to send JSON response."""
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode('utf-8'))

    def translate_path(self, path):
        # Fix for paths with query strings or fragments
        path = path.split('?')[0].split('#')[0]
        return super().translate_path(path)
    
    def end_headers(self):
        # Add CORS headers for all responses
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()


class GracefulTCPServer(socketserver.TCPServer):
    """TCPServer that handles SIGTERM for graceful shutdown."""
    allow_reuse_address = True
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._shutdown_request = False
    
    def serve_forever(self, poll_interval=0.5):
        """Handle one request at a time until shutdown."""
        self._shutdown_request = False
        try:
            while not self._shutdown_request:
                self.handle_request()
        finally:
            self.server_close()
    
    def shutdown(self):
        """Stop the serve_forever loop."""
        self._shutdown_request = True
        # Send a dummy request to unblock the server
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.server_address[0], self.server_address[1]))
            s.close()
        except:
            pass


def signal_handler(signum, frame):
    """Handle termination signals gracefully."""
    print(f"\n\nReceived signal {signum}, shutting down server...")
    sys.exit(0)


def run_server(port=8000, bind='0.0.0.0'):
    """Start the HTTP server with graceful shutdown handling."""
    Handler = CourseHandler
    
    # Register signal handlers for graceful shutdown BEFORE creating the server
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
    
    # Try to create the server with retry for address-in-use errors
    import time
    max_retries = 3
    retry_delay = 1
    
    httpd = None
    for attempt in range(max_retries):
        try:
            httpd = GracefulTCPServer((bind, port), Handler)
            break
        except OSError as e:
            if e.errno == 48:  # Address already in use on macOS/Linux
                if attempt < max_retries - 1:
                    print(f"Port {port} is in use, retrying in {retry_delay} second(s)... ({attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                else:
                    print(f"\nError: Port {port} is already in use by another process.")
                    print(f"Try running: lsof -i :{port} to find and kill the process.")
                    sys.exit(1)
            else:
                raise
    
    if httpd is None:
        print("Failed to start server after retries.")
        sys.exit(1)
    
    try:
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
        
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\nServer stopped by user.")
    finally:
        httpd.server_close()
        print("Server socket closed.")
        sys.exit(0)


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
