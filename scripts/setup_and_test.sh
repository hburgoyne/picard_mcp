#!/bin/bash
set -e

echo "=== Stopping any existing containers ==="
docker-compose down

echo "=== Rebuilding containers with the latest changes ==="
docker-compose build

echo "=== Starting containers ==="
docker-compose up -d

echo "=== Waiting for database to be ready ==="
sleep 15

echo "=== Creating .env file if it doesn't exist ==="
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env file from .env.example"
fi

echo "=== Creating database if it doesn't exist ==="
docker-compose exec db psql -U postgres -c "CREATE DATABASE picard_mcp;" || echo "Database already exists"

echo "=== Enabling pgvector extension ==="
docker-compose exec db psql -U postgres -d picard_mcp -c "CREATE EXTENSION IF NOT EXISTS vector;"

echo "=== Running database migrations ==="
docker-compose exec app bash -c "cd /app && alembic upgrade head"

echo "=== Initializing database with test data ==="
docker-compose exec app bash -c "cd /app && python scripts/init_db.py"

echo "=== Running tests ==="
docker-compose exec app bash -c "cd /app && python scripts/test_mcp.py"

echo "=== Setup and testing complete ==="
echo "The MCP server is running at http://localhost:8000"
echo "You can check the logs with: docker-compose logs -f app"
