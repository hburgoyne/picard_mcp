# Picard MCP Django Client

This Django application serves as a reference implementation for integrating with the Picard MCP server. It demonstrates the OAuth 2.0 authentication flow, memory management capabilities, and persona-based querying features provided by the MCP server.

## Features

- **User Management**:
  - Registration and authentication
  - Profile management
  - OAuth 2.0 client implementation with PKCE

- **Memory Management**:
  - Creation, retrieval, updating, and deletion of memories
  - Permission control (public/private)
  - Memory expiration date management (using ISO 8601 format)
  - Encrypted storage of sensitive memory content using Fernet symmetric encryption

- **Search and Query**:
  - Semantic search using vector embeddings
  - Persona-based querying
  - Filtering by permission level and expiration date

- **OAuth 2.0 Implementation**:
  - Secure token storage in PostgreSQL database
  - Automatic token refresh with 1-hour access token lifetime
  - Scope-based feature availability
  - Error handling and recovery

## Setup

### Prerequisites

- Python 3.10+
- Docker and Docker Compose (for containerized setup)
- PostgreSQL database (separate from the MCP server database)

### Environment Variables

Create a `.env` file in the django_client directory with the following variables:

```
# Django settings
DEBUG=True
DJANGO_SECRET_KEY=django-insecure-key-for-development-only

# Database settings
DB_NAME=django_client
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432

# MCP Server settings
MCP_SERVER_URL=http://localhost:8001
MCP_SERVER_INTERNAL_URL=http://app:8000

# OAuth settings
# Note: In production, use UUID format for client_id and a strong random string for client_secret
OAUTH_CLIENT_ID=550e8400-e29b-41d4-a716-446655440000
OAUTH_CLIENT_SECRET=a_strong_random_secret_at_least_32_characters
OAUTH_REDIRECT_URI=http://localhost:8000/oauth/callback
OAUTH_SCOPES=memories:read memories:write
```

### Local Development

1. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run migrations:
   ```
   python manage.py migrate
   ```

4. Create a superuser:
   ```
   python manage.py createsuperuser
   ```

5. Run the development server:
   ```
   python manage.py runserver
   ```

### Docker Setup

The application is configured to run with Docker Compose alongside the MCP server. From the project root directory:

```bash
docker-compose up -d
```

This will start the following services:
- `db-django`: PostgreSQL database for the Django client (internal port 5432)
- `django_client`: Django client web application on port 8000
- `mcp_server`: MCP server running on port 8001 (internal name: mcp_server:8000)
- `db-mcp`: PostgreSQL database for the MCP server (internal port 5432)

After starting the services, register the Django client with the MCP server (requires admin authentication):

```bash
docker-compose exec django_client python register_oauth_client.py
```

Note: The registration script uses admin credentials from environment variables (`ADMIN_USERNAME` and `ADMIN_PASSWORD`). Make sure these are set in your environment or the script will use default values (admin/adminpassword).

Access the Django client at http://localhost:8000

## Usage

1. Register a new user account on the Django client
2. Log in to your account
3. Connect to the MCP server via OAuth by clicking "Connect to MCP Server"
4. Create memories with the following attributes:
   - Text content (will be encrypted at rest using Fernet encryption)
   - Permission level (public or private)
   - Expiration date in ISO 8601 format (e.g., "2025-12-31T23:59:59Z") indicating when the memory is no longer considered valid
5. Manage your memories:
   - View all your memories
   - Edit memory content
   - Change permission levels
   - Delete memories
6. Search and query:
   - Perform semantic searches across your memories
   - Query your own persona (includes private and public memories)
   - Query other users' personas (only includes their public memories)

## OAuth Flow

The Django client implements the OAuth 2.0 Authorization Code flow with PKCE (Proof Key for Code Exchange) for enhanced security:

1. User logs in to the Django app
2. User clicks "Connect to MCP Server" on the dashboard
3. Django client generates a cryptographically secure random `state` parameter for CSRF protection
4. Client generates a random PKCE `code_verifier` and derives `code_challenge` using SHA-256
5. Client redirects to MCP server's `/authorize` endpoint with required parameters
6. MCP server authenticates the user (if not already authenticated)
7. MCP server validates all parameters and redirects back to the client with an authorization code
8. Django client verifies the returned `state` parameter matches the one sent in the request
9. Client exchanges the authorization code for access and refresh tokens via `/token` endpoint
10. Client stores tokens securely and uses the access token for API calls
11. When the access token expires, the client uses the refresh token to obtain a new access token
12. Each refresh token use generates a new refresh token and invalidates the old one

## MCP Server Integration

### OAuth Endpoints

- **Authorization**: `/oauth/authorize`
  - Method: GET
  - Description: Initiates the OAuth 2.0 authorization flow
  - Parameters: response_type, client_id, redirect_uri, scope, state, code_challenge, code_challenge_method

- **Token Exchange**: `/oauth/token`
  - Method: POST
  - Description: Exchange authorization code for tokens
  - Request: grant_type, code, redirect_uri, client_id, client_secret, code_verifier
  - Response: Access token, refresh token, expiration, and scope information

- **Token Refresh**: `/oauth/token`
  - Method: POST
  - Description: Refresh an expired access token
  - Request: grant_type=refresh_token, refresh_token, client_id, client_secret
  - Response: New access token, new refresh token, expiration, and scope information

### Memory Tools

- **Submit Memory**: `/api/tools` (tool: `submit_memory`)
  - Method: POST
  - Description: Create a new memory
  - Authentication: Bearer token
  - Request: Memory text, permission level, and expiration date (ISO 8601 format)
  - Response: Created memory details including UUID identifier

- **Get Memories**: `/api/tools` (tool: `get_memories`)
  - Method: POST
  - Description: Retrieve memories with optional filtering
  - Authentication: Bearer token
  - Request: Optional filter parameters
  - Response: List of memories accessible to the user

- **Update Memory**: `/api/tools` (tool: `update_memory`)
  - Method: POST
  - Description: Update an existing memory
  - Authentication: Bearer token
  - Request: Memory ID, updated content, and optionally updated expiration date (ISO 8601 format)
  - Response: Updated memory details

- **Delete Memory**: `/api/tools` (tool: `delete_memory`)
  - Method: POST
  - Description: Delete a memory
  - Authentication: Bearer token
  - Request: Memory ID
  - Response: Deletion confirmation

- **Query Memory**: `/api/tools` (tool: `query_memory`)
  - Method: POST
  - Description: Perform semantic search on memories
  - Authentication: Bearer token
  - Request: Query text and optional limit
  - Response: List of relevant memories

- **Query User**: `/api/tools` (tool: `query_user`)
  - Method: POST
  - Description: Query a user's persona based on memories
  - Authentication: Bearer token
  - Request: User UUID and query prompt
  - Response: JSON containing non-expired memories, either all valid memories or top-N most similar to query

## Testing

To test the Django client integration with the MCP server:

```bash
docker exec picard_mcp-django_client-1 python scripts/test_django_client.py
```

This will test:
- User interface functionality
- OAuth integration with the MCP server
- Memory management features
- The interface between the Django client and the MCP server
