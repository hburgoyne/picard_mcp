# Picard MCP Django Client

This is a simple Django application that integrates with the Picard MCP server for OAuth authentication and memory management.

## Features

- User registration and authentication
- OAuth2 integration with MCP server
- Memory creation and management
- Memory visibility control (public/private)
- Memory querying

## Setup

### Prerequisites

- Python 3.8+
- Docker and Docker Compose (for containerized setup)

### Environment Variables

The following environment variables are required:

```
DJANGO_SECRET_KEY=your-secret-key
MCP_SERVER_URL=http://localhost:8001
OAUTH_CLIENT_ID=picard_client
OAUTH_CLIENT_SECRET=picard_secret
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

The application is configured to run with Docker Compose alongside the MCP server.

```
docker-compose up -d
```

## Usage

1. Register a new user account
2. Log in to your account
3. Connect to the MCP server via OAuth
4. Create and manage memories
5. Query your memories

## OAuth Flow

1. User logs in to the Django app
2. User clicks "Connect to MCP Server" on the dashboard
3. User is redirected to the MCP server for authorization
4. MCP server redirects back to the Django app with an authorization code
5. Django app exchanges the code for an access token
6. Django app uses the access token for API calls to the MCP server

## API Endpoints

The Django app communicates with the following MCP server endpoints:

- `/auth/authorize` - OAuth authorization
- `/auth/token` - Token exchange
- `/tools/memories` - List memories
- `/tools/submit_memory` - Create a memory
- `/tools/update_memory` - Update a memory
- `/tools/query` - Query memories
