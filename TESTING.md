# Picard MCP Testing Guide

## Quick Start: Running All Tests

To run all tests for the Picard MCP project (MCP server, Django client, and integration tests), follow these steps:

### Prerequisites

1. Ensure Docker and Docker Compose are installed
2. Make sure all containers are running:
   ```bash
   docker-compose up -d
   ```
3. Install required Python dependencies for integration tests:
   ```bash
   pip install pytest selenium requests
   ```
4. Ensure you have Chrome WebDriver installed for browser automation tests

### Run All Tests with One Command

The easiest way to run all tests is with our all-in-one command:

```bash
python tests/test_oauth_integration.py --all
```

This will run:
1. MCP server tests (FastAPI backend)
2. Django client tests (web frontend)
3. Integration tests (OAuth flow between services)

### Running Tests Individually

If you prefer to run tests separately:

```bash
# MCP server tests
docker-compose exec mcp_server pytest -xvs

# Django client tests
docker exec picard_mcp-django_client python manage.py test

# Integration tests
python -m pytest tests/test_oauth_integration.py -v
```

---

## Detailed Test Documentation

### Environment Setup Tests

### Docker Environment Tests

These tests verify that the Docker environment is properly set up and all containers can start successfully.

#### Testing Docker Setup

1. **Basic Docker Compose Test**:
   ```bash
   docker-compose down
   docker-compose up -d
   ```
   Verify that all containers start successfully without errors.

2. **Container Health Check**:
   ```bash
   docker-compose ps
   ```
   Verify that all containers show as "Up" and the database containers show as "healthy".

3. **Database Connection Test**:
   ```bash
   # Test MCP server database connection
   docker exec picard_mcp-db-mcp psql -U postgres -d picard_mcp -c "SELECT 1;"
   
   # Test Django client database connection
   docker exec picard_mcp-db-django psql -U postgres -d django_client -c "SELECT 1;"
   ```
   Both commands should return "1" if the database connections are working.

4. **Web Server Access Test**:
   - MCP Server: Visit http://localhost:8001/docs in a browser or use `curl http://localhost:8001/health`
   - Django Client: Visit http://localhost:8000 in a browser

### Environment Configuration Tests

These manual tests verify that the environment variables are properly loaded from .env files:

1. **Environment Files Setup Test**:
   ```bash
   # Verify that .env files exist
   ls -la .env
   ls -la django_client/.env
   ```
   Both files should exist. If they don't, create them from the example files:
   ```bash
   cp .env.example .env
   cp django_client/.env.example django_client/.env
   ```

2. **MCP Server Environment Test**:
   ```bash
   docker exec picard_mcp-mcp_server env | grep -E "POSTGRES|MCP|OAUTH"
   ```
   Verify that all required environment variables are loaded from the .env file.

3. **Django Client Environment Test**:
   ```bash
   docker exec picard_mcp-django_client env | grep -E "DB_|MCP|OAUTH"
   ```
   Verify that all required environment variables are loaded from the django_client/.env file.

## MCP Server Tests

### MCP Server Tests

The MCP server tests are organized into several categories:

#### Model Tests

1. **User Model Tests**:
   - Test user creation with default values
   - Test unique constraints (email, username)

2. **Memory Model Tests**:
   - Test memory creation with default values
   - Test the expiration date functionality
   - Test vector embeddings storage
   - Test user-memory relationships

3. **OAuth Model Tests**:
   - Test OAuth client creation
   - Test authorization code creation and expiration
   - Test token creation and expiration
   - Test relationships between models

#### OAuth Implementation Tests

1. **OAuth Authorization Tests**:
   - Test authorization endpoint with and without PKCE
   - Test user consent flow
   - Test authorization code generation

2. **OAuth Token Tests**:
   - Test token exchange with authorization code
   - Test token refresh flow
   - Test token validation

#### Running MCP Server Tests

```bash
# Run all MCP server tests
docker-compose exec mcp_server pytest -xvs

# Run specific test files
docker-compose exec mcp_server pytest -xvs tests/test_oauth.py
docker-compose exec mcp_server pytest -xvs tests/test_oauth_pkce.py
```

### Django Client Tests

The Django client tests focus on user authentication, profile management, and OAuth integration:

1. **User Authentication Tests**:
   - Test user registration and login
   - Test profile management

2. **OAuth Client Tests**:
   - Test OAuth authorization flow
   - Test token storage and management
   - Test token refresh

#### Running Django Client Tests

```bash
# Collect static files (only needed initially or after changes)
docker exec picard_mcp-django_client python manage.py collectstatic --noinput

# Run all Django client tests
docker exec picard_mcp-django_client python manage.py test
```

## Phase 3: OAuth 2.0 Implementation Tests

### OAuth Core Setup Tests

We have implemented tests to verify the OAuth 2.0 core setup:

1. **OAuth Client Registration Test** (`test_register_client`):
   - Verifies that OAuth clients can be registered via the API
   - Tests validation of client data
   - Checks that client credentials are generated properly
   - Verifies client is saved in the database

2. **OAuth Authorization Endpoint Test** (`test_authorize_endpoint`):
   - Verifies the authorization flow
   - Tests redirection with authorization code
   - Validates state parameter handling
   - Checks PKCE challenge handling
   - Verifies user ID is properly used in authorization

3. **OAuth Token Endpoint Test** (`test_token_endpoint`):
   - Verifies authorization code exchange for tokens
   - Tests token response format
   - Validates client credentials requirement
   - Checks PKCE code verifier validation
   - Verifies token storage in database

### OAuth PKCE Flow Tests

We have implemented comprehensive tests for the OAuth 2.0 PKCE flow:

1. **PKCE Authorization Test** (`test_authorize_with_pkce`):
   - Verifies the authorization flow with PKCE challenge
   - Tests the consent page rendering
   - Validates the authorization code generation
   - Checks that code challenge is stored with authorization code

2. **PKCE Token Exchange Test** (`test_token_exchange_with_pkce`):
   - Verifies token exchange with valid code verifier
   - Tests token response format and content
   - Validates that authorization code is consumed
   - Checks token storage in database

3. **PKCE Security Test** (`test_token_exchange_without_code_verifier`):
   - Verifies that token exchange fails without code verifier
   - Tests error response format
   - Validates security requirements

4. **Token Refresh Test** (`test_refresh_token`):
   - Verifies refresh token flow
   - Tests new token generation
   - Validates old refresh token invalidation
   - Checks token rotation security

### Django OAuth Client Tests

We have implemented tests for the Django client's OAuth integration:

1. **OAuth Authorization Test** (`test_oauth_authorize_generates_state_and_pkce`):
   - Verifies state and PKCE parameter generation
   - Tests session storage of parameters
   - Validates redirect URL format

2. **OAuth Callback Test** (`test_oauth_callback_exchanges_code_for_tokens`):
   - Verifies authorization code exchange
   - Tests state validation
   - Validates token storage in database
   - Checks error handling

3. **Token Model Test** (`test_token_is_expired`, `test_token_get_for_user`):
   - Verifies token expiration logic
   - Tests token retrieval methods
   - Validates token management

## OAuth Integration Tests

The integration tests verify the complete OAuth flow between the MCP server and Django client, ensuring that both services work together correctly.

### Test Coverage

1. **OAuth Flow Integration Test** (`test_oauth_flow`):
   - Tests the complete user journey from login to authorization
   - Verifies consent page rendering and approval
   - Validates token exchange and storage
   - Checks successful redirection and session management

2. **Token Refresh Integration Test** (`test_token_refresh`):
   - Tests the refresh token flow in a real-world scenario
   - Verifies token refresh functionality between services
   - Validates session persistence

#### Prerequisites for Integration Tests

Before running the integration tests, ensure you have:

1. Both services (MCP server and Django client) running via Docker Compose
2. Required Python dependencies installed:
   ```bash
   pip install pytest selenium requests
   ```
3. Chrome WebDriver installed on your system
4. Created a test user in the Django client:
   ```bash
   docker exec picard_mcp-django_client python manage.py shell -c "from django.contrib.auth.models import User; User.objects.filter(username='integrationtestuser').exists() or User.objects.create_user(username='integrationtestuser', email='integration@example.com', password='integrationtestpassword')"
   ```

#### Running the Integration Tests

To run the integration tests:

```bash
# Make sure both services are running
docker-compose up -d

# Run the integration tests
python -m pytest tests/test_oauth_integration.py -v
```

You can also run the integration tests directly with Python, which provides more options:

```bash
# Run just the integration tests
python tests/test_oauth_integration.py

# Run all tests (MCP server, Django client, and integration tests)
python tests/test_oauth_integration.py --all
```

### Running All Tests

To run all tests (MCP server, Django client, and integration tests), you can either run them in sequence or use our all-in-one command:

#### Running Tests in Sequence

```bash
# Make sure the Docker containers are running
docker-compose up -d

# Run MCP server tests
docker-compose exec mcp_server pytest -xvs

# Run Django client tests (collect static files first if needed)
docker exec picard_mcp-django_client python manage.py collectstatic --noinput
docker exec picard_mcp-django_client python manage.py test

# Run integration tests
python -m pytest tests/test_oauth_integration.py -v
```

#### Running All Tests with One Command

We've added a convenience method to run all tests with a single command:

```bash
# Make sure the Docker containers are running
docker-compose up -d

# Run all tests (MCP server, Django client, and integration tests)
python tests/test_oauth_integration.py --all
```

This will run all test suites in sequence and provide a summary of the results.

## Test Coverage

Our current test coverage includes:

1. **Unit Tests**: For individual components in isolation
   - MCP server models, utilities, and endpoints
   - Django client views, forms, and models

2. **Integration Tests**: For interactions between components
   - OAuth flow between MCP server and Django client
   - Token management and refresh flows

3. **End-to-End Tests**: For complete user workflows
   - User registration and authentication
   - OAuth authorization and consent
   - Token exchange and management

## Future Testing Plans

In subsequent phases, we will implement additional tests for:

1. **Memory Management API**: Tests for memory creation, retrieval, and search
2. **Permission System**: Tests for scope-based permissions and access control
3. **Vector Embedding**: Tests for semantic search functionality
4. **LLM Integration**: Tests for AI-powered memory queries
