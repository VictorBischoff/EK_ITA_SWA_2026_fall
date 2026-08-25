# Running the Course Frontend

This document explains how to run the Software Architecture course frontend on your local machine.

> **Just want to read the course material?** The frontend is static after the
> initial load, so a static host (GitHub Pages, Netlify, Vercel — see
> [Production Deployment](#production-deployment)) plus a plain `git pull` to
> update is simpler than running `server.py` and has no server-side attack
> surface at all. The custom server here mainly exists for the in-browser
> "Update" button (`/api/update`), which runs `git merge` on your machine —
> only worth it if you want that convenience.

## Quick Start

### Option 1: Python Server (Recommended)

The simplest way to run the frontend. Requires Python 3.7+.

```bash
# Start the server
python server.py

# Or specify a different port
python server.py --port 8080
```

Then open: **http://localhost:8000**

#### Stop the server
Press `Ctrl+C` in the terminal.

---

### Option 2: Docker

If you have Docker installed (covered in Session 5).

```bash
# Build the image
docker build -t ek-ita-swa-frontend .

# Run the container
docker run -p 8000:8000 ek-ita-swa-frontend
```

Then open: **http://localhost:8000**

---

### Option 3: Docker Compose (Recommended for Docker)

```bash
# Start the service
docker-compose up -d

# View the website
echo "http://localhost:8000"

# View logs
docker-compose logs -f

# Stop the service
docker-compose down
```

---

## Server Features

- **SPA Routing**: Any path that doesn't match a file will serve `index.html` (for client-side routing)
- **Markdown Support**: `.md` files are served with correct content-type
- **Automatic index.html**: Directory requests automatically serve index.html
- **Live Reload**: When using Docker Compose with volume mount, content updates are reflected immediately
- **Update button** (`/api/update`): fetches and merges from the configured `upstream` remote (see `scripts/README.md`). Restricted to requests from `localhost` — even if you bind the server to `0.0.0.0` so classmates on your LAN can view the site, they cannot trigger a merge on your machine through the button. It never pushes.

## Command Line Options

The Python server accepts these arguments:

```bash
# Show help
python server.py --help

# Run on a different port
python server.py --port 3000

# Bind to localhost only (no external access)
python server.py --bind 127.0.0.1

# Run on port 8080, accessible from network
python server.py --port 8080 --bind 0.0.0.0
```

## Accessing from Other Devices

To access the server from other devices on your network:

1. Find your local IP address:
   - **macOS/Linux**: `ifconfig | grep "inet "` (look for non-127.0.0.1 addresses)
   - **Windows**: `ipconfig` (look for IPv4 Address)

2. Run the server with network access:
   ```bash
   python server.py --bind 0.0.0.0 --port 8000
   ```

3. On another device, open: `http://<your-ip>:8000`

## Troubleshooting

### Port already in use

If you get an error that port 8000 is already in use:

```bash
# Find which process is using the port (macOS/Linux)
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
python server.py --port 8001
```

### Module not found errors

The server uses only Python's built-in modules, so no installation should be needed. If you get errors:

```bash
# Verify Python version
python --version
# Should be Python 3.7 or higher

# Try with python3 explicitly
python3 server.py
```

### Docker permission issues

On Linux, you might need to add your user to the docker group:

```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Then log out and back in, or restart
newgrp docker
```

## Production Deployment

For deploying to a real web server, you have several options:

### 1. Static File Hosting

Since the frontend is static (after the initial load), you can deploy it to any static hosting:

- GitHub Pages
- Netlify
- Vercel
- AWS S3 + CloudFront
- Any web server (Nginx, Apache)

### 2. Nginx Configuration

```nginx
server {
    listen 80;
    server_name architecture.your-school.dk;
    
    root /path/to/EK_ITA_SWA_2026_fall;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

### 3. Using a Process Manager

For long-running server processes:

```bash
# Install pm2 globally
npm install -g pm2

# Start the server
pm2 start server.py --name "course-frontend" -- --port 8000

# Make it start on boot
pm2 startup
pm2 save
```

## Files Created

| File | Purpose |
|------|---------|
| `index.html` | Main frontend application |
| `server.py` | Python HTTP server |
| `Dockerfile` | Container image definition |
| `docker-compose.yml` | Docker Compose configuration |
| `README_SERVER.md` | This documentation |

---

## Course Navigation Tips

Once the server is running, you can:

1. **Home Page**: http://localhost:8000 - Course overview and statistics
2. **Curriculum**: http://localhost:8000/#curriculum - Full course curriculum
3. **Sessions**: http://localhost:8000/#session-1 - Direct link to Session 1

All navigation is client-side, so page loads are instant after the initial load.
