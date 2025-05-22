"""
Tests for the OAuth permission system.
"""
import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User
from app.models.oauth import OAuthClient, Token
from app.middleware.oauth import require_scopes
from app.utils.oauth import create_access_token
from app.db.session import get_db

client = TestClient(app)

@pytest.fixture
def db():
    """Get a database session for testing."""
    db = next(get_db())
    yield db
    db.close()

@pytest.fixture
def test_user(db):
    """Create a test user."""
    user = User(
        id=uuid.uuid4(),
        username="test_user",
        email="test@example.com",
        hashed_password="hashed_password",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def oauth_client(db):
    """Create a test OAuth client."""
    client = OAuthClient(
        id=uuid.uuid4(),
        client_id=uuid.uuid4(),
        client_secret="test_secret",
        client_name="Test Client",
        redirect_uris=["http://localhost:8000/callback"],
        scopes=["memories:read", "memories:write", "profile:read"],
        is_confidential=True
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client

@pytest.fixture
def access_token_with_read_scope(db, test_user, oauth_client):
    """Create an access token with memories:read scope."""
    access_token, refresh_token, _ = create_access_token(
        db=db,
        client_id=oauth_client.client_id,
        user_id=test_user.id,
        scope="memories:read"
    )
    return access_token

@pytest.fixture
def access_token_with_write_scope(db, test_user, oauth_client):
    """Create an access token with memories:write scope."""
    access_token, refresh_token, _ = create_access_token(
        db=db,
        client_id=oauth_client.client_id,
        user_id=test_user.id,
        scope="memories:write"
    )
    return access_token

@pytest.fixture
def access_token_with_multiple_scopes(db, test_user, oauth_client):
    """Create an access token with multiple scopes."""
    access_token, refresh_token, _ = create_access_token(
        db=db,
        client_id=oauth_client.client_id,
        user_id=test_user.id,
        scope="memories:read memories:write profile:read"
    )
    return access_token

def test_access_with_correct_scope(access_token_with_read_scope):
    """Test accessing an endpoint with the correct scope."""
    response = client.get(
        "/api/v1/memories/",
        headers={"Authorization": f"Bearer {access_token_with_read_scope}"}
    )
    assert response.status_code == 200
    assert "memories" in response.json()

def test_access_denied_with_wrong_scope(access_token_with_write_scope):
    """Test accessing an endpoint with the wrong scope."""
    # The memories GET endpoint requires memories:read, but we're using a token with memories:write
    response = client.get(
        "/api/v1/memories/",
        headers={"Authorization": f"Bearer {access_token_with_write_scope}"}
    )
    assert response.status_code == 403
    assert response.json()["error"] == "insufficient_scope"

def test_access_with_multiple_scopes(access_token_with_multiple_scopes):
    """Test accessing endpoints with a token that has multiple scopes."""
    # Test GET endpoint (requires memories:read)
    response = client.get(
        "/api/v1/memories/",
        headers={"Authorization": f"Bearer {access_token_with_multiple_scopes}"}
    )
    assert response.status_code == 200
    
    # Test POST endpoint (requires memories:write)
    response = client.post(
        "/api/v1/memories/",
        json={"memory_content": "Test memory"},
        headers={"Authorization": f"Bearer {access_token_with_multiple_scopes}"}
    )
    assert response.status_code == 201

def test_access_without_token():
    """Test accessing a protected endpoint without a token."""
    response = client.get("/api/v1/memories/")
    assert response.status_code == 401
    assert response.json()["error"] == "unauthorized"

def test_token_revocation(db, access_token_with_read_scope):
    """Test revoking a token."""
    # First, verify the token works
    response = client.get(
        "/api/v1/memories/",
        headers={"Authorization": f"Bearer {access_token_with_read_scope}"}
    )
    assert response.status_code == 200
    
    # Revoke the token
    response = client.post(
        "/api/v1/tokens/revoke",
        json={"token": access_token_with_read_scope},
        headers={"Authorization": f"Bearer {access_token_with_read_scope}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Token revoked successfully"
    
    # Try to use the revoked token
    response = client.get(
        "/api/v1/memories/",
        headers={"Authorization": f"Bearer {access_token_with_read_scope}"}
    )
    assert response.status_code == 401
    assert response.json()["error"] == "unauthorized"

def test_token_introspection(access_token_with_multiple_scopes):
    """Test token introspection endpoint."""
    response = client.post(
        "/api/v1/tokens/introspect",
        json={"token": access_token_with_multiple_scopes},
        headers={"Authorization": f"Bearer {access_token_with_multiple_scopes}"}
    )
    assert response.status_code == 200
    assert response.json()["active"] is True
    assert "memories:read" in response.json()["scope"]
    assert "memories:write" in response.json()["scope"]
    assert "profile:read" in response.json()["scope"]
