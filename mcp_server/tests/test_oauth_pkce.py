"""
Tests for the OAuth 2.0 PKCE flow and token management.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import base64
import hashlib
import secrets
import uuid
from urllib.parse import parse_qs, urlparse

from app.main import app
from app.models.oauth import OAuthClient, AuthorizationCode, Token
from app.models.user import User
from app.utils.oauth import create_authorization_code, create_access_token

client = TestClient(app)

@pytest.fixture
def test_user(db_session: Session):
    """Create a test user for OAuth flow testing."""
    # Check if test user exists
    test_user = db_session.query(User).filter(User.username == "testuser").first()
    if test_user:
        return test_user
    
    # Create test user
    from app.utils.security import get_password_hash
    test_user = User(
        id=uuid.uuid4(),
        username="testuser",
        email="testuser@example.com",
        hashed_password=get_password_hash("testpassword"),
        is_active=True,
        is_superuser=False
    )
    db_session.add(test_user)
    db_session.commit()
    db_session.refresh(test_user)
    return test_user

@pytest.fixture
def test_oauth_client(db_session: Session):
    """Create a test OAuth client for testing."""
    # Generate a unique client name for this test run to avoid conflicts
    unique_suffix = secrets.token_hex(4)
    client_name = f"Test PKCE Client {unique_suffix}"
    
    # Check if a client with this name already exists and delete it
    existing_client = db_session.query(OAuthClient).filter(OAuthClient.client_name == client_name).first()
    if existing_client:
        db_session.delete(existing_client)
        db_session.commit()
    
    # Create a test client
    client_id = uuid.uuid4()
    client_secret = secrets.token_urlsafe(32)
    redirect_uri = "http://localhost:8000/oauth/callback/"
    
    test_client = OAuthClient(
        client_id=client_id,
        client_secret=client_secret,
        client_name=client_name,
        redirect_uris=[redirect_uri],
        scopes=["memories:read", "memories:write"],
        is_confidential=True
    )
    db_session.add(test_client)
    db_session.commit()
    
    # Verify the client was added correctly
    added_client = db_session.query(OAuthClient).filter(OAuthClient.client_id == client_id).first()
    assert added_client is not None
    assert added_client.client_name == client_name
    
    # Return the client information
    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "client_name": client_name
    }

@pytest.fixture
def pkce_params():
    """Generate PKCE code verifier and challenge."""
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().rstrip("=")
    
    return {
        "code_verifier": code_verifier,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256"
    }

def test_authorize_with_pkce(db_session: Session, override_get_db, test_user, test_oauth_client, pkce_params, monkeypatch):
    """Test authorization endpoint with PKCE."""
    # Mock the get_current_user function to return our test user
    from app.utils import auth
    monkeypatch.setattr(auth, "get_current_user", lambda *args, **kwargs: test_user)
    
    # First, clean up any existing authorization codes for this client and user
    db_session.query(AuthorizationCode).filter(
        AuthorizationCode.client_id == test_oauth_client["client_id"],
        AuthorizationCode.user_id == test_user.id
    ).delete()
    db_session.commit()
    
    # Prepare authorization request with PKCE
    params = {
        "response_type": "code",
        "client_id": str(test_oauth_client["client_id"]),
        "redirect_uri": test_oauth_client["redirect_uri"],
        "scope": "memories:read memories:write",
        "state": "test_state",
        "code_challenge": pkce_params["code_challenge"],
        "code_challenge_method": pkce_params["code_challenge_method"]
    }
    
    # Make the authorization request
    response = client.get("/api/oauth/authorize", params=params)
    
    # Should return 200 with the consent page
    assert response.status_code == 200
    assert "consent.html" in response.template.name
    assert test_oauth_client["client_name"] in response.text
    
    # Now simulate the user approving the consent
    consent_data = {
        "client_id": str(test_oauth_client["client_id"]),
        "redirect_uri": test_oauth_client["redirect_uri"],
        "scope": "memories:read memories:write",
        "state": "test_state",
        "response_type": "code",
        "decision": "approve",
        "code_challenge": pkce_params["code_challenge"],
        "code_challenge_method": pkce_params["code_challenge_method"]
    }
    
    response = client.post("/api/oauth/consent", data=consent_data, allow_redirects=False)
    
    # Should redirect back to client with code
    assert response.status_code == 302
    redirect_url = response.headers["location"]
    assert test_oauth_client["redirect_uri"] in redirect_url
    
    # Extract the authorization code from the redirect URL
    parsed_url = urlparse(redirect_url)
    query_params = parse_qs(parsed_url.query)
    assert "code" in query_params
    assert query_params["state"][0] == "test_state"
    
    auth_code = query_params["code"][0]
    
    # Verify the authorization code exists in the database
    db_auth_code = db_session.query(AuthorizationCode).filter(
        AuthorizationCode.code == auth_code
    ).first()
    
    assert db_auth_code is not None
    
    # Get the client associated with this authorization code
    auth_code_client = db_session.query(OAuthClient).filter(
        OAuthClient.id == db_auth_code.client_id
    ).first()
    
    assert auth_code_client is not None
    
    # Print debug information
    print(f"Auth code client_id: {auth_code_client.client_id}")
    print(f"Test client_id: {test_oauth_client['client_id']}")
    print(f"Auth code client name: {auth_code_client.client_name}")
    print(f"Test client name: {test_oauth_client['client_name']}")
    
    # Verify the client associated with the auth code is the same one we created
    assert str(auth_code_client.client_id) == str(test_oauth_client["client_id"])
    assert auth_code_client.client_name == test_oauth_client["client_name"]
    
    assert db_auth_code.user_id == test_user.id
    assert db_auth_code.code_challenge == pkce_params["code_challenge"]
    assert db_auth_code.code_challenge_method == pkce_params["code_challenge_method"]
    
    return auth_code, pkce_params["code_verifier"]

def test_token_exchange_with_pkce(db_session: Session, override_get_db, test_user, test_oauth_client, pkce_params, monkeypatch):
    """Test token exchange with PKCE code verifier."""
    # First, clean up any existing tokens for this client and user
    db_session.query(Token).filter(
        Token.client_id == test_oauth_client["client_id"],
        Token.user_id == test_user.id
    ).delete()
    db_session.commit()
    
    # First get an authorization code
    auth_code, code_verifier = test_authorize_with_pkce(
        db_session, override_get_db, test_user, test_oauth_client, pkce_params, monkeypatch
    )
    
    # Now exchange it for a token with the code verifier
    token_data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": test_oauth_client["redirect_uri"],
        "client_id": str(test_oauth_client["client_id"]),
        "client_secret": test_oauth_client["client_secret"],
        "code_verifier": code_verifier
    }
    
    response = client.post("/api/oauth/token", data=token_data)
    
    # Should return 200 with tokens
    assert response.status_code == 200
    token_response = response.json()
    
    assert "access_token" in token_response
    assert "refresh_token" in token_response
    assert "expires_in" in token_response
    assert token_response["token_type"] == "bearer"
    
    # Verify tokens exist in the database
    db_token = db_session.query(Token).filter(
        Token.access_token == token_response["access_token"]
    ).first()
    
    assert db_token is not None
    
    # Get the client associated with this token
    token_client = db_session.query(OAuthClient).filter(
        OAuthClient.id == db_token.client_id
    ).first()
    
    assert token_client is not None
    
    # Print debug information
    print(f"Token client_id: {token_client.client_id}")
    print(f"Test client_id: {test_oauth_client['client_id']}")
    print(f"Token client name: {token_client.client_name}")
    print(f"Test client name: {test_oauth_client['client_name']}")
    
    # Verify the client associated with the token is the same one we created
    assert str(token_client.client_id) == str(test_oauth_client["client_id"])
    assert token_client.client_name == test_oauth_client["client_name"]
    
    assert db_token.user_id == test_user.id
    assert db_token.refresh_token == token_response["refresh_token"]
    
    # Authorization code should be deleted after use
    db_auth_code = db_session.query(AuthorizationCode).filter(
        AuthorizationCode.code == auth_code
    ).first()
    assert db_auth_code is None
    
    return token_response

def test_token_exchange_without_code_verifier(db_session: Session, override_get_db, test_user, test_oauth_client, pkce_params, monkeypatch):
    """Test token exchange fails without PKCE code verifier."""
    # Mock the get_current_user function to return our test user
    from app.utils import auth
    monkeypatch.setattr(auth, "get_current_user", lambda *args, **kwargs: test_user)
    
    # First, clean up any existing authorization codes for this client and user
    db_session.query(AuthorizationCode).filter(
        AuthorizationCode.client_id == test_oauth_client["client_id"],
        AuthorizationCode.user_id == test_user.id
    ).delete()
    db_session.commit()
    
    # First get an authorization code with PKCE
    # Prepare authorization request with PKCE
    params = {
        "response_type": "code",
        "client_id": str(test_oauth_client["client_id"]),
        "redirect_uri": test_oauth_client["redirect_uri"],
        "scope": "memories:read memories:write",
        "state": "test_state",
        "code_challenge": pkce_params["code_challenge"],
        "code_challenge_method": pkce_params["code_challenge_method"]
    }
    
    # Make the authorization request
    response = client.get("/api/oauth/authorize", params=params)
    
    # Simulate the user approving the consent
    consent_data = {
        "client_id": str(test_oauth_client["client_id"]),
        "redirect_uri": test_oauth_client["redirect_uri"],
        "scope": "memories:read memories:write",
        "state": "test_state",
        "response_type": "code",
        "decision": "approve",
        "code_challenge": pkce_params["code_challenge"],
        "code_challenge_method": pkce_params["code_challenge_method"]
    }
    
    response = client.post("/api/oauth/consent", data=consent_data, allow_redirects=False)
    
    # Extract the authorization code from the redirect URL
    redirect_url = response.headers["location"]
    parsed_url = urlparse(redirect_url)
    query_params = parse_qs(parsed_url.query)
    auth_code = query_params["code"][0]
    
    # Verify the authorization code exists in the database
    db_auth_code = db_session.query(AuthorizationCode).filter(
        AuthorizationCode.code == auth_code
    ).first()
    
    assert db_auth_code is not None
    
    # Get the client associated with this authorization code
    auth_code_client = db_session.query(OAuthClient).filter(
        OAuthClient.id == db_auth_code.client_id
    ).first()
    
    assert auth_code_client is not None
    
    # Verify the client associated with the auth code is the same one we created
    assert str(auth_code_client.client_id) == str(test_oauth_client["client_id"])
    assert auth_code_client.client_name == test_oauth_client["client_name"]
    
    # Now try to exchange it for a token WITHOUT the code verifier
    token_data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": test_oauth_client["redirect_uri"],
        "client_id": str(test_oauth_client["client_id"]),
        "client_secret": test_oauth_client["client_secret"]
        # Intentionally omitting code_verifier
    }
    
    response = client.post("/api/oauth/token", data=token_data)
    
    # Should return 400 Bad Request
    assert response.status_code == 400
    error_response = response.json()
    
    assert "error" in error_response
    assert error_response["error"] == "invalid_request"
    assert "code verifier" in error_response["error_description"].lower()

def test_refresh_token(db_session: Session, override_get_db, test_user, test_oauth_client, pkce_params, monkeypatch):
    """Test refresh token flow."""
    # First, clean up any existing tokens for this client and user
    db_session.query(Token).filter(
        Token.client_id == test_oauth_client["client_id"],
        Token.user_id == test_user.id
    ).delete()
    db_session.commit()
    
    # First get tokens
    token_response = test_token_exchange_with_pkce(
        db_session, override_get_db, test_user, test_oauth_client, pkce_params, monkeypatch
    )
    
    refresh_token = token_response["refresh_token"]
    
    # Verify the original token exists in the database
    original_token = db_session.query(Token).filter(
        Token.refresh_token == refresh_token
    ).first()
    
    assert original_token is not None
    
    # Get the client associated with this token
    original_token_client = db_session.query(OAuthClient).filter(
        OAuthClient.id == original_token.client_id
    ).first()
    
    assert original_token_client is not None
    
    # Verify the client associated with the token is the same one we created
    assert str(original_token_client.client_id) == str(test_oauth_client["client_id"])
    assert original_token_client.client_name == test_oauth_client["client_name"]
    assert original_token.user_id == test_user.id
    
    # Now use the refresh token to get new tokens
    refresh_data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": str(test_oauth_client["client_id"]),
        "client_secret": test_oauth_client["client_secret"]
    }
    
    response = client.post("/api/oauth/token", data=refresh_data)
    
    # Should return 200 with new tokens
    assert response.status_code == 200
    new_token_response = response.json()
    
    assert "access_token" in new_token_response
    assert "refresh_token" in new_token_response
    assert new_token_response["access_token"] != token_response["access_token"]
    assert new_token_response["refresh_token"] != token_response["refresh_token"]
    
    # Verify new tokens exist in the database
    db_token = db_session.query(Token).filter(
        Token.access_token == new_token_response["access_token"]
    ).first()
    
    assert db_token is not None
    
    # Get the client associated with this token
    token_client = db_session.query(OAuthClient).filter(
        OAuthClient.id == db_token.client_id
    ).first()
    
    assert token_client is not None
    
    # Print debug information
    print(f"Token client_id: {token_client.client_id}")
    print(f"Test client_id: {test_oauth_client['client_id']}")
    print(f"Token client name: {token_client.client_name}")
    print(f"Test client name: {test_oauth_client['client_name']}")
    
    # Verify the client associated with the token is the same one we created
    assert str(token_client.client_id) == str(test_oauth_client["client_id"])
    assert token_client.client_name == test_oauth_client["client_name"]
    assert db_token.user_id == test_user.id
    assert db_token.refresh_token == new_token_response["refresh_token"]
    
    # Old refresh token should no longer be valid
    old_refresh_data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": str(test_oauth_client["client_id"]),
        "client_secret": test_oauth_client["client_secret"]
    }
    
    response = client.post("/api/oauth/token", data=old_refresh_data)
    
    # Should return 400 Bad Request
    assert response.status_code == 400
    error_response = response.json()
    
    assert "error" in error_response
    assert error_response["error"] == "invalid_grant"
