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

    def translate_path(self, path):
        # Fix for paths with query strings or fragments
        path = path.split('?')[0].split('#')[0]
        return super().translate_path(path)
    
    def handle_update(self):
        """Handle the /api/update endpoint to pull latest changes."""
        repo_dir = Path(__file__).parent
        
        try:
            # Get current branch
            current_branch = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=repo_dir,
                capture_output=True,
                text=True
            )
            
            if current_branch.returncode != 0:
                raise Exception(f"Not in a git repository")
            
            current_branch_name = current_branch.stdout.strip()
            
            # Check if upstream remote exists
            remotes = subprocess.run(
                ['git', 'remote'],
                cwd=repo_dir,
                capture_output=True,
                text=True
            )
            
            upstream_exists = remotes.returncode == 0 and 'upstream' in remotes.stdout
            
            if upstream_exists:
                # Fetch from upstream
                fetch_result = subprocess.run(
                    ['git', 'fetch', 'upstream'],
                    cwd=repo_dir,
                    capture_output=True,
                    text=True
                )
                
                if fetch_result.returncode != 0:
                    raise Exception(f"Failed to fetch from upstream: {fetch_result.stderr.strip()}")
                
                # Checkout master if not already there
                if current_branch_name != 'master':
                    checkout_result = subprocess.run(
                        ['git', 'checkout', 'master'],
                        cwd=repo_dir,
                        capture_output=True,
                        text=True
                    )
                    if checkout_result.returncode != 0:
                        raise Exception(f"Failed to checkout master: {checkout_result.stderr.strip()}")
                
                # Merge from upstream/master
                merge_result = subprocess.run(
                    ['git', 'merge', 'upstream/master', '--no-edit'],
                    cwd=repo_dir,
                    capture_output=True,
                    text=True
                )
                
                if merge_result.returncode != 0:
                    raise Exception(f"Failed to merge upstream/master: {merge_result.stderr.strip()}")
                
                message = 'Successfully updated from upstream'
            else:
                # No upstream configured - cannot update from source repo
                # Just return a message
                message = 'No upstream remote configured. To set it up, run: git remote add upstream <original-repo-url>'
                raise Exception(message)
            
            response = {
                'success': True,
                'message': message,
                'upstream': upstream_exists
            }
            self.send_response(200)
            
        except Exception as e:
            response = {
                'success': False,
                'message': str(e)
            }
            self.send_response(500)
        
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


def run_server(port=8000, bind='0.0.0.0'):
    """Start the HTTP server."""
    Handler = CourseHandler
    
    with socketserver.TCPServer((bind, port), Handler) as httpd:
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
            print("\n\nServer stopped.")
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
