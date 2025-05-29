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

# Create startup script
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "Starting Django Client startup tasks..."\n\
\n\
# Run startup tasks (migrations, static files, OAuth registration)\n\
python scripts/render_startup.py\n\
\n\
# Start the server\n\
echo "Starting Django server with Gunicorn..."\n\
exec gunicorn django_client.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers ${WORKERS:-1}' > /app/startup.sh && chmod +x /app/startup.sh

# Expose port
EXPOSE 8000

# Use startup script as the command
CMD ["/app/startup.sh"]
