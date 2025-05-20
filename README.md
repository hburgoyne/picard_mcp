# Picard MCP Server

## Overview

Picard MCP is a complete memory management system built on the [Model Context Protocol (MCP)](https://modelcontextprotocol.io) standard. It consists of two main components: an MCP server that provides secure memory storage and retrieval services, and a Django client application that demonstrates how to integrate with the MCP server. The system enables users to store, retrieve, and manage their memories while controlling access permissions, and allows for semantic search and AI-powered queries based on stored memories.

### MCP Compliance

This implementation follows the Model Context Protocol standard, which allows LLM applications to interact with the server in a standardized way. The MCP server exposes:

- **Resources**: Read-only endpoints that provide data to LLMs (memory content)
- **Tools**: Functional endpoints that perform actions (memory creation, updates, queries)
- **Authentication**: OAuth 2.0 implementation for secure access to protected resources

### Key Components

1. **MCP Server**: A FastAPI-based implementation of the Model Context Protocol that provides:
   - OAuth 2.0 authentication and authorization
   - Memory storage with vector embeddings
   - Permission-based memory access control
   - LLM integration for memory-based queries

2. **Django Client**: A web application that demonstrates integration with the MCP server:
   - User registration and authentication
   - OAuth 2.0 client implementation
   - Memory creation, retrieval, and management UI
   - Persona-based querying interface

## System Architecture

### Overall Architecture

The Picard MCP system follows a client-server architecture with the following components:

1. **MCP Server**: Core backend service that handles memory storage, retrieval, and AI operations
   - Built with FastAPI (FastMCP) for high performance and async support
   - Uses PostgreSQL with pgvector extension for vector storage and semantic search
   - Implements OAuth 2.0 for secure authentication and authorization
   - Integrates with OpenAI API for memory embeddings (text-embedding-3-small)
   - Uses LangChain for LLM operations when available
   - Provides both stateful and stateless operation modes
   - Supports streamable HTTP transport for better scalability

2. **Django Client**: Web application that demonstrates integration with the MCP server
   - Provides user registration, authentication, and profile management
   - Implements OAuth 2.0 client for secure communication with the MCP server
   - Offers a user-friendly interface for memory management and querying
   - Uses its own PostgreSQL database separate from the MCP server

3. **Docker Infrastructure**: Containerized deployment for easy setup and scaling
   - Separate containers for MCP server (port 8001), Django client (port 8000), and PostgreSQL databases
   - Configured networking for secure inter-container communication
   - Volume mounting for persistent data storage
   - Compatible with both local Docker deployment and Render cloud deployment

### OAuth 2.0 Authentication Flow

The system implements OAuth 2.0 Authorization Code flow with PKCE (Proof Key for Code Exchange) for enhanced security, following RFC 6749 and RFC 7636 standards:

1. **Client Registration**:
   - The Django client registers with the MCP server using the `/register` endpoint
   - Registration includes client credentials, redirect URIs, and requested scopes
   - The MCP server issues a UUID-based client ID and cryptographically secure client secret
   - Client credentials should be stored securely and never exposed in client-side code

2. **Authorization Flow**:
   - User initiates login through the Django client
   - Client generates a cryptographically secure random `state` parameter for CSRF protection
   - Client generates a random PKCE `code_verifier` (min 43 characters) and derives `code_challenge` using SHA-256
   - Client redirects to MCP server's `/authorize` endpoint with:
     - `response_type=code`
     - `client_id` (UUID format)
     - `redirect_uri` (must exactly match one of the registered URIs)
     - `scope` (space-separated list, e.g., `memories:read memories:write`)
     - `state` (for CSRF protection and session binding)
     - PKCE parameters (`code_challenge` and `code_challenge_method=S256`)
   - MCP server authenticates the user (if not already authenticated)
   - MCP server validates all parameters and redirects back to the client with a short-lived authorization code

3. **Token Exchange**:
   - Client verifies the returned `state` parameter matches the one sent in the authorization request
   - Client exchanges the authorization code for access and refresh tokens via `/token` endpoint
   - Request includes:
     - `grant_type=authorization_code`
     - `code` (the authorization code received)
     - `redirect_uri` (must match the one used in authorization request)
     - `client_id` (UUID format)
     - `client_secret` (for confidential clients)
     - `code_verifier` (the original PKCE verifier that corresponds to the challenge)
   - MCP server validates all parameters, verifies the code hasn't been used before, and confirms the code_verifier
   - MCP server issues a JWT access token, refresh token, expiration time, and granted scopes
   - Client stores tokens securely (server-side for web applications) and never exposes them to the frontend

4. **API Access**:
   - Client includes the access token in the Authorization header (`Authorization: Bearer {token}`) for all API requests
   - MCP server validates the token signature, expiration, and audience claims
   - MCP server enforces scope-based permissions for each endpoint
   - When the access token expires, client uses the refresh token to obtain a new one via the `/token` endpoint with `grant_type=refresh_token`
   - If refresh token is expired or invalid, client must restart the authorization flow

### Memory Management System

The core functionality of Picard MCP revolves around memory management with the following components:

1. **Memory Storage**:
   - Memories are stored as text with associated metadata
   - Vector embeddings (using text-embedding-3-small model) enable semantic search capabilities
   - Permissions control who can access each memory
   - Timestamps track creation, modification, and expiration
   - Memory text is encrypted at rest while metadata remains searchable
   - All identifiers use UUID format instead of sequential integers for scalability
   - Each memory is converted to a vector embedding using OpenAI's embedding model
   - Embeddings enable semantic search and similarity matching
   - PostgreSQL with pgvector extension provides efficient vector storage and retrieval

2. **Permission Management**:
   - Each memory has a permission level (private or public)
   - Private memories are only accessible to the owner
   - Public memories can be accessed by other users for persona queries
   - System is designed to be extensible for future permission types (e.g., for statistical/aggregated use)
   - Shared memories can be accessed by specific users or groups
   - Permissions can be modified by the memory owner at any time

3. **Memory Retrieval**:
   - Users can retrieve their own memories with filtering and sorting options
   - Semantic search allows finding memories based on meaning, not just keywords
   - Vector similarity (cosine) enables finding related memories across the database
   - Top-N most similar memories are returned based on query relevance
   - Permission checks ensure users only access authorized memories

4. **LLM Integration**:
   - Memories can be used as context for LLM queries
   - Users can create personas based on their public memories
   - Other users can query these personas to get responses informed by the memories
   - The system handles context management and prompt engineering automatically

## Key Features

### MCP Server Features

- **OAuth 2.0 Authentication**:
  - Authorization Code flow with PKCE for enhanced security
  - Scope-based permission system (`memories:read`, `memories:write`, `memories:admin`)
  - Token management with refresh token support
  - Client registration and management

- **Memory Management**:
  - Create, read, update, and delete memories
  - Vector embedding for semantic search
  - Permission-based access control
  - Batch operations for efficient memory management

- **User Management**:
  - User registration and authentication
  - Profile management and settings
  - Activity tracking and analytics
  - Admin controls for system management

- **AI Integration**:
  - OpenAI API integration for embeddings and LLM queries
  - Persona creation based on user memories
  - Context-aware query processing
  - Customizable AI parameters and settings

### Django Client Features

- **User Interface**:
  - Clean, responsive design for desktop and mobile
  - Intuitive memory management interface
  - Advanced search and filtering options
  - Persona creation and query interface

- **OAuth Client Implementation**:
  - Secure token storage and management
  - Automatic token refresh
  - Scope-based feature availability
  - Error handling and recovery

- **Memory Tools**:
  - Memory creation with rich text support
  - Batch import and export
  - Permission management interface
  - Tagging and categorization

## MCP Interface

### MCP Resources

- **Memory Resource**: `memories://{memory_id}`
  - Returns the content of a specific memory with permission checks
  - Parameters: memory_id (UUID)
  - Response: Memory content with metadata

- **User Memories Resource**: `users://{user_id}/memories`
  - Returns a list of memories for a specific user with permission checks
  - Parameters: user_id (UUID), optional filters
  - Response: List of memory summaries

### MCP Tools

- **Submit Memory Tool**: Creates a new memory
  - Parameters: text (string), permission (string)
  - Returns: Created memory details with UUID

- **Update Memory Tool**: Updates an existing memory
  - Parameters: memory_id (UUID), text (string)
  - Returns: Updated memory details

- **Delete Memory Tool**: Deletes a memory
  - Parameters: memory_id (UUID)
  - Returns: Success confirmation

- **Query Memory Tool**: Performs semantic search on memories
  - Parameters: query (string), limit (integer)
  - Returns: List of relevant memories

- **Query User Tool**: Queries a user's persona based on memories
  - Parameters: user_id (UUID), query (string)
  - Returns: Response based on user's memories

## API Endpoints

### OAuth Endpoints

- **Client Registration**: `/register`
  - Method: POST
  - Description: Register a new OAuth client
  - Request: Client details (ID, secret, redirect URIs, scopes)
  - Response: Client credentials and registration information

- **Authorization**: `/authorize`
  - Method: GET
  - Description: Initiate OAuth authorization flow
  - Parameters: response_type, client_id, redirect_uri, scope, state, code_challenge, code_challenge_method
  - Response: Redirects to client with authorization code

- **Token Exchange**: `/token`
  - Method: POST
  - Description: Exchange authorization code for tokens
  - Request: grant_type, code, redirect_uri, client_id, client_secret, code_verifier
  - Response: Access token, refresh token, expiration, and scope information

### Memory Endpoints

- **Get Memories**: `/api/tools` (tool: `get_memories`)
  - Method: POST
  - Description: Retrieve memories with optional filtering
  - Authentication: Bearer token
  - Request: Optional filter parameters (user_id, permission, expiration status)
  - Response: List of memories accessible to the user
  - Example Request:
    ```json
    {
      "tool": "get_memories",
      "data": {
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "permission": "private"
      }
    }
    ```

- **Submit Memory**: `/api/tools` (tool: `submit_memory`)
  - Method: POST
  - Description: Create a new memory
  - Authentication: Bearer token
  - Request: Memory text, permission level, and expiration date (ISO 8601 format, e.g., "2025-12-31T23:59:59Z")
  - Response: Created memory details including UUID identifier
  - Example Request:
    ```json
    {
      "tool": "submit_memory",
      "data": {
        "text": "This is my memory content",
        "permission": "private"
      }
    }
    ```

- **Retrieve Memories**: `/api/tools` (tool: `retrieve_memories`)
  - Method: POST
  - Description: Get all memories for the authenticated user
  - Authentication: Bearer token
  - Response: List of memory objects with UUID identifiers
  - Example Request:
    ```json
    {
      "tool": "retrieve_memories",
      "data": {}
    }
    ```

- **Update Memory**: `/api/tools` (tool: `update_memory`)
  - Method: POST
  - Description: Update an existing memory
  - Authentication: Bearer token
  - Request: Memory ID, updated content, and optionally updated expiration date (ISO 8601 format)
  - Response: Updated memory details
  - Example Request:
    ```json
    {
      "tool": "update_memory",
      "data": {
        "memory_id": "550e8400-e29b-41d4-a716-446655440000",
        "text": "Updated memory content",
        "expiration_date": "2026-01-01T00:00:00Z"
      }
    }
    ```

- **Modify Permissions**: `/api/tools` (tool: `modify_permissions`)
  - Method: POST
  - Description: Update memory permission level
  - Authentication: Bearer token
  - Request: Memory UUID and new permission level
  - Response: Updated memory details
  - Example Request:
    ```json
    {
      "tool": "modify_permissions",
      "data": {
        "memory_id": "550e8400-e29b-41d4-a716-446655440000",
        "permission": "public"
      }
    }
    ```

- **Query User**: `/api/tools` (tool: `query_user`)
  - Method: POST
  - Description: Query a user's persona based on memories (public for other users, public+private for self)
  - Authentication: Bearer token
  - Request: User UUID and query prompt
  - Response: JSON containing non-expired memories, either all valid memories or top-N most similar to query
  - Response: AI-generated response based on user's memories
  - Example Request:
    ```json
    {
      "tool": "query_user",
      "data": {
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "prompt": "What are your thoughts on artificial intelligence?"
      }
    }
    ```

## Setup and Deployment

### Prerequisites

- Docker and Docker Compose
- Python 3.10+
- OpenAI API key

### Configuration

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/picard_mcp.git
   cd picard_mcp
   ```

2. Create a `.env` file based on the `.env.example` template:
   ```
   # PostgreSQL Configuration
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   POSTGRES_DB=picard_mcp
   POSTGRES_HOST=db
   POSTGRES_PORT=5432

   # MCP Server Configuration
   MCP_SERVER_NAME=Picard MCP
   MCP_SERVER_HOST=0.0.0.0
   MCP_SERVER_PORT=8000
   MCP_ISSUER_URL=http://localhost:8000

   # OAuth Configuration
   # Note: In production, use UUID format for client_id and a strong random string for client_secret
   OAUTH_CLIENT_ID=550e8400-e29b-41d4-a716-446655440000
   OAUTH_CLIENT_SECRET=a_strong_random_secret_at_least_32_characters
   OAUTH_REDIRECT_URI=http://localhost:8000/oauth/callback

   # OpenAI Configuration
   OPENAI_API_KEY=your_openai_api_key
   ```

3. Create a `.env` file for the Django client in the `django_client` directory:
   ```
   # Django settings
   DEBUG=True
   DJANGO_SECRET_KEY=django-insecure-key-for-development-only

   # MCP Server settings
   MCP_SERVER_URL=http://localhost:8000
   MCP_SERVER_INTERNAL_URL=http://app:8000

   # OAuth settings
   # Note: In production, use UUID format for client_id and a strong random string for client_secret
   OAUTH_CLIENT_ID=550e8400-e29b-41d4-a716-446655440000
   OAUTH_CLIENT_SECRET=a_strong_random_secret_at_least_32_characters
   OAUTH_REDIRECT_URI=http://localhost:8000/oauth/callback
   OAUTH_SCOPES=memories:read memories:write
   ```

4. Start the services using Docker Compose:
   ```bash
   docker-compose up -d
   ```
   This will start the following services:
   - `db-mcp`: PostgreSQL database for the MCP server (internal port 5432)
   - `db-django`: PostgreSQL database for the Django client (internal port 5432)
   - `mcp_server`: MCP server running on http://localhost:8001 (internal name: mcp_server:8000)
   - `django_client`: Django client running on http://localhost:8000

5. Register the Django client with the MCP server:
   ```bash
   docker exec picard_mcp-django_client-1 python register_oauth_client.py
   ```

6. Access the Django client at http://localhost:8000 and the MCP server at http://localhost:8001

### Testing

The repository includes test scripts to verify the functionality of both the MCP server and Django client:

- **MCP Server Tests**: `scripts/test_mcp_server.py`
  - Tests OAuth flow, memory endpoints, and user queries
  - Tests authentication for data access in the MCP server
  - Tests authentication for adding/modifying/removing data in the MCP server
  - Run with: `docker exec picard_mcp-app-1 python scripts/test_mcp_server.py`

- **Django Client Tests**: `scripts/test_django_client.py`
  - Tests user interface, OAuth integration, and memory management
  - Tests the interface between the Django client and the MCP server
  - Run with: `docker exec picard_mcp-django_client-1 python scripts/test_django_client.py`

### Local Development

1. Clone the repository
2. Copy `.env.example` to `.env` and fill in the required values
3. Run `docker-compose up`
4. Access the MCP server at http://localhost:8001
5. Access the Django client at http://localhost:8000

## Security Considerations

### Data Protection

- Memory text content is encrypted at rest using Python's Fernet symmetric encryption (AES-128 in CBC mode with PKCS7 padding) while metadata remains searchable
- Personal identifiable information (PII) is protected through text field encryption
- Access tokens have a 1-hour expiration time to limit exposure
- Refresh tokens are long-lived but use rotation: each use generates a new refresh token and invalidates the old one
- OAuth tokens are securely stored in the Django client's PostgreSQL database

### UUID Usage

All identifiers in the system use UUID v4 format instead of sequential integers for several reasons:

1. **Security**: UUIDs don't expose system information or record counts
2. **Scalability**: UUIDs can be generated without database coordination, enabling distributed systems
3. **Non-guessability**: UUIDs are practically impossible to guess, preventing enumeration attacks
4. **Consistency**: Using UUIDs throughout the system simplifies integration with other services

All IDs in the API (user_id, memory_id, client_id, etc.) must be in UUID format.

### OAuth Best Practices

- All OAuth communication must use HTTPS in production environments
- Authorization codes are single-use and short-lived (max 5 minutes)
- PKCE is required for all clients, even confidential ones, for defense in depth
- Refresh tokens are long-lived but can be revoked by users or administrators
- The system maintains a token blacklist for revoked tokens

## Documentation

### API Documentation

The MCP server includes Swagger/OpenAPI documentation for all endpoints:

- Access the Swagger UI at `/docs` when the server is running
- The OpenAPI specification is available at `/openapi.json`
- All API endpoints are fully documented with request/response schemas and examples

### Additional Documentation Files

- **TESTING.md**: Comprehensive guide to testing the application
  - Describes all implemented tests and their purposes
  - Instructions for running tests locally and in CI/CD
  - Documents test coverage and identifies areas needing additional testing

- **DEBUGGING.md**: Tracks issues and their resolutions
  - Logs known bugs that have not yet been fixed
  - Documents previously solved bugs and their solutions
  - Provides troubleshooting guidance for common issues

## Deployment

This project includes a `render.yaml` blueprint for deploying to Render. The same codebase works both locally in Docker containers and when deployed to Render cloud services.

### MCP Server Deployment

The MCP server can be deployed in several ways:

1. **Development Mode**:
   ```bash
   mcp dev app/server.py
   ```

2. **Direct Execution**:
   ```bash
   python app/server.py
   # or
   mcp run app/server.py
   ```

3. **Docker Deployment** (recommended for production):
   ```bash
   docker-compose up -d
   ```
   
   The Docker Compose configuration includes:
   - Network configuration for inter-container communication
   - Volume mounts for persistent data storage
   - Environment variable configuration from .env files
   - Port mappings (8000 for Django client, 8001 for MCP server)
   - Health checks for service dependencies

4. **Render Cloud Deployment**:
   Use the included `render.yaml` blueprint to deploy to Render.

## License

MIT