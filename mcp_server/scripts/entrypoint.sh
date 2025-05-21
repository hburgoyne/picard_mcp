#!/bin/bash
set -e

# Wait for the main database to be ready
echo "Waiting for database to be ready..."
i=0
until PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT 1" > /dev/null 2>&1; do
  i=$((i+1))
  if [ "$i" -gt 10 ]; then
    echo "Database connection timed out"
    exit 1
  fi
  echo "Waiting for database connection..."
  sleep 2
done
echo "Database is ready!"

# Check if the test database exists, create it if it doesn't
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT 1 FROM pg_database WHERE datname='${POSTGRES_DB}_test'" | grep -q 1 || PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c "CREATE DATABASE ${POSTGRES_DB}_test"

# Create pgvector extension in both databases if they don't exist
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c "CREATE EXTENSION IF NOT EXISTS vector"
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -d "${POSTGRES_DB}_test" -c "CREATE EXTENSION IF NOT EXISTS vector"

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Execute the main container command
exec "$@"
