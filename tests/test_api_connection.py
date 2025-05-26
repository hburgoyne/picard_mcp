"""
Direct API connection test between Django client and MCP server.

This test bypasses the UI and directly tests the API connection
between the Django client and MCP server.

Usage:
    cd /Users/hayden/Documents/Github/picard_mcp
    python -m pytest tests/test_api_connection.py -v
"""
import os
import sys
import pytest
import requests
import json
import time
from urllib.parse import urlparse, parse_qs

# Configuration
DJANGO_URL = "http://localhost:8000"
MCP_URL = "http://localhost:8001"
MCP_INTERNAL_URL = "http://mcp_server:8000"  # Used for direct container-to-container communication

def test_mcp_server_health():
    """Test that the MCP server is running and healthy."""
    print("\n=== Testing MCP server health ===")
    try:
        # Check MCP server health endpoint
        response = requests.get(f"{MCP_URL}/health")
        print(f"MCP server health response: {response.status_code}")
        print(f"Response body: {response.text}")
        
        assert response.status_code == 200, f"MCP server health check failed with status {response.status_code}"
        assert "status" in response.json(), "MCP server health response missing status field"
        assert response.json()["status"] == "ok", f"MCP server health status is not ok: {response.json()}"
        
        print("MCP server health check passed")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Error connecting to MCP server: {str(e)}")

def test_django_client_health():
    """Test that the Django client is running and healthy."""
    print("\n=== Testing Django client health ===")
    try:
        # Check Django client home page
        response = requests.get(f"{DJANGO_URL}/")
        print(f"Django client home page response: {response.status_code}")
        
        assert response.status_code == 200, f"Django client home page check failed with status {response.status_code}"
        
        print("Django client health check passed")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Error connecting to Django client: {str(e)}")

def test_direct_api_connection():
    """Test direct API connection between Django client and MCP server."""
    print("\n=== Testing direct API connection ===")
    
    # First, we need to get an OAuth token
    # We'll do this by creating a test user and logging in
    username = f"apitest_{int(time.time())}"
    password = "testpassword123"
    email = f"{username}@example.com"
    
    try:
        # 1. Create a test user using Django's admin command
        create_user_cmd = f"docker exec picard_mcp-django_client python manage.py shell -c \"from django.contrib.auth.models import User; User.objects.create_user(username='{username}', email='{email}', password='{password}')\""
        print(f"Creating test user with command: {create_user_cmd}")
        os.system(create_user_cmd)
        
        # 2. Log in with the test user
        session = requests.Session()
        login_data = {
            "username": username,
            "password": password,
            "csrfmiddlewaretoken": session.get(f"{DJANGO_URL}/login/").cookies['csrftoken']
        }
        login_response = session.post(f"{DJANGO_URL}/login/", data=login_data)
        print(f"Login response status: {login_response.status_code}")
        assert login_response.status_code == 200 or login_response.status_code == 302, f"Login failed with status {login_response.status_code}"
        
        # 3. Explicitly use the direct connect endpoint instead of the OAuth authorize flow
        direct_connect_response = session.get(f"{DJANGO_URL}/oauth/direct-connect/")
        print(f"Direct connect response status: {direct_connect_response.status_code}")
        assert direct_connect_response.status_code == 200 or direct_connect_response.status_code == 302, f"Direct connect failed with status {direct_connect_response.status_code}"
        
        # 4. Check if we're redirected to the dashboard, which means we're authorized
        dashboard_response = session.get(f"{DJANGO_URL}/dashboard/")
        print(f"Dashboard response status: {dashboard_response.status_code}")
        assert dashboard_response.status_code == 200, f"Dashboard access failed with status {dashboard_response.status_code}"
        assert "Connected to MCP" in dashboard_response.text, "User is not connected to MCP server according to dashboard"
        
        # 5. Verify that the OAuth token exists and has the correct scopes
        check_token_cmd = f"docker exec picard_mcp-django_client python manage.py shell -c \"from django.contrib.auth.models import User; from memory_app.models import OAuthToken; user = User.objects.get(username='{username}'); token = OAuthToken.objects.get(user=user); print(f'Token exists: {{token is not None}}'); print(f'Token scopes: {{token.scope}}'); print(f'Token expired: {{token.is_expired}}');\""
        print(f"Checking token with command: {check_token_cmd}")
        os.system(check_token_cmd)
        
        # 6. Now try to directly call the Django client's API to create a memory
        create_memory_data = {
            "text": f"API Test Memory {int(time.time())}",
            "permission": "private",
            "csrfmiddlewaretoken": session.get(f"{DJANGO_URL}/memories/create/").cookies['csrftoken']
        }
        
        create_memory_response = session.post(f"{DJANGO_URL}/memories/create/", data=create_memory_data)
        print(f"Create memory response status: {create_memory_response.status_code}")
        print(f"Create memory response headers: {dict(create_memory_response.headers)}")
        
        # Check if we were redirected to the dashboard or memory detail page
        assert create_memory_response.status_code == 200 or create_memory_response.status_code == 302, f"Memory creation failed with status {create_memory_response.status_code}"
        
        # 7. Check if the memory was created by looking at the dashboard
        dashboard_response = session.get(f"{DJANGO_URL}/dashboard/")
        assert dashboard_response.status_code == 200, f"Dashboard access failed with status {dashboard_response.status_code}"
        
        # Check if our memory text is in the dashboard HTML
        assert create_memory_data["text"] in dashboard_response.text, "Created memory not found on dashboard"
        
        print("Direct API connection test passed")
        
    except Exception as e:
        pytest.fail(f"Direct API connection test failed: {str(e)}")

def test_mcp_server_api_endpoints():
    """Test MCP server API endpoints directly."""
    print("\n=== Testing MCP server API endpoints ===")
    
    try:
        # Check MCP server API docs
        docs_response = requests.get(f"{MCP_URL}/docs")
        print(f"MCP server API docs response: {docs_response.status_code}")
        assert docs_response.status_code == 200, f"MCP server API docs check failed with status {docs_response.status_code}"
        
        # Check MCP server OpenAPI schema
        openapi_response = requests.get(f"{MCP_URL}/openapi.json")
        print(f"MCP server OpenAPI schema response: {openapi_response.status_code}")
        assert openapi_response.status_code == 200, f"MCP server OpenAPI schema check failed with status {openapi_response.status_code}"
        
        # Verify that the tools endpoint exists in the OpenAPI schema
        openapi_schema = openapi_response.json()
        assert "/api/tools" in openapi_schema["paths"], "Tools endpoint not found in OpenAPI schema"
        
        print("MCP server API endpoints check passed")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Error connecting to MCP server API: {str(e)}")
    except Exception as e:
        pytest.fail(f"Error checking MCP server API endpoints: {str(e)}")

def test_docker_network_connection():
    """Test Docker network connection between Django client and MCP server."""
    print("\n=== Testing Docker network connection ===")
    
    try:
        # Run a command in the Django client container to ping the MCP server container
        ping_cmd = "docker exec picard_mcp-django_client ping -c 3 mcp_server"
        print(f"Running ping command: {ping_cmd}")
        ping_result = os.system(ping_cmd)
        assert ping_result == 0, "Ping from Django client to MCP server failed"
        
        # Run a curl command in the Django client container to check the MCP server health endpoint
        curl_cmd = "docker exec picard_mcp-django_client curl -s http://mcp_server:8000/health"
        print(f"Running curl command: {curl_cmd}")
        curl_result = os.popen(curl_cmd).read()
        print(f"Curl result: {curl_result}")
        
        # Parse the JSON response
        try:
            health_data = json.loads(curl_result)
            assert "status" in health_data, "MCP server health response missing status field"
            assert health_data["status"] == "ok", f"MCP server health status is not ok: {health_data}"
        except json.JSONDecodeError:
            pytest.fail(f"Invalid JSON response from MCP server: {curl_result}")
        
        print("Docker network connection test passed")
    except Exception as e:
        pytest.fail(f"Docker network connection test failed: {str(e)}")

def test_env_variables():
    """Test that environment variables are correctly set in the Django client."""
    print("\n=== Testing environment variables ===")
    
    try:
        # Run a command in the Django client container to check environment variables
        env_cmd = "docker exec picard_mcp-django_client env | grep MCP"
        print(f"Running env command: {env_cmd}")
        env_result = os.popen(env_cmd).read()
        print(f"Environment variables: {env_result}")
        
        # Check for MCP_SERVER_URL
        assert "MCP_SERVER_URL=http://mcp_server:8000" in env_result, "MCP_SERVER_URL not set correctly in Django client"
        
        # Check for MCP_SERVER_INTERNAL_URL
        assert "MCP_SERVER_INTERNAL_URL=http://mcp_server:8000" in env_result, "MCP_SERVER_INTERNAL_URL not set correctly in Django client"
        
        print("Environment variables test passed")
    except Exception as e:
        pytest.fail(f"Environment variables test failed: {str(e)}")

def test_django_settings():
    """Test that Django settings are correctly configured."""
    print("\n=== Testing Django settings ===")
    
    try:
        # Run a command in the Django client container to check Django settings
        settings_cmd = "docker exec picard_mcp-django_client python manage.py shell -c \"from django.conf import settings; print('MCP_SERVER_URL =', settings.MCP_SERVER_URL); print('MCP_SERVER_INTERNAL_URL =', settings.MCP_SERVER_INTERNAL_URL)\""
        print(f"Running settings command: {settings_cmd}")
        settings_result = os.popen(settings_cmd).read()
        print(f"Django settings: {settings_result}")
        
        # Check for MCP_SERVER_URL
        assert "MCP_SERVER_URL = http://mcp_server:8000" in settings_result, "MCP_SERVER_URL not set correctly in Django settings"
        
        # Check for MCP_SERVER_INTERNAL_URL
        assert "MCP_SERVER_INTERNAL_URL = http://mcp_server:8000" in settings_result, "MCP_SERVER_INTERNAL_URL not set correctly in Django settings"
        
        print("Django settings test passed")
    except Exception as e:
        pytest.fail(f"Django settings test failed: {str(e)}")

if __name__ == "__main__":
    # This allows running the tests directly with python
    test_mcp_server_health()
    test_django_client_health()
    test_direct_api_connection()
    test_mcp_server_api_endpoints()
    test_docker_network_connection()
    test_env_variables()
    test_django_settings()
    print("\nAll API connection tests completed successfully!")
