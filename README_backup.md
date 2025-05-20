# Picard MCP Server

## Overview

Picard MCP is a complete memory management system built on the Model Context Protocol (MCP) standard. It consists of two main components: an MCP server that provides secure memory storage and retrieval services, and a Django client application that demonstrates how to integrate with the MCP server. The system enables users to store, retrieve, and manage their memories while controlling access permissions, and allows for semantic search and AI-powered queries based on stored memories.

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
   - Integrates with OpenAI API for memory embeddings and LLM queries

2. **Django Client**: Web application that demonstrates integration with the MCP server
   - Provides user registration, authentication, and profile management
   - Implements OAuth 2.0 client for secure communication with the MCP server
   - Offers a user-friendly interface for memory management and querying

3. **Docker Infrastructure**: Containerized deployment for easy setup and scaling
   - Separate containers for MCP server, Django client, and PostgreSQL database
   - Configured networking for secure inter-container communication
   - Volume mounting for persistent data storage

### OAuth 2.0 Authentication Flow

The system implements OAuth 2.0 Authorization Code flow with PKCE (Proof Key for Code Exchange) for enhanced security:

1. **Client Registration**:
   - The Django client registers with the MCP server using the `/register` endpoint
   - Registration includes client credentials, redirect URIs, and requested scopes
   - The MCP server issues a client ID and secret for subsequent authentication

2. **Authorization Flow**:
   - User initiates login through the Django client
   - Client redirects to MCP server's `/authorize` endpoint with:
     - `response_type=code`
     - `client_id`
     - `redirect_uri`
     - `scope` (e.g., `memories:read memories:write`)
     - `state` (for CSRF protection)
     - PKCE parameters (`code_challenge` and `code_challenge_method=S256`)
   - MCP server authenticates the user and redirects back to the client with an authorization code

3. **Token Exchange**:
   - Client exchanges the authorization code for access and refresh tokens via `/token` endpoint
   - Request includes the authorization code, client credentials, and PKCE verifier
   - MCP server validates the request and issues access and refresh tokens
   - Client stores tokens securely for subsequent API calls

4. **API Access**:
   - Client includes the access token in the Authorization header for all API requests
   - MCP server validates the token and enforces scope-based permissions
   - When the access token expires, client uses the refresh token to obtain a new one

### Memory Management System

The core functionality of Picard MCP revolves around memory management with the following components:

1. **Memory Storage**:
   - Memories are stored as text with associated metadata
   - Each memory is converted to a vector embedding using OpenAI's embedding model
   - Embeddings enable semantic search and similarity matching
   - PostgreSQL with pgvector extension provides efficient vector storage and retrieval

2. **Permission System**:
   - Each memory has a permission level (private, public, or shared)
   - Private memories are only accessible to the owner
   - Public memories can be accessed by any authenticated user
   - Shared memories can be accessed by specific users or groups
   - Permissions can be modified by the memory owner at any time

3. **Memory Retrieval**:
   - Users can retrieve their own memories with filtering and sorting options
   - Semantic search allows finding memories based on meaning, not just keywords
   - Vector similarity enables finding related memories across the database
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

- **Submit Memory**: `/api/tools` (tool: `submit_memory`)
  - Method: POST
  - Description: Create a new memory
  - Authentication: Bearer token
  - Request: Memory text and permission level
  - Response: Created memory details

- **Retrieve Memories**: `/api/tools` (tool: `retrieve_memories`)
  - Method: POST
  - Description: Get all memories for the authenticated user
  - Authentication: Bearer token
  - Response: List of memory objects

- **Modify Permissions**: `/api/tools` (tool: `modify_permissions`)
  - Method: POST
  - Description: Update memory permission level
  - Authentication: Bearer token
  - Request: Memory ID and new permission level
  - Response: Updated memory details

- **Query User**: `/api/tools` (tool: `query_user`)
  - Method: POST
  - Description: Query a user's persona based on public memories
  - Authentication: Bearer token
  - Request: User ID and query prompt
  - Response: AI-generated response based on user's memories

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
   OAUTH_CLIENT_ID=picard_client
   OAUTH_CLIENT_SECRET=picard_secret
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
   OAUTH_CLIENT_ID=picard_client
   OAUTH_CLIENT_SECRET=picard_secret
   OAUTH_REDIRECT_URI=http://localhost:8000/oauth/callback
   OAUTH_SCOPES=memories:read memories:write
   ```

4. Start the services using Docker Compose:
   ```bash
   docker-compose up -d
   ```

5. Register the Django client with the MCP server:
   ```bash
   docker exec picard_mcp-django_client-1 python register_oauth_client.py
   ```

6. Access the Django client at http://localhost:8000 and the MCP server at http://localhost:8001

### Testing

The repository includes test scripts to verify the functionality of both the MCP server and Django client:

- **MCP Server Tests**: `scripts/test_mcp_server.py`
  - Tests OAuth flow, memory endpoints, and user queries
  - Run with: `docker exec picard_mcp-app-1 python scripts/test_mcp_server.py`

- **Django Client Tests**: `scripts/test_django_client.py`
  - Tests user interface, OAuth integration, and memory management
  - Run with: `docker exec picard_mcp-django_client-1 python scripts/test_django_client.py`

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