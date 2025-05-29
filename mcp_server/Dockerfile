FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LOG_LEVEL=info

# Create a non-root user
RUN addgroup --system app && adduser --system --group app

# Create logs directory with appropriate permissions
RUN mkdir -p /app/logs && chown -R app:app /app/logs

# Copy requirements file
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Change ownership of the application code
RUN chown -R app:app /app

# Switch to non-root user for security
USER app

# Expose port
EXPOSE 8000

# Create startup script
COPY <<EOF /app/startup.sh
#!/bin/bash
set -e

echo "Starting MCP Server startup tasks..."

# Run startup tasks (database setup, migrations, admin user creation)
python scripts/startup_tasks.py

# Start the server
if [ "\$ENVIRONMENT" = "production" ]; then
    echo "Starting production server..."
    exec uvicorn app.main:app --host 0.0.0.0 --port \${PORT:-8000} --workers \${WORKERS:-1}
else
    echo "Starting development server..."
    exec uvicorn app.main:app --host 0.0.0.0 --port \${PORT:-8000} --reload
fi
EOF

# Make startup script executable
RUN chmod +x /app/startup.sh

# Use startup script as the command
CMD ["/app/startup.sh"]
