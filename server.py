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
        try:
            # Run the update script
            repo_dir = Path(__file__).parent
            update_script = repo_dir / 'scripts' / 'auto_update.py'
            
            if update_script.exists():
                # Run the update script
                result = subprocess.run(
                    [sys.executable, str(update_script)],
                    cwd=repo_dir,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    response = {
                        'success': True,
                        'message': 'Successfully updated from upstream',
                        'output': result.stdout
                    }
                    self.send_response(200)
                else:
                    response = {
                        'success': False,
                        'message': 'Failed to update from upstream',
                        'error': result.stderr or result.stdout
                    }
                    self.send_response(500)
            else:
                # Fallback: run git commands directly
                result = subprocess.run(
                    ['git', 'fetch', 'upstream'],
                    cwd=repo_dir,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    # Try to merge
                    merge_result = subprocess.run(
                        ['git', 'merge', 'upstream/master', '--no-edit', '-m', 'Auto-merge upstream'],
                        cwd=repo_dir,
                        capture_output=True,
                        text=True
                    )
                    
                    if merge_result.returncode == 0:
                        push_result = subprocess.run(
                            ['git', 'push', 'origin', 'master'],
                            cwd=repo_dir,
                            capture_output=True,
                            text=True
                        )
                        
                        if push_result.returncode == 0:
                            response = {
                                'success': True,
                                'message': 'Successfully updated from upstream',
                                'fetch': result.stdout,
                                'merge': merge_result.stdout,
                                'push': push_result.stdout
                            }
                            self.send_response(200)
                        else:
                            response = {
                                'success': False,
                                'message': 'Failed to push to origin',
                                'error': push_result.stderr or push_result.stdout
                            }
                            self.send_response(500)
                    else:
                        response = {
                            'success': False,
                            'message': 'Failed to merge upstream changes',
                            'error': merge_result.stderr or merge_result.stdout
                        }
                        self.send_response(500)
                else:
                    response = {
                        'success': False,
                        'message': 'Failed to fetch from upstream',
                        'error': result.stderr or result.stdout
                    }
                    self.send_response(500)
            
            # Send JSON response
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response, indent=2).encode('utf-8'))
            
        except Exception as e:
            response = {
                'success': False,
                'message': 'Internal server error',
                'error': str(e)
            }
            self.send_response(500)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response, indent=2).encode('utf-8'))

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
