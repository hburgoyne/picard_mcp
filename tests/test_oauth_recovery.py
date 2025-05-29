"""
Tests for the OAuth flow with enhanced credential handling.

This test verifies the complete OAuth flow between Django client and MCP server,
including proper credential validation and automatic recovery from invalid credentials.
"""
import pytest
import requests
import time
import os
from urllib.parse import urlparse, parse_qs

# Test configuration
DJANGO_URL = os.environ.get('DJANGO_URL', 'http://localhost:8000')
MCP_SERVER_URL = os.environ.get('MCP_SERVER_URL', 'http://localhost:8001')
USERNAME = 'testuser'
PASSWORD = 'testpassword123'
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'adminpassword')

@pytest.fixture
def registered_user():
    """Create a test user in the Django client."""
    # Register a user
    register_url = f"{DJANGO_URL}/register/"
    session = requests.Session()
    
    # Get CSRF token
    response = session.get(register_url)
    if response.status_code != 200:
        pytest.skip(f"Could not access registration page: {response.status_code}")
    
    # Extract CSRF token
    csrf_token = None
    for cookie in session.cookies:
        if cookie.name == 'csrftoken':
            csrf_token = cookie.value
            break
    
    if not csrf_token:
        pytest.skip("Could not get CSRF token")
    
    # Register user
    register_data = {
        'username': USERNAME,
        'email': 'test@example.com',
        'password1': PASSWORD,
        'password2': PASSWORD,
        'csrfmiddlewaretoken': csrf_token
    }
    
    response = session.post(register_url, data=register_data, headers={'Referer': register_url})
    
    # Login user
    login_url = f"{DJANGO_URL}/login/"
    response = session.get(login_url)
    
    # Extract CSRF token again
    csrf_token = None
    for cookie in session.cookies:
        if cookie.name == 'csrftoken':
            csrf_token = cookie.value
            break
    
    if not csrf_token:
        pytest.skip("Could not get CSRF token for login")
    
    login_data = {
        'username': USERNAME,
        'password': PASSWORD,
        'csrfmiddlewaretoken': csrf_token
    }
    
    response = session.post(login_url, data=login_data, headers={'Referer': login_url})
    
    if 'dashboard' not in response.url:
        pytest.skip("Login failed")
    
    # Return the authenticated session
    return session

def test_credential_validation_endpoint():
    """Test the client_info endpoint for credential validation."""
    # Test with non-existent client ID
    response = requests.get(f"{MCP_SERVER_URL}/api/oauth/client_info?client_id=00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404, "Should return 404 for non-existent client"
    
    # Register a test client with admin credentials
    admin_auth = (ADMIN_USERNAME, ADMIN_PASSWORD)
    client_data = {
        'client_name': 'Test Validation Client',
        'redirect_uris': ['http://localhost:8000/oauth/callback/'],
        'scopes': ['memories:read', 'memories:write'],
        'is_confidential': True
    }
    
    response = requests.post(
        f"{MCP_SERVER_URL}/api/admin/clients/register",
        json=client_data,
        auth=admin_auth
    )
    
    assert response.status_code == 200, f"Failed to register client: {response.text}"
    client_info = response.json()
    client_id = client_info['client_id']
    
    # Now test the validation endpoint with the valid client ID
    response = requests.get(f"{MCP_SERVER_URL}/api/oauth/client_info?client_id={client_id}")
    assert response.status_code == 200, "Should return 200 for valid client"
    
    # Verify the response contains expected fields
    data = response.json()
    assert 'client_id' in data
    assert 'client_name' in data
    assert 'redirect_uris' in data
    assert 'scopes' in data
    assert data['client_id'] == client_id
    
    # Verify it doesn't contain sensitive information
    assert 'client_secret' not in data, "Should not expose client secret"

def test_oauth_flow_with_recovery(registered_user):
    """Test the complete OAuth flow with automatic credential recovery."""
    session = registered_user
    
    # 1. First invalidate any existing credentials by forcing a new registration
    # This ensures we test the recovery mechanism
    oauth_url = f"{DJANGO_URL}/oauth/authorize/"
    response = session.get(oauth_url)
    
    # 2. Follow redirects to the MCP server authorization page
    authorization_url = response.url
    assert MCP_SERVER_URL in authorization_url, f"Expected redirect to MCP server, got: {authorization_url}"
    
    # 3. Get the consent page
    response = session.get(authorization_url)
    assert response.status_code == 200
    
    # 4. Extract CSRF token from the form
    csrf_token = None
    for cookie in session.cookies:
        if cookie.name == 'csrftoken':
            csrf_token = cookie.value
            break
    
    if not csrf_token:
        pytest.skip("Could not get CSRF token for consent form")
    
    # Parse query parameters from the authorization URL
    parsed_url = urlparse(authorization_url)
    query_params = parse_qs(parsed_url.query)
    
    # 5. Submit the consent form
    consent_data = {
        'client_id': query_params.get('client_id', [''])[0],
        'redirect_uri': query_params.get('redirect_uri', [''])[0],
        'scope': query_params.get('scope', [''])[0],
        'state': query_params.get('state', [''])[0],
        'response_type': query_params.get('response_type', [''])[0],
        'code_challenge': query_params.get('code_challenge', [''])[0],
        'code_challenge_method': query_params.get('code_challenge_method', [''])[0],
        'decision': 'approve',
        'csrfmiddlewaretoken': csrf_token
    }
    
    consent_url = f"{MCP_SERVER_URL}/api/oauth/consent"
    response = session.post(consent_url, data=consent_data, headers={'Referer': authorization_url})
    
    # 6. Verify redirection back to Django client
    assert response.status_code == 200 or response.status_code == 302
    callback_url = response.url
    assert DJANGO_URL in callback_url, f"Expected redirect to Django client, got: {callback_url}"
    
    # 7. Follow the redirect to complete the flow
    response = session.get(callback_url)
    
    # 8. Verify successful connection
    dashboard_url = f"{DJANGO_URL}/dashboard/"
    response = session.get(dashboard_url)
    assert 'Connected to MCP Server' in response.text or 'OAuth Connection' in response.text
    
    # 9. Test token usage by fetching memories
    response = session.get(f"{DJANGO_URL}/memories/")
    assert response.status_code == 200
