# Picard MCP Server

This is the FastAPI implementation of the Model Context Protocol (MCP) server for the Picard MCP project. It provides secure memory storage and retrieval services with vector embeddings for semantic search.

## Features

- OAuth 2.0 authentication and authorization
- Memory storage with vector embeddings
- Permission-based memory access control
- LLM integration for memory-based queries

## Setup

### Prerequisites

- Python 3.10+
- PostgreSQL with pgvector extension
- OpenAI API key

### Installation

1. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables by copying the `.env.example` file to `.env` and filling in the required values.

4. Initialize the database:
   ```
   alembic upgrade head
   ```

5. Run the server:
   ```
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## Docker Setup

The application is configured to run with Docker Compose:

```bash
docker-compose up -d
```

This will start the following services:
- `db-mcp`: PostgreSQL database with pgvector extension
- `mcp_server`: FastAPI server running on port 8001

## API Documentation

Once the server is running, you can access the API documentation at:

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`

## MCP Compliance

This implementation follows the Model Context Protocol standard, which allows LLM applications to interact with the server in a standardized way. The MCP server exposes:

- **Resources**: Read-only endpoints that provide data to LLMs (memory content)
- **Tools**: Functional endpoints that perform actions (memory creation, updates, queries)
- **Authentication**: OAuth 2.0 implementation for secure access to protected resources
