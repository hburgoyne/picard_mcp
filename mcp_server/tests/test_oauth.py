"""
Tests for the OAuth 2.0 API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.oauth import OAuthClient, AuthorizationCode, Token
from app.models.user import User
from app.utils.oauth import create_authorization_code, create_access_token
from app.utils.admin import verify_admin_credentials
import uuid
import secrets
import hashlib
import base64

client = TestClient(app)

@pytest.fixture
def admin_user(db_session: Session):
    """Create an admin user for testing."""
    # Check if admin user exists
    admin = db_session.query(User).filter(User.username == "testadmin").first()
    if admin:
        return admin
    
    # Create admin user
    password_hash = hashlib.sha256("testpassword".encode()).hexdigest()
    admin = User(
        username="testadmin",
        email="testadmin@example.com",
        hashed_password=password_hash,
        is_active=True,
        is_superuser=True
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin

@pytest.fixture
def admin_auth_header():
    """Create an auth header for admin authentication."""
    credentials = base64.b64encode(b"testadmin:testpassword").decode("utf-8")
    return {"Authorization": f"Basic {credentials}"}

@pytest.fixture
def non_admin_user(db_session: Session):
    """Create a non-admin user for testing."""
    # Check if user exists
    user = db_session.query(User).filter(User.username == "testuser").first()
    if user:
        return user
    
    # Create user
    password_hash = hashlib.sha256("userpassword".encode()).hexdigest()
    user = User(
        username="testuser",
        email="testuser@example.com",
        hashed_password=password_hash,
        is_active=True,
        is_superuser=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def non_admin_auth_header():
    """Create an auth header for non-admin authentication."""
    credentials = base64.b64encode(b"testuser:userpassword").decode("utf-8")
    return {"Authorization": f"Basic {credentials}"}

def test_register_client(db_session: Session, override_get_db):
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
    db_client = db_session.query(OAuthClient).filter(OAuthClient.client_id == uuid.UUID(data["client_id"])).first()
    assert db_client is not None
    assert db_client.client_name == client_data["client_name"]

def test_authorize_endpoint(db_session: Session, override_get_db):
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
    db_session.add(test_client)
    db_session.commit()
    
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
    
    # Create test user
    test_user = User(
        email="test_auth@example.com",
        username="test_auth_user",
        hashed_password="test_password"
    )
    db_session.add(test_user)
    db_session.commit()
    
    # Add user_id to auth params
    auth_params["user_id"] = str(test_user.id)
    
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
    db_code = db_session.query(AuthorizationCode).filter(AuthorizationCode.code == code).first()
    assert db_code is not None
    assert db_code.client_id == test_client.id
    assert db_code.redirect_uri == redirect_uri

def test_token_endpoint(db_session: Session, override_get_db):
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
    db_session.add(test_client)
    db_session.commit()
    
    # Create test user
    test_user = User(
        email="test_oauth@example.com",
        username="test_oauth_user",
        hashed_password="test_password"
    )
    db_session.add(test_user)
    db_session.commit()
    
    user_id = test_user.id
    
    # Create code verifier and code challenge for PKCE
    code_verifier = "test_verifier_for_oauth_endpoint_test"
    hash_object = hashlib.sha256(code_verifier.encode())
    code_challenge = base64.urlsafe_b64encode(hash_object.digest()).decode().rstrip("=")
    
    # Create authorization code
    code = create_authorization_code(
        db=db_session,
        client_id=test_client.id,
        user_id=user_id,
        redirect_uri=redirect_uri,
        scope="memories:read",
        code_challenge=code_challenge,
        code_challenge_method="S256"
    )
    
    # Request token
    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": str(client_id),
        "client_secret": client_secret,
        "code_verifier": code_verifier
    }
    
    response = client.post("/api/oauth/token", data=token_data)
    
    # Print response content for debugging
    print(f"Response status: {response.status_code}")
    print(f"Response content: {response.json()}")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert "expires_in" in data
    assert "scope" in data
    
    # Verify token exists in database
    db_token = db_session.query(Token).filter(Token.access_token == data["access_token"]).first()
    assert db_token is not None
    assert db_token.client_id == test_client.id
    assert db_token.user_id == user_id
    assert db_token.scope == "memories:read"


def test_admin_list_oauth_clients(db_session: Session, override_get_db, admin_user, admin_auth_header):
    """Test listing OAuth clients as admin."""
    # Create test clients
    client1 = OAuthClient(
        client_id=uuid.uuid4(),
        client_secret=secrets.token_urlsafe(32),
        client_name="Admin Test Client 1",
        redirect_uris=["http://localhost/callback1"],
        scopes=["memories:read"]
    )
    client2 = OAuthClient(
        client_id=uuid.uuid4(),
        client_secret=secrets.token_urlsafe(32),
        client_name="Admin Test Client 2",
        redirect_uris=["http://localhost/callback2"],
        scopes=["memories:write"]
    )
    db_session.add_all([client1, client2])
    db_session.commit()
    
    # Test listing clients
    response = client.get("/api/admin/clients", headers=admin_auth_header)
    
    assert response.status_code == 200
    clients = response.json()
    assert isinstance(clients, list)
    assert len(clients) >= 2
    
    # Check that our test clients are in the list
    client_ids = [c["client_id"] for c in clients]
    assert str(client1.client_id) in client_ids
    assert str(client2.client_id) in client_ids


def test_admin_get_oauth_client(db_session: Session, override_get_db, admin_user, admin_auth_header):
    """Test getting a specific OAuth client as admin."""
    # Create test client
    client_id = uuid.uuid4()
    test_client = OAuthClient(
        client_id=client_id,
        client_secret=secrets.token_urlsafe(32),
        client_name="Admin Get Test Client",
        redirect_uris=["http://localhost/callback"],
        scopes=["memories:read", "memories:write"]
    )
    db_session.add(test_client)
    db_session.commit()
    
    # Test getting client
    response = client.get(f"/api/admin/clients/{client_id}", headers=admin_auth_header)
    
    assert response.status_code == 200
    client_data = response.json()
    assert client_data["client_id"] == str(client_id)
    assert client_data["client_name"] == "Admin Get Test Client"
    assert client_data["redirect_uris"] == ["http://localhost/callback"]
    assert client_data["scopes"] == ["memories:read", "memories:write"]


def test_admin_update_oauth_client(db_session: Session, override_get_db, admin_user, admin_auth_header):
    """Test updating an OAuth client as admin."""
    # Create test client
    client_id = uuid.uuid4()
    test_client = OAuthClient(
        client_id=client_id,
        client_secret=secrets.token_urlsafe(32),
        client_name="Admin Update Test Client",
        redirect_uris=["http://localhost/callback"],
        scopes=["memories:read"]
    )
    db_session.add(test_client)
    db_session.commit()
    
    # Update data
    update_data = {
        "client_name": "Updated Client Name",
        "redirect_uris": ["http://localhost/new-callback"],
        "scopes": ["memories:read", "memories:write"],
        "is_confidential": True
    }
    
    # Test updating client
    response = client.put(
        f"/api/admin/clients/{client_id}",
        headers=admin_auth_header,
        json=update_data
    )
    
    assert response.status_code == 200
    client_data = response.json()
    assert client_data["client_name"] == "Updated Client Name"
    assert client_data["redirect_uris"] == ["http://localhost/new-callback"]
    assert client_data["scopes"] == ["memories:read", "memories:write"]
    
    # Verify in database
    updated_client = db_session.query(OAuthClient).filter(OAuthClient.client_id == client_id).first()
    assert updated_client.client_name == "Updated Client Name"
    assert updated_client.redirect_uris == ["http://localhost/new-callback"]
    assert updated_client.scopes == ["memories:read", "memories:write"]


def test_admin_delete_oauth_client(db_session: Session, override_get_db, admin_user, admin_auth_header):
    """Test deleting an OAuth client as admin."""
    # Create test client
    client_id = uuid.uuid4()
    test_client = OAuthClient(
        client_id=client_id,
        client_secret=secrets.token_urlsafe(32),
        client_name="Admin Delete Test Client",
        redirect_uris=["http://localhost/callback"],
        scopes=["memories:read"]
    )
    db_session.add(test_client)
    db_session.commit()
    
    # Test deleting client
    response = client.delete(f"/api/admin/clients/{client_id}", headers=admin_auth_header)
    
    assert response.status_code == 204
    
    # Verify client is deleted
    deleted_client = db_session.query(OAuthClient).filter(OAuthClient.client_id == client_id).first()
    assert deleted_client is None


def test_admin_unauthorized_access(db_session: Session, override_get_db):
    """Test that admin endpoints require authentication."""
    # No auth header
    response = client.get("/api/admin/clients")
    assert response.status_code == 401
    
    # Invalid credentials
    invalid_credentials = base64.b64encode(b"invalid:credentials").decode("utf-8")
    headers = {"Authorization": f"Basic {invalid_credentials}"}
    response = client.get("/api/admin/clients", headers=headers)
    assert response.status_code == 401


def test_admin_non_admin_access(db_session: Session, override_get_db, non_admin_user, non_admin_auth_header):
    """Test that non-admin users cannot access admin endpoints."""
    response = client.get("/api/admin/clients", headers=non_admin_auth_header)
    assert response.status_code == 403  # Forbidden
