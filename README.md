# Picard MCP Server

A Model Context Protocol (MCP) server that provides memory storage and retrieval for authenticated users, with the ability to query an LLM using personas based on public memories.

## Overview

This is a Model Context Protocol (MCP) server that provides memory storage and retrieval for authenticated users. It uses FastAPI, PostgreSQL with pgvector for vector storage, and OAuth 2.0 for authentication.

## Architecture

### OAuth 2.0 Integration

The MCP server implements OAuth 2.0 Authorization Code flow to authenticate users. The flow works as follows:

1. A client application (e.g., Django backend) initiates the OAuth flow by redirecting the user to the MCP server's `/auth/authorize` endpoint
2. The MCP server authenticates the user and redirects back to the client's callback URL with an authorization code
3. The client exchanges the code for an access token by making a POST request to the MCP server's `/auth/token` endpoint
4. The client uses the access token to make authenticated requests to the MCP server's memory endpoints

### Memory Storage and Retrieval

The MCP server provides endpoints for:

- Submitting memories
- Retrieving memories
- Modifying memory permissions
- Querying users based on their memories

## Features

- OAuth 2.0 Authentication (Authorization Code flow)
- Memory storage and retrieval
- Memory permission management (public/private)
- Vector embedding of memories for semantic search
- LLM integration for querying user personas

## Setup

### Prerequisites

- Docker and Docker Compose
- Python 3.10+

### Configuration

1. Create a `.env` file based on the `.env.example` template:

```
# PostgreSQL Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=picard_mcp
POSTGRES_HOST=db
POSTGRES_PORT=5433  # Updated port

# MCP Server Configuration
MCP_SERVER_NAME=Picard MCP
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8001  # Updated port
MCP_ISSUER_URL=http://localhost:8001  # Updated port

# OAuth Configuration
OAUTH_CLIENT_ID=picard_client
OAUTH_CLIENT_SECRET=picard_secret
OAUTH_REDIRECT_URI=http://localhost:8000/oauth/callback  # Django backend callback URL

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
```

2. Run the setup script to build and start the containers, create the database, and initialize test data:

```bash
./scripts/setup_and_test.sh
```

## Testing

### Testing with Django Backend

The MCP server is designed to work with a Django backend that handles the OAuth flow. To test this integration:

1. Ensure your Django application is running at http://localhost:8000
2. Implement the OAuth client flow in your Django application:
   - Redirect users to `http://localhost:8001/auth/authorize` with appropriate parameters
   - Handle the callback at `http://localhost:8000/oauth/callback`
   - Exchange the authorization code for an access token
   - Use the access token to make authenticated requests to the MCP server

### Direct API Testing

If you already have an access token (obtained through your Django app), you can test the MCP endpoints directly using the included test client:

1. Open `test_client.html` in your browser
2. Enter your access token in the "Access Token" field
3. Test the memory endpoints:
   - Submit a new memory
   - Retrieve all memories
   - Modify memory permissions
   - Query a user with a prompt based on public memories

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.10+

### Local Development

1. Clone the repository
2. Copy `.env.example` to `.env` and fill in the required values
3. Run `docker-compose up`
4. Access the MCP server at http://localhost:8000

## Deployment

This project includes a `render.yaml` blueprint for deploying to Render.

## License

MIT