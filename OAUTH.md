# OAuth Authentication System

## Overview

This document describes the OAuth authentication system between the Django client and MCP server, including the credential management, validation, and automatic recovery mechanisms that have been implemented to ensure robust operation in production environments.

## Key Components

### 1. OAuth Client Registration

The OAuth client registration system uses these key components:

- **Client Registration Endpoint**: MCP server endpoint for registering OAuth clients
- **Client Validation Endpoint**: New endpoint for validating client credentials
- **Credential Management**: Multiple storage methods for persisting credentials
- **Automatic Recovery**: System for detecting and fixing invalid credentials

### 2. OAuth Credential Validation

The system includes mechanisms to validate OAuth credentials:

#### MCP Server: `/api/oauth/client_info` Endpoint

This endpoint allows validation of a client ID without requiring authentication:

```http
GET /api/oauth/client_info?client_id=<client_id>
```

Response for a valid client:
```json
{
  "client_id": "550e8400-e29b-41d4-a716-446655440000",
  "client_name": "Picard MCP Django Client",
  "redirect_uris": ["https://picard-django-client.onrender.com/oauth/callback"],
  "scopes": ["memories:read", "memories:write"]
}
```

#### Django Client: `ensure_oauth_credentials` Command

This management command verifies and fixes OAuth credentials:

```bash
python manage.py ensure_oauth_credentials [--force]
```

- Without `--force`: Validates existing credentials and only registers new ones if validation fails
- With `--force`: Forces registration of new credentials regardless of current state

### 3. OAuth Token Flow with Auto-Recovery

The enhanced OAuth flow includes automatic recovery from invalid credentials:

1. User initiates OAuth authorization
2. System redirects to MCP server authorization endpoint
3. User approves access
4. MCP server redirects back with authorization code
5. Django client exchanges code for tokens
6. If exchange fails with "invalid_client" error:
   - System automatically runs `ensure_oauth_credentials --force`
   - User is prompted to try again
   - New credentials are used for subsequent token requests

### 4. Credential Storage Methods

The system uses multiple storage methods to ensure credentials are available:

1. **Environment Variables**: Primary storage method
2. **Environment File**: `.env` file in project root
3. **Temporary Environment File**: `/tmp/oauth_credentials.env`
4. **Python Module**: `/tmp/oauth_credentials.py` for import-based loading

This multi-layered approach ensures credentials are available across process restarts and container rebuilds.

## Deployment Configuration

### Render Deployment

The Render deployment is configured to ensure proper OAuth credential handling:

1. **Environment Variables**:
   - `ENSURE_OAUTH_CREDENTIALS=true`: Enables automatic credential validation
   - `MCP_SERVER_INTERNAL_URL`: Set to the Render MCP server URL
   - `OAUTH_REDIRECT_URI`: Set to the Render Django client callback URL

2. **Startup Sequence**:
   - WSGI application initializes
   - `ensure_oauth_credentials` command runs automatically
   - Client validates credentials with MCP server
   - If validation fails, new credentials are registered

### Health Monitoring

The system includes health endpoints for monitoring OAuth status:

- `/health/`: General health check endpoint that includes OAuth status
- `/admin/fix-oauth/`: Admin endpoint for triggering credential fixes

## Testing

### Integration Tests

The test suite includes specific tests for the OAuth system:

- `test_oauth_recovery.py`: Tests the automatic recovery mechanism
- `monitor_oauth.py`: Monitors OAuth credential status

### Running Tests in Production

To run tests against the deployed environment:

```bash
python run_render_tests.py \
  --django-url https://picard-django-client.onrender.com \
  --mcp-url https://picard-mcp-server.onrender.com \
  --admin-password <password>
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Invalid Client Credentials

**Symptoms**: 
- "Invalid client" error during token exchange
- OAuth authorization fails with client error

**Solutions**:
- Run `ensure_oauth_credentials --force` to register new credentials
- Check logs for credential registration errors
- Verify MCP server is accessible from Django client

#### 2. Credentials Not Persisting

**Symptoms**:
- Credentials reset after container restart
- Frequent credential registration

**Solutions**:
- Check environment variable persistence in Render dashboard
- Verify temporary credential files are being created
- Check permissions on credential storage locations

#### 3. PKCE Validation Failures

**Symptoms**:
- "Code verifier does not match challenge" errors
- Authorization fails at token exchange

**Solutions**:
- Check PKCE implementation in client
- Verify code challenge method (S256)
- Check session handling for code verifier storage

## Future Improvements

- **Token Refresh Optimization**: Implement proactive token refresh before expiration
- **Credential Rotation**: Scheduled credential rotation for security
- **Multi-tenant Support**: Enhanced credential management for multiple client applications
- **Audit Logging**: Detailed audit trail for credential management operations
