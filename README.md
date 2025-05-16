# Picard MCP Server

A Model Context Protocol (MCP) server that provides memory storage and retrieval for authenticated users, with the ability to query an LLM using personas based on public memories.

## Overview

This is a Model Context Protocol (MCP) server that provides memory storage and retrieval for authenticated users. It uses FastAPI, PostgreSQL with pgvector for vector storage, and OAuth 2.0 for authentication. The repository includes both the MCP server and a Django client application that demonstrates how to integrate with the MCP server.

## Architecture

### OAuth 2.0 Implementation Details

The OAuth 2.0 implementation uses the Authorization Code flow with PKCE (Proof Key for Code Exchange) for enhanced security. The flow works as follows:

1. **Client Registration**:
   - The Django client registers with the MCP server using the OAuth client registration endpoint
   - The registration includes:
     - Client ID: `picard_client`
     - Client Secret: `picard_secret`
     - Redirect URI: `http://localhost:8000/oauth/callback`
     - Scopes: `memories:read memories:write memories:admin`

2. **Authorization Flow**:
   - The client initiates authorization by redirecting to `/oauth/authorize` with parameters:
     - `response_type=code`
     - `client_id=picard_client`
     - `redirect_uri=http://localhost:8000/oauth/callback`
     - `scope=memories:read memories:write`
     - `state` (a random UUID for CSRF protection)
     - `code_challenge` and `code_challenge_method=S256` (PKCE parameters)

3. **Token Exchange**:
   - After authorization, the client exchanges the authorization code for tokens at `/oauth/token`
   - The request includes:
     - `grant_type=authorization_code`
     - `code` (the authorization code)
     - `redirect_uri`
     - `client_id`
     - `client_secret`
     - `code_verifier` (matches the code_challenge from authorization)

### Memory Storage and Retrieval

The MCP server provides endpoints for:
- Submitting memories
- Retrieving memories
- Modifying memory permissions
- Querying users based on their memories

## Current Implementation Status

### Working Features

- OAuth client registration with MCP server
- PKCE support for enhanced security
- Memory storage and retrieval endpoints
- Vector embedding of memories for semantic search
- User authentication and authorization

### Known Issues and Debugging Status

1. **Scope Validation Issue**
   - The OAuth flow is failing with an "invalid_scope" error despite the client being registered with the correct scopes
   - Error message: `error=invalid_scope&error_description=Client+was+not+registered+with+scope+memories%3Aread`
   - Debugging shows:
     - Client is registered with scopes: `['memories:read', 'memories:write', 'memories:admin']`
     - Requested scopes: `memories:read memories:write`
   - Current debugging attempts:
     - Added detailed logging to track scope validation
     - Modified scope validation logic to be more lenient
     - Verified database client registration

2. **Debugging Steps Taken**
   - Added extensive logging to the authorization flow
   - Verified client registration in the database
   - Modified scope validation logic
   - Added error handling and logging

3. **Next Debugging Steps**
   - Investigate how scopes are being passed through the OAuth flow
   - Verify scope parsing and comparison logic
   - Add more detailed logging at each step of the authorization process

## Features

- OAuth 2.0 Authentication (Authorization Code flow with PKCE)
- Memory storage and retrieval
- Memory permission management (public/private)
- Vector embedding of memories for semantic search
- LLM integration for querying user personas
- Django client application for OAuth integration

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
- Django client application for OAuth integration

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

The repository includes a Django client application that demonstrates the OAuth flow with the MCP server. To use it:

1. The Django application will run at http://localhost:8000 when using docker-compose
2. The Django app implements the complete OAuth client flow:
   - User registration and login
   - OAuth authorization with the MCP server
   - Token exchange and management
   - Memory creation, retrieval, and querying

See the [Django Client README](django_client/README.md) for more details on the Django application.

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
4. Access the MCP server at http://localhost:8001
5. Access the Django client at http://localhost:8000

## Deployment

This project includes a `render.yaml` blueprint for deploying to Render.

## License

MIT