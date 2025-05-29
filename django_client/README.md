# Picard MCP Django Client

This Django application serves as a **fully functional** reference implementation for integrating with the Picard MCP server. It demonstrates the OAuth 2.0 authentication flow, memory management capabilities, and provides a complete user interface for interacting with the MCP server.

**✅ Current Status**: All core functionality is implemented and working, including OAuth flow, memory CRUD operations, and permission management.

## Features

- **✅ User Management**:
  - Registration and authentication
  - Profile management
  - OAuth 2.0 client implementation with User Context Token flow

- **✅ Memory Management**:
  - Creation, retrieval, updating, and deletion of memories
  - Permission control (public/private) with toggle interface
  - Memory expiration date management (using ISO 8601 format)
  - Encrypted storage of sensitive memory content using Fernet symmetric encryption

- **✅ Search and Query**:
  - Basic memory filtering and retrieval
  - Permission-based access control
  - Filtering by permission level and expiration date

- **✅ OAuth 2.0 Implementation**:
  - Secure token storage in PostgreSQL database
  - Automatic token refresh with 1-hour access token lifetime
  - Scope-based feature availability
  - Comprehensive error handling and recovery

- **🔄 Advanced Features** (Infrastructure Ready):
  - Semantic search using vector embeddings
  - Persona-based querying
  - AI-powered memory interactions

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
   - Permission level (public or private) with toggle controls
   - Optional expiration date in ISO 8601 format (e.g., "2025-12-31T23:59:59Z")
5. Manage your memories:
   - View all your memories with filtering options
   - Edit memory content and expiration dates
   - Change permission levels using toggle controls
   - Delete memories with confirmation
6. **Current capabilities**:
   - Basic memory retrieval and filtering
   - Permission-based access control
   - Memory CRUD operations
7. **🔄 Planned features**:
   - Perform semantic searches across your memories
   - Query your own persona (includes private and public memories)
   - Query other users' personas (only includes their public memories)

## OAuth Flow

The Django client implements the **User Context Token flow** for simplified authentication with the MCP server:

1. User logs in to the Django app
2. User clicks "Connect to MCP Server" on the dashboard
3. Django client makes a server-side request to the MCP's `/api/user-tokens/user-token` endpoint
4. The request includes:
   - Client credentials (client_id and client_secret)
   - User information (username and email)
   - Option to create user if not exists
5. The MCP server verifies client credentials and either finds or creates a corresponding user
6. MCP server issues access and refresh tokens for the user
7. Django client securely stores these tokens and uses them for API requests
8. When the access token expires, the client uses the refresh token to obtain a new one
9. Each refresh token use generates a new refresh token and invalidates the old one

**Note**: This is different from the standard OAuth 2.0 Authorization Code flow with PKCE, which would require users to authenticate with both the client and the MCP server. The current implementation provides a streamlined user experience.

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
docker-compose exec django_client python manage.py test
```

**✅ Current Test Status**: 13/13 tests passing, including:
- User interface functionality
- OAuth integration with the MCP server
- Memory management features
- The interface between the Django client and the MCP server
- Permission management and error handling

For comprehensive testing documentation, see the main project's [TESTING.md](../TESTING.md).
