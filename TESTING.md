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

## Phase 2: MCP Server Implementation Tests

For Phase 2, we have implemented the following tests:

### API Endpoint Tests

1. **Health Endpoint Tests**:
   ```bash
   pytest mcp_server/tests/test_health.py -v
   ```
   Tests the basic health check and root endpoints to ensure the server is running correctly.

2. **OAuth 2.0 Tests**:
   ```bash
   pytest mcp_server/tests/test_oauth.py -v
   ```
   Tests the OAuth 2.0 implementation, including client registration, authorization, token exchange, and userinfo endpoints.

3. **Memory Management Tests**:
   ```bash
   pytest mcp_server/tests/test_memories.py -v
   ```
   Tests the memory CRUD operations, including creating, reading, updating, and deleting memories, as well as semantic search functionality.

4. **LLM Integration Tests**:
   ```bash
   pytest mcp_server/tests/test_llm.py -v
   ```
   Tests the LangChain integration for memory-based queries using LLMs.

5. **User Management Tests**:
   ```bash
   pytest mcp_server/tests/test_users.py -v
   ```
   Tests user creation, profile retrieval, and profile updates.

### Running Tests in Docker

All tests should be run inside the Docker container to ensure they use the same environment as the application. Follow these steps to set up and run the tests:

#### 1. Ensure all dependencies are installed

First, make sure the Docker container has all the required dependencies:

```bash
# Install required dependencies in the container
docker exec picard_mcp-mcp_server pip install httpx email-validator "pydantic[email]" authlib pytest pytest-asyncio pytest-cov
```

#### 2. Run the tests

```bash
# Run all tests in the MCP server container
docker exec picard_mcp-mcp_server python -m pytest /app/tests/ -v

# Run specific test file
docker exec picard_mcp-mcp_server python -m pytest /app/tests/test_health.py -v

# Run with coverage report
docker exec picard_mcp-mcp_server python -m pytest /app/tests/ --cov=app -v
```

#### 3. Troubleshooting

If you encounter dependency issues, you can check the logs:

```bash
# View the logs of the MCP server container
docker-compose logs mcp_server
```

If you need to rebuild the container with updated dependencies:

```bash
# Stop the existing containers
docker-compose down

# Rebuild the containers with no cache
docker-compose build --no-cache mcp_server

# Start the containers
docker-compose up -d
```

### Test Database Setup

The tests use a separate test database to avoid affecting the development database. For Docker-based testing, we use the Docker database service with a separate test database.

#### Setting Up the Test Database

1. First, create the test database in the Docker PostgreSQL container:

```bash
# Connect to the PostgreSQL container
docker exec -it picard_mcp-db-mcp bash

# Connect to PostgreSQL as the postgres user
psql -U postgres

# Create the test database
CREATE DATABASE test_picard_mcp;

# Create the pgvector extension in the test database
\c test_picard_mcp
CREATE EXTENSION vector;

# Exit PostgreSQL and the container
\q
exit
```

2. The test configuration in `mcp_server/tests/conftest.py` is set to use the Docker database service:

```python
# Test database URL for Docker environment
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@db-mcp:5432/test_picard_mcp"
```

## Future Testing Plans

### Phase 3: Django Client Implementation

As we move into Phase 3, we will implement the following tests:

1. **Django View Tests**:
   - Test user authentication views
   - Test memory management views
   - Test OAuth client integration

2. **Integration Tests**:
   - Test communication between Django client and MCP server
   - Test OAuth flow end-to-end

3. **UI Tests**:
   - Test user interface functionality
   - Test responsive design

### Additional Future Tests

In subsequent phases, we will also implement:

1. **Unit Tests**: For individual components and functions
2. **Integration Tests**: For API endpoints and database interactions
3. **End-to-End Tests**: For complete user workflows

These tests will be documented as they are implemented in future phases.
