"""Tests for the OAuth models."""
import pytest
import uuid
from datetime import datetime, timedelta
from app.models.oauth import OAuthClient, AuthorizationCode, Token
from app.models.user import User


@pytest.fixture(scope="function")
def test_user(db_session):
    """Create a test user for OAuth tests."""
    user = User(
        email="oauth_test@example.com",
        username="oauth_test_user",
        hashed_password="hashed_password"
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture(scope="function")
def test_client(db_session):
    """Create a test OAuth client."""
    client = OAuthClient(
        client_secret="test_client_secret",
        client_name="Test Client",
        redirect_uris=["http://localhost:8000/callback"],
        scopes=["read", "write"]
    )
    db_session.add(client)
    db_session.commit()
    return client


def test_oauth_client_creation(db_session):
    """Test that an OAuth client can be created."""
    client = OAuthClient(
        client_secret="test_client_secret",
        client_name="Test Client",
        redirect_uris=["http://localhost:8000/callback"],
        scopes=["read", "write"]
    )
    db_session.add(client)
    db_session.commit()
    
    # Query the client
    db_client = db_session.query(OAuthClient).filter(
        OAuthClient.client_name == "Test Client"
    ).first()
    
    assert db_client is not None
    assert db_client.client_name == "Test Client"
    assert db_client.client_secret == "test_client_secret"
    assert db_client.redirect_uris == ["http://localhost:8000/callback"]
    assert db_client.scopes == ["read", "write"]
    assert db_client.is_confidential is True
    assert isinstance(db_client.client_id, uuid.UUID)
    assert isinstance(db_client.id, uuid.UUID)


def test_authorization_code_creation(db_session, test_user, test_client):
    """Test that an authorization code can be created."""
    expiration_time = (datetime.utcnow() + timedelta(minutes=10)).isoformat()
    auth_code = AuthorizationCode(
        code="test_auth_code",
        client_id=test_client.id,
        user_id=test_user.id,
        redirect_uri="http://localhost:8000/callback",
        scope="read write",
        expires_at=expiration_time,
        code_challenge="test_challenge",
        code_challenge_method="S256"
    )
    db_session.add(auth_code)
    db_session.commit()
    
    # Query the code
    db_code = db_session.query(AuthorizationCode).filter(
        AuthorizationCode.code == "test_auth_code"
    ).first()
    
    assert db_code is not None
    assert db_code.code == "test_auth_code"
    assert db_code.client_id == test_client.id
    assert db_code.user_id == test_user.id
    assert db_code.redirect_uri == "http://localhost:8000/callback"
    assert db_code.scope == "read write"
    assert db_code.expires_at == expiration_time
    assert db_code.code_challenge == "test_challenge"
    assert db_code.code_challenge_method == "S256"
    assert db_code.is_expired is False


def test_authorization_code_expiration(db_session, test_user, test_client):
    """Test the authorization code expiration property."""
    # Create expired code (10 minutes in the past)
    past_time = (datetime.utcnow() - timedelta(minutes=10)).isoformat()
    expired_code = AuthorizationCode(
        code="expired_code",
        client_id=test_client.id,
        user_id=test_user.id,
        redirect_uri="http://localhost:8000/callback",
        scope="read",
        expires_at=past_time
    )
    db_session.add(expired_code)
    db_session.commit()
    
    # Create valid code (10 minutes in the future)
    future_time = (datetime.utcnow() + timedelta(minutes=10)).isoformat()
    valid_code = AuthorizationCode(
        code="valid_code",
        client_id=test_client.id,
        user_id=test_user.id,
        redirect_uri="http://localhost:8000/callback",
        scope="read",
        expires_at=future_time
    )
    db_session.add(valid_code)
    db_session.commit()
    
    # Test is_expired property
    assert expired_code.is_expired is True
    assert valid_code.is_expired is False


def test_token_creation(db_session, test_user, test_client):
    """Test that a token can be created."""
    access_expires = (datetime.utcnow() + timedelta(hours=1)).isoformat()
    refresh_expires = (datetime.utcnow() + timedelta(days=7)).isoformat()
    
    token = Token(
        access_token="test_access_token",
        refresh_token="test_refresh_token",
        client_id=test_client.id,
        user_id=test_user.id,
        scope="read write",
        access_token_expires_at=access_expires,
        refresh_token_expires_at=refresh_expires
    )
    db_session.add(token)
    db_session.commit()
    
    # Query the token
    db_token = db_session.query(Token).filter(
        Token.access_token == "test_access_token"
    ).first()
    
    assert db_token is not None
    assert db_token.access_token == "test_access_token"
    assert db_token.refresh_token == "test_refresh_token"
    assert db_token.client_id == test_client.id
    assert db_token.user_id == test_user.id
    assert db_token.scope == "read write"
    assert db_token.access_token_expires_at == access_expires
    assert db_token.refresh_token_expires_at == refresh_expires
    assert db_token.is_revoked is False
    assert db_token.is_access_token_expired is False
    assert db_token.is_refresh_token_expired is False


def test_token_expiration(db_session, test_user, test_client):
    """Test token expiration properties."""
    # Create token with expired access token but valid refresh token
    past_access = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    future_refresh = (datetime.utcnow() + timedelta(days=7)).isoformat()
    
    token = Token(
        access_token="expired_access_token",
        refresh_token="valid_refresh_token",
        client_id=test_client.id,
        user_id=test_user.id,
        scope="read",
        access_token_expires_at=past_access,
        refresh_token_expires_at=future_refresh
    )
    db_session.add(token)
    db_session.commit()
    
    assert token.is_access_token_expired is True
    assert token.is_refresh_token_expired is False
    
    # Create token with both tokens expired
    past_access = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    past_refresh = (datetime.utcnow() - timedelta(days=1)).isoformat()
    
    expired_token = Token(
        access_token="expired_access_token2",
        refresh_token="expired_refresh_token",
        client_id=test_client.id,
        user_id=test_user.id,
        scope="read",
        access_token_expires_at=past_access,
        refresh_token_expires_at=past_refresh
    )
    db_session.add(expired_token)
    db_session.commit()
    
    assert expired_token.is_access_token_expired is True
    assert expired_token.is_refresh_token_expired is True


def test_client_relationships(db_session, test_user, test_client):
    """Test the relationships between OAuth models."""
    # Create authorization code
    auth_code = AuthorizationCode(
        code="rel_auth_code",
        client_id=test_client.id,
        user_id=test_user.id,
        redirect_uri="http://localhost:8000/callback",
        scope="read",
        expires_at=(datetime.utcnow() + timedelta(minutes=10)).isoformat()
    )
    
    # Create token
    token = Token(
        access_token="rel_access_token",
        refresh_token="rel_refresh_token",
        client_id=test_client.id,
        user_id=test_user.id,
        scope="read",
        access_token_expires_at=(datetime.utcnow() + timedelta(hours=1)).isoformat(),
        refresh_token_expires_at=(datetime.utcnow() + timedelta(days=7)).isoformat()
    )
    
    db_session.add_all([auth_code, token])
    db_session.commit()
    
    # Refresh the client to update relationships
    db_session.refresh(test_client)
    
    # Test client-authorization_codes relationship
    assert len(test_client.authorization_codes) == 1
    assert test_client.authorization_codes[0].code == "rel_auth_code"
    
    # Test client-tokens relationship
    assert len(test_client.tokens) == 1
    assert test_client.tokens[0].access_token == "rel_access_token"
