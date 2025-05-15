# MCP Server

A Django-based implementation of the Model Context Protocol (MCP) for managing political preferences and visions for the future.

## Features

- User authentication with JWT
- Agent-based architecture
- Context blocks for storing political preferences and beliefs
- Fine-grained permission system
- Vector embeddings for semantic search

## Prerequisites

- Docker and Docker Compose
- Python 3.9+

## Getting Started

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd mcp-server
   ```

2. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

3. Update the `.env` file with your configuration.

4. Build and start the services:
   ```bash
   docker-compose up -d --build
   ```

5. Run database migrations:
   ```bash
   docker-compose exec web python manage.py migrate
   ```

6. Create a superuser:
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

7. Access the admin interface at `http://localhost:8000/admin/`

## Project Structure

- `mcp_server/` - Main Django project settings
- `users/` - User authentication and management
- `agents/` - MCP agent definitions
- `memories/` - Context blocks and memory management
- `permissions/` - Fine-grained access control
- `embeddings/` - Vector embeddings and search

## API Documentation

API documentation is available at `/swagger/` and `/redoc/` when running in development mode.

## Testing

Run tests with:

```bash
docker-compose exec web pytest
```

## License

MIT
