# Dockerfile for running the Software Architecture course frontend
# 
# This provides a simple way to run the course website in a container.
# 
# Build: docker build -t ek-ita-swa-frontend .
# Run:   docker run -p 8000:8000 ek-ita-swa-frontend
# 
# Or use docker-compose for easier management.

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy all files from the repository
COPY . .

# Create a non-root user for security
RUN useradd -m courseuser && \
    chown -R courseuser:courseuser /app

# Switch to non-root user
USER courseuser

# Expose port 8000
EXPOSE 8000

# Start the server
CMD ["python", "server.py", "--port", "8000", "--bind", "0.0.0.0"]
