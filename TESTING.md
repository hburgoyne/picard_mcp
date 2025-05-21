### Document Purpose
**TESTING.md:** Comprehensive guide to testing the application
- Describes all implemented tests and their purposes
- Instructions for running tests locally and in CI/CD
- Documents test coverage and identifies areas needing additional testing
---

# Picard MCP Testing Guide

## Phase 1: Project Setup and Configuration Tests

### Docker Environment Tests

At this phase, the primary testing is to verify that the Docker environment is properly set up and all containers can start successfully.

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
   - MCP Server: Visit http://localhost:8001/health in a browser or use `curl http://localhost:8001/health`
   - Django Client: Visit http://localhost:8000/health in a browser or use `curl http://localhost:8000/health`
   
   Both should return a JSON response with status "healthy".

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

## Phase 2: Database Model Tests

### Model Unit Tests

We've implemented comprehensive tests for all database models:

1. **User Model Tests**:
   - Test user creation and retrieval
   - Verify unique constraints for email and username
   - Confirm default values are set correctly

2. **Memory Model Tests**:
   - Test memory creation and association with users
   - Test vector embedding storage (using pgvector)
   - Verify expiration date logic and the is_expired property

3. **OAuth Models Tests**:
   - Test OAuthClient creation and verification
   - Test AuthorizationCode creation and expiration
   - Test Token creation, retrieval, and expiration checking

### Running Model Tests

```bash
# Run the model tests
docker exec -it picard_mcp-mcp_server pytest -xvs tests/test_models.py
```

### Automated Test Database Setup

The test database is automatically set up with:

1. An entrypoint script that:
   - Creates the test database (`picard_mcp_test`) if it doesn't exist
   - Enables the pgvector extension in both main and test databases
   - Runs migrations to initialize schema

2. Test fixtures in `conftest.py` that:
   - Configure a separate test database connection
   - Create and drop tables for each test
   - Ensure the pgvector extension is available

## Future Testing Plans

In subsequent phases, we will implement more comprehensive tests:

1. **API Tests**: For testing the REST endpoints
2. **OAuth Flow Tests**: For testing the complete OAuth 2.0 authentication flow
3. **End-to-End Tests**: For complete user workflows

These tests will be documented as they are implemented in future phases.
