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

# Create startup script before switching to non-root user
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "Starting MCP Server startup tasks..."\n\
\n\
# Run startup tasks (database setup, migrations, admin user creation)\n\
python scripts/startup_tasks.py\n\
\n\
# Start the server\n\
if [ "$ENVIRONMENT" = "production" ]; then\n\
    echo "Starting production server..."\n\
    exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WORKERS:-1}\n\
else\n\
    echo "Starting development server..."\n\
    exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --reload\n\
fi' > /app/startup.sh && chmod +x /app/startup.sh

# Change ownership of the application code and startup script
RUN chown -R app:app /app

# Switch to non-root user for security
USER app

# Expose port
EXPOSE 8000

# Use startup script as the command
CMD ["/app/startup.sh"]
