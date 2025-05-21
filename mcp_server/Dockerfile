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

# Copy requirements files
COPY requirements.txt requirements-dev.txt ./

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

# Command for different environments
CMD if [ "$ENVIRONMENT" = "production" ]; then \
        uvicorn app.asgi:app --host 0.0.0.0 --port 8000 --workers ${WORKERS:-4} --no-access-log; \
    else \
        uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload; \
    fi
