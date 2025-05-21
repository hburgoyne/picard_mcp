#!/bin/bash
# Run the Django client with Docker

# Go to the project root
cd "$(dirname "$0")/.."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Collect static files first
docker exec picard_mcp-django_client python manage.py collectstatic --noinput

# Display success message
echo "Django client running at http://localhost:8000"
echo "Login credentials:"
echo "- Username: admin"
echo "- Password: admin"
echo ""
echo "You can create a new user by visiting http://localhost:8000/register/"
