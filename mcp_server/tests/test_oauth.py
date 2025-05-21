import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_client_registration(client: TestClient):
    """Test OAuth client registration."""
    client_data = {
        "client_name": "Test Client",
        "redirect_uris": "http://localhost:8000/callback",
        "grant_types": "authorization_code refresh_token",
        "response_types": "code",
        "scopes": "memories:read memories:write",
        "client_uri": "http://localhost:8000",
        "logo_uri": "http://localhost:8000/logo.png",
        "tos_uri": "http://localhost:8000/tos",
        "policy_uri": "http://localhost:8000/policy",
        "jwks_uri": "http://localhost:8000/jwks",
        "software_id": "test-client",
        "software_version": "1.0.0"
    }
    
    response = client.post("/oauth/register", json=client_data)
    assert response.status_code == 201
    data = response.json()
    assert "client_id" in data
    assert "client_secret" in data
    assert "client_id_issued_at" in data
    assert "client_secret_expires_at" in data
    
    # Store client credentials for other tests
    return data["client_id"], data["client_secret"]

@pytest.mark.asyncio
async def test_authorization_endpoint(client: TestClient):
    """Test OAuth authorization endpoint."""
    # First register a client
    client_id, _ = await test_client_registration(client)
    
    # Test authorization endpoint
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": "http://localhost:8000/callback",
        "scope": "memories:read memories:write",
        "state": "test_state"
    }
    
    response = client.get("/oauth/authorize", params=params, allow_redirects=False)
    assert response.status_code == 307  # Temporary redirect
    
    # Check that the redirect URL contains the authorization code
    location = response.headers["Location"]
    assert "code=" in location
    assert "state=test_state" in location

@pytest.mark.asyncio
async def test_token_endpoint(client: TestClient):
    """Test OAuth token endpoint."""
    # First register a client
    client_id, client_secret = await test_client_registration(client)
    
    # Get an authorization code
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": "http://localhost:8000/callback",
        "scope": "memories:read memories:write",
        "state": "test_state"
    }
    
    response = client.get("/oauth/authorize", params=params, allow_redirects=False)
    location = response.headers["Location"]
    code = location.split("code=")[1].split("&")[0]
    
    # Exchange the code for a token
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": "http://localhost:8000/callback"
    }
    
    response = client.post("/oauth/token", data=data)
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert "token_type" in token_data
    assert "expires_in" in token_data
    assert "refresh_token" in token_data
    assert "scope" in token_data
    
    # Test userinfo endpoint
    headers = {
        "Authorization": f"Bearer {token_data['access_token']}"
    }
    
    response = client.get("/oauth/userinfo", headers=headers)
    assert response.status_code == 200
    user_data = response.json()
    assert "sub" in user_data
    assert "username" in user_data
    assert "email" in user_data
