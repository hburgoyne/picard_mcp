# Picard MCP Testing Guide

This document provides instructions for using the comprehensive test suites to diagnose and fix issues with the Picard MCP server and Django client.

## Test Suites Overview

Three test scripts have been created to systematically test different aspects of the system:

1. **MCP Server Test Suite** (`test_mcp_server.py`): Tests the MCP server's OAuth flow and memory endpoints.
2. **Django Client Test Suite** (`test_django_client.py`): Tests the Django client's integration with the MCP server.
3. **Combined Test Runner** (`run_all_tests.py`): Runs both test suites and provides a consolidated report.

## Prerequisites

- Docker and Docker Compose must be running
- The MCP server and Django client containers must be up
- Python 3.8+ with the following packages:
  - httpx
  - asyncio

## Running the Tests

### Option 1: Run All Tests

To run all tests with default settings:

```bash
docker-compose exec app python scripts/run_all_tests.py
```

This will test both the MCP server and Django client and provide a consolidated report.

### Option 2: Run Specific Tests

To run only the MCP server tests:

```bash
docker-compose exec app python scripts/run_all_tests.py --mcp
```

To run only the Django client tests:

```bash
docker-compose exec app python scripts/run_all_tests.py --django
```

### Option 3: Run Individual Test Suites Directly

To run the MCP server test suite directly:

```bash
docker-compose exec app python scripts/test_mcp_server.py
```

To run the Django client test suite directly:

```bash
docker-compose exec app python scripts/test_django_client.py
```

## Test Suite Configuration

You can customize the test suite behavior using command-line arguments:

```bash
docker-compose exec app python scripts/run_all_tests.py --mcp-url http://app:8000 --django-url http://django_client:8000 --output test_results.json
```

Available options:
- `--mcp-url`: URL for the MCP server (default: http://localhost:8001)
- `--django-url`: URL for the Django client (default: http://localhost:8000)
- `--output` or `-o`: Output file for test results in JSON format

## Understanding Test Results

Each test suite generates detailed logs and results that help identify issues:

1. **OAuth Flow Tests**: Verify the authentication process is working correctly
2. **Memory Endpoint Tests**: Verify the memory storage and retrieval endpoints
3. **User Interface Tests**: Verify the Django client's UI components
4. **Memory Management Tests**: Verify the Django client's memory management features

For each test, you'll see:
- ✅ PASSED: The test completed successfully
- ❌ FAILED: The test failed, with details about the failure

## Common Issues and Solutions

### OAuth Flow Issues

1. **404 Not Found for OAuth Endpoints**:
   - Check that the MCP server is properly configured to handle OAuth routes
   - Verify that the FastMCP server is mounted correctly in main.py
   - Ensure the PicardOAuthProvider is properly registered

2. **Type Errors in OAuth Token Creation**:
   - Ensure client_id is handled consistently as a string throughout the OAuth flow
   - Check that database column types match the data types used in the code

### Memory Endpoint Issues

1. **Endpoint Not Found (404)**:
   - Verify that memory endpoints are registered correctly with the MCP server
   - Check that the URL patterns match those expected by the client

2. **Authorization Failures**:
   - Ensure that the access token is valid and has the required scopes
   - Verify that the user authentication flow is complete

## Fixing Issues Systematically

1. Start by running the full test suite to identify all issues
2. Address OAuth flow issues first, as memory endpoints depend on authentication
3. Fix one issue at a time and re-run the tests to verify the fix
4. Document any changes made to fix issues for future reference

## Extending the Test Suites

You can extend these test suites by:
1. Adding new test methods to the existing classes
2. Creating additional test categories
3. Adding more detailed assertions for specific functionality

Follow the existing patterns in the test code to maintain consistency.
