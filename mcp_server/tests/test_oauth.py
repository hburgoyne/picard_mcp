"""
Tests for the OAuth 2.0 API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.oauth import OAuthClient, AuthorizationCode, Token
from app.utils.oauth import create_authorization_code, create_access_token
import uuid
import secrets

client = TestClient(app)

def test_register_client(db: Session):
    """Test OAuth client registration."""
    client_data = {
        "client_name": "Test Client",
        "redirect_uris": ["http://localhost/callback"],
        "scopes": ["memories:read", "memories:write"],
        "is_confidential": True
    }
    
    response = client.post("/api/oauth/register", json=client_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "client_id" in data
    assert "client_secret" in data
    assert data["client_name"] == client_data["client_name"]
    assert data["redirect_uris"] == client_data["redirect_uris"]
    assert data["scopes"] == client_data["scopes"]
    assert data["is_confidential"] == client_data["is_confidential"]
    
    # Verify client was saved in database
    db_client = db.query(OAuthClient).filter(OAuthClient.client_id == uuid.UUID(data["client_id"])).first()
    assert db_client is not None
    assert db_client.client_name == client_data["client_name"]

def test_authorize_endpoint(db: Session):
    """Test authorization endpoint."""
    # Create a test client first
    client_id = uuid.uuid4()
    client_secret = secrets.token_urlsafe(32)
    redirect_uri = "http://localhost/callback"
    
    test_client = OAuthClient(
        client_id=client_id,
        client_secret=client_secret,
        client_name="Test Auth Client",
        redirect_uris=[redirect_uri],
        scopes=["memories:read", "memories:write"]
    )
    db.add(test_client)
    db.commit()
    
    # Create authorization request
    auth_params = {
        "response_type": "code",
        "client_id": str(client_id),
        "redirect_uri": redirect_uri,
        "scope": "memories:read",
        "state": "test_state",
        "code_challenge": "test_challenge",
        "code_challenge_method": "S256"
    }
    
    # Make request to authorize endpoint
    response = client.get("/api/oauth/authorize", params=auth_params, allow_redirects=False)
    
    # Check for redirect
    assert response.status_code == 302
    location = response.headers["Location"]
    
    # Check redirect contains code and state
    assert "code=" in location
    assert "state=test_state" in location
    
    # Extract code from redirect URI
    import urllib.parse
    parsed = urllib.parse.urlparse(location)
    query = urllib.parse.parse_qs(parsed.query)
    code = query["code"][0]
    
    # Verify code exists in database
    db_code = db.query(AuthorizationCode).filter(AuthorizationCode.code == code).first()
    assert db_code is not None
    assert db_code.client_id == test_client.id
    assert db_code.redirect_uri == redirect_uri

def test_token_endpoint(db: Session):
    """Test token exchange endpoint."""
    # Create a test client
    client_id = uuid.uuid4()
    client_secret = secrets.token_urlsafe(32)
    redirect_uri = "http://localhost/callback"
    
    test_client = OAuthClient(
        client_id=client_id,
        client_secret=client_secret,
        client_name="Test Token Client",
        redirect_uris=[redirect_uri],
        scopes=["memories:read", "memories:write"]
    )
    db.add(test_client)
    db.commit()
    
    # Create test user
    user_id = uuid.uuid4()
    
    # Create authorization code
    code = create_authorization_code(
        db=db,
        client_id=test_client.id,
        user_id=user_id,
        redirect_uri=redirect_uri,
        scope="memories:read",
        code_challenge="test_challenge",
        code_challenge_method="S256"
    )
    
    # Request token
    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": str(client_id),
        "client_secret": client_secret,
        "code_verifier": "test_verifier"
    }
    
    response = client.post("/api/oauth/token", data=token_data)
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert "expires_in" in data
    assert "scope" in data
    
    # Verify token exists in database
    db_token = db.query(Token).filter(Token.access_token == data["access_token"]).first()
    assert db_token is not None
    assert db_token.client_id == test_client.id
    assert db_token.user_id == user_id
    assert db_token.scope == "memories:read"
