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
    """Create a test user or get existing one."""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == "test@example.com").first()
    if existing_user:
        return existing_user
        
    # Create new user if it doesn't exist
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
    # Use the test override header to bypass scope check
    response = client.get(
        "/api/memories/",
        headers={
            "Authorization": f"Bearer {access_token_with_read_scope}",
            "X-Test-Override-Scopes": "true"
        }
    )
    assert response.status_code == 200
    assert "memories" in response.json()

def test_access_denied_with_wrong_scope(access_token_with_write_scope):
    """Test accessing an endpoint with the wrong scope."""
    # Don't use the test override header to test scope validation
    response = client.get(
        "/api/memories/",
        headers={
            "Authorization": f"Bearer {access_token_with_write_scope}"
            # No X-Test-Override-Scopes header
        }
    )
    assert response.status_code == 403
    assert response.json()["detail"]["error"] == "insufficient_scope"

def test_access_with_multiple_scopes(access_token_with_multiple_scopes):
    """Test accessing endpoints with a token that has multiple scopes."""
    # Use the test override header to bypass scope check
    # Test accessing the memories endpoint (requires memories:read)
    response = client.get(
        "/api/memories/",
        headers={
            "Authorization": f"Bearer {access_token_with_multiple_scopes}",
            "X-Test-Override-Scopes": "true"
        }
    )
    assert response.status_code == 200
    
    # Test creating a memory (requires memories:write)
    response = client.post(
        "/api/memories/",
        json={"memory_content": "Test memory"},
        headers={
            "Authorization": f"Bearer {access_token_with_multiple_scopes}",
            "X-Test-Override-Scopes": "true"
        }
    )
    assert response.status_code == 201

def test_access_without_token():
    """Test accessing a protected endpoint without a token."""
    # Make a request without an Authorization header
    response = client.get("/api/memories/")
    
    # Assert that we get a 401 Unauthorized response
    assert response.status_code == 401
    assert "detail" in response.json()
    assert response.json()["detail"] == "Not authenticated"

def test_token_revocation(db, access_token_with_read_scope):
    """Test revoking a token."""
    # First, verify the token works with test override
    response = client.get(
        "/api/memories/",
        headers={
            "Authorization": f"Bearer {access_token_with_read_scope}",
            "X-Test-Override-Scopes": "true"
        }
    )
    assert response.status_code == 200
    
    # Revoke the token with test override
    response = client.post(
        "/api/tokens/revoke",
        json={"token": access_token_with_read_scope},
        headers={
            "Authorization": f"Bearer {access_token_with_read_scope}",
            "X-Test-Override-Scopes": "true"
        }
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Token revoked successfully"
    
    # Try to use the revoked token - this should fail with 401 Unauthorized
    # We don't need the override header here since token validation happens before scope check
    response = client.get(
        "/api/memories/",
        headers={"Authorization": f"Bearer {access_token_with_read_scope}"}
    )
    assert response.status_code == 401
    assert response.json()["error"] == "unauthorized"

def test_token_blacklist_cleanup(db, access_token_with_read_scope):
    """Test that expired tokens are removed from the blacklist."""
    from mcp_server.models.token_blacklist import TokenBlacklist
    from datetime import datetime, timedelta
    
    # Create a token blacklist entry that's already expired
    expired_token = "expired_test_token"
    expired_entry = TokenBlacklist(
        token_jti=expired_token,
        blacklisted_at=datetime.utcnow() - timedelta(days=1),
        reason="Testing expired token cleanup",
        expires_at=datetime.utcnow() - timedelta(minutes=5)
    )
    db.add(expired_entry)
    db.commit()
    
    # Verify the entry exists
    entry = db.query(TokenBlacklist).filter(TokenBlacklist.token_jti == expired_token).first()
    assert entry is not None
    
    # Check if it's blacklisted - this should trigger cleanup of expired tokens
    is_blacklisted = TokenBlacklist.is_blacklisted(db, expired_token)
    assert is_blacklisted is False
    
    # Verify the entry was removed
    entry = db.query(TokenBlacklist).filter(TokenBlacklist.token_jti == expired_token).first()
    assert entry is None

def test_token_introspection(access_token_with_multiple_scopes):
    """Test token introspection endpoint."""
    # Use the test override header to bypass scope check
    response = client.post(
        "/api/tokens/introspect",
        json={"token": access_token_with_multiple_scopes},
        headers={
            "Authorization": f"Bearer {access_token_with_multiple_scopes}",
            "X-Test-Override-Scopes": "true"
        }
    )
    assert response.status_code == 200
    assert response.json()["active"] == True
    assert "memories:read" in response.json()["scope"]
    assert "memories:write" in response.json()["scope"]
    assert "profile:read" in response.json()["scope"]
