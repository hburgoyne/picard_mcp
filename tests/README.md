# Picard MCP Testing

This directory contains integration tests that verify the interaction between the MCP server and Django client components.

## Test Types

The Picard MCP project includes several types of tests:

1. **MCP Server Unit Tests**: Located in `/mcp_server/tests/`
2. **Django Client Unit Tests**: Located in `/django_client/memory_app/tests/`
3. **Integration Tests**: Located in this directory (`/tests/`)

## Running Tests

### MCP Server Unit Tests

These tests verify the functionality of the MCP server components in isolation:

```bash
# Run from the project root
docker-compose exec mcp_server pytest -xvs

# Run a specific test file
docker-compose exec mcp_server pytest -xvs tests/test_oauth_pkce.py

# Run with coverage report
docker-compose exec mcp_server pytest --cov=app tests/
```

### Django Client Unit Tests

These tests verify the functionality of the Django client components in isolation:

```bash
# Run from the project root
docker-compose exec django_client python manage.py test

# Run a specific test file
docker-compose exec django_client python manage.py test memory_app.tests.test_oauth_integration
```

### Integration Tests

These tests verify the end-to-end functionality between the MCP server and Django client:

```bash
# Install required dependencies
pip install pytest selenium

# Run from the project root (both services must be running)
python -m pytest tests/test_oauth_integration.py -v
```

## Test Coverage

The tests cover the following functionality:

### OAuth Flow Tests

- **Authorization Flow**: Tests the complete OAuth 2.0 authorization flow with PKCE
- **Token Exchange**: Tests exchanging authorization codes for access and refresh tokens
- **Token Refresh**: Tests refreshing expired access tokens using refresh tokens
- **Error Handling**: Tests error conditions like invalid state parameters or missing code verifiers

### Integration Tests

- **End-to-End OAuth Flow**: Tests the complete user journey from login to authorization to token exchange
- **Token Refresh**: Tests the token refresh functionality in a real-world scenario

## Adding New Tests

When adding new features, please add corresponding tests:

1. **Unit Tests**: Add tests for individual components in their respective test directories
2. **Integration Tests**: Add tests for interactions between components in this directory

## Test Requirements

- **Unit Tests**: No external dependencies required beyond what's in the Docker containers
- **Integration Tests**: Requires Python 3.8+, pytest, and selenium with Chrome WebDriver

## Continuous Integration

These tests are designed to run in CI/CD pipelines. The unit tests run automatically, but integration tests require additional setup in CI environments.
