FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Create startup script
COPY <<EOF /app/startup.sh
#!/bin/bash
set -e

echo "Starting Django Client startup tasks..."

# Run startup tasks (migrations, static files, OAuth registration)
python scripts/render_startup.py

# Start the server
echo "Starting Django server with Gunicorn..."
exec gunicorn django_client.wsgi:application --bind 0.0.0.0:\${PORT:-8000} --workers \${WORKERS:-1}
EOF

# Make startup script executable
RUN chmod +x /app/startup.sh

# Use startup script as the command
CMD ["/app/startup.sh"]
