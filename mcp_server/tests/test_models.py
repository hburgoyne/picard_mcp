"""
Test file for database models.

This file contains tests for the User, Memory, OAuthClient, and Token models.
"""
import pytest
import uuid
from datetime import datetime, timedelta
import numpy as np
from sqlalchemy.exc import IntegrityError
from pgvector.sqlalchemy import Vector

from app.models.user import User
from app.models.memory import Memory
from app.models.oauth import OAuthClient, AuthorizationCode, Token


class TestUserModel:
    """Tests for the User model."""

    def test_user_creation(self, db_session):
        """Test creating a user."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
        )
        db_session.add(user)
        db_session.commit()

        # Query the user back from the database
        retrieved_user = db_session.query(User).filter_by(email="test@example.com").first()
        assert retrieved_user is not None
        assert retrieved_user.email == "test@example.com"
        assert retrieved_user.username == "testuser"
        assert retrieved_user.hashed_password == "hashed_password"
        assert retrieved_user.is_active is True
        assert retrieved_user.is_superuser is False
        assert retrieved_user.id is not None
        assert retrieved_user.created_at is not None
        assert retrieved_user.updated_at is not None

    def test_user_unique_constraint(self, db_session):
        """Test unique constraints on user email and username."""
        # Create first user
        user1 = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
        )
        db_session.add(user1)
        db_session.commit()

        # Try to create another user with the same email
        user2 = User(
            email="test@example.com",
            username="testuser2",
            hashed_password="hashed_password2",
        )
        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

        # Try to create another user with the same username
        user3 = User(
            email="test2@example.com",
            username="testuser",
            hashed_password="hashed_password3",
        )
        db_session.add(user3)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestMemoryModel:
    """Tests for the Memory model."""

    def test_memory_creation(self, db_session):
        """Test creating a memory."""
        # First, create a user that the memory belongs to
        user = User(
            email="memory_test@example.com",
            username="memory_user",
            hashed_password="hashed_password",
        )
        db_session.add(user)
        db_session.commit()

        # Create a memory for the user
        memory_text = "This is a test memory."
        memory = Memory(
            user_id=user.id,
            text=memory_text,
            permission="private",
        )
        db_session.add(memory)
        db_session.commit()

        # Query the memory back
        retrieved_memory = db_session.query(Memory).filter_by(text=memory_text).first()
        assert retrieved_memory is not None
        assert retrieved_memory.user_id == user.id
        assert retrieved_memory.text == memory_text
        assert retrieved_memory.permission == "private"
        assert retrieved_memory.embedding is None
        assert retrieved_memory.expiration_date is None

    def test_memory_with_embedding(self, db_session):
        """Test creating a memory with vector embedding."""
        # Create a user
        user = User(
            email="vector_test@example.com",
            username="vector_user",
            hashed_password="hashed_password",
        )
        db_session.add(user)
        db_session.commit()

        # Create a random embedding vector (1536 dimensions for OpenAI embeddings)
        embedding = np.random.rand(1536).astype(np.float32)

        # Create a memory with the embedding
        memory = Memory(
            user_id=user.id,
            text="Memory with embedding",
            permission="private",
            embedding=embedding,
        )
        db_session.add(memory)
        db_session.commit()

        # Query the memory back
        retrieved_memory = db_session.query(Memory).filter_by(text="Memory with embedding").first()
        assert retrieved_memory is not None
        assert retrieved_memory.embedding is not None
        assert len(retrieved_memory.embedding) == 1536

    def test_memory_expiration(self, db_session):
        """Test memory expiration property."""
        # Create a user
        user = User(
            email="expiry_test@example.com",
            username="expiry_user",
            hashed_password="hashed_password",
        )
        db_session.add(user)
        db_session.commit()

        # Create a memory that has already expired
        past_date = datetime.utcnow() - timedelta(days=1)
        expired_memory = Memory(
            user_id=user.id,
            text="Expired memory",
            permission="private",
            expiration_date=past_date,
        )
        db_session.add(expired_memory)

        # Create a memory that expires in the future
        future_date = datetime.utcnow() + timedelta(days=1)
        active_memory = Memory(
            user_id=user.id,
            text="Active memory",
            permission="private",
            expiration_date=future_date,
        )
        db_session.add(active_memory)

        # Create a memory with no expiration
        permanent_memory = Memory(
            user_id=user.id,
            text="Permanent memory",
            permission="private",
        )
        db_session.add(permanent_memory)
        
        db_session.commit()

        # Check expiration status
        assert expired_memory.is_expired is True
        assert active_memory.is_expired is False
        assert permanent_memory.is_expired is False


class TestOAuthModels:
    """Tests for the OAuth models."""

    def test_oauth_client_creation(self, db_session):
        """Test creating an OAuth client."""
        client = OAuthClient(
            client_id=uuid.uuid4(),
            client_secret="test_client_secret",
            client_name="Test Client",
            redirect_uris=["https://example.com/callback"],
            scopes=["memories:read", "memories:write"],
        )
        db_session.add(client)
        db_session.commit()

        # Query the client back
        retrieved_client = db_session.query(OAuthClient).filter_by(client_name="Test Client").first()
        assert retrieved_client is not None
        assert retrieved_client.client_name == "Test Client"
        assert retrieved_client.redirect_uris == ["https://example.com/callback"]
        assert retrieved_client.scopes == ["memories:read", "memories:write"]
        assert retrieved_client.is_confidential is True

    def test_authorization_code_creation(self, db_session):
        """Test creating an authorization code."""
        # Create a user and client first
        user = User(
            email="auth_code_test@example.com",
            username="auth_code_user",
            hashed_password="hashed_password",
        )
        db_session.add(user)
        
        client = OAuthClient(
            client_id=uuid.uuid4(),
            client_secret="auth_code_client_secret",
            client_name="Auth Code Test Client",
            redirect_uris=["https://example.com/callback"],
            scopes=["memories:read"],
        )
        db_session.add(client)
        db_session.commit()

        # Create an authorization code
        expires_at = (datetime.utcnow() + timedelta(minutes=10)).isoformat()
        auth_code = AuthorizationCode(
            code="test_auth_code",
            client_id=client.id,
            user_id=user.id,
            redirect_uri="https://example.com/callback",
            scope="memories:read",
            expires_at=expires_at,
            code_challenge="test_challenge",
            code_challenge_method="S256",
        )
        db_session.add(auth_code)
        db_session.commit()

        # Query the auth code back
        retrieved_code = db_session.query(AuthorizationCode).filter_by(code="test_auth_code").first()
        assert retrieved_code is not None
        assert retrieved_code.client_id == client.id
        assert retrieved_code.user_id == user.id
        assert retrieved_code.scope == "memories:read"
        assert retrieved_code.code_challenge == "test_challenge"
        assert not retrieved_code.is_expired

    def test_token_creation(self, db_session):
        """Test creating access and refresh tokens."""
        # Create a user and client first
        user = User(
            email="token_test@example.com",
            username="token_user",
            hashed_password="hashed_password",
        )
        db_session.add(user)
        
        client = OAuthClient(
            client_id=uuid.uuid4(),
            client_secret="token_client_secret",
            client_name="Token Test Client",
            redirect_uris=["https://example.com/callback"],
            scopes=["memories:read"],
        )
        db_session.add(client)
        db_session.commit()

        # Create tokens
        access_expires = (datetime.utcnow() + timedelta(minutes=60)).isoformat()
        refresh_expires = (datetime.utcnow() + timedelta(days=30)).isoformat()
        
        token = Token(
            access_token="test_access_token",
            refresh_token="test_refresh_token",
            client_id=client.id,
            user_id=user.id,
            scope="memories:read",
            access_token_expires_at=access_expires,
            refresh_token_expires_at=refresh_expires,
        )
        db_session.add(token)
        db_session.commit()

        # Query the token back
        retrieved_token = db_session.query(Token).filter_by(access_token="test_access_token").first()
        assert retrieved_token is not None
        assert retrieved_token.refresh_token == "test_refresh_token"
        assert retrieved_token.client_id == client.id
        assert retrieved_token.user_id == user.id
        assert retrieved_token.scope == "memories:read"
        assert not retrieved_token.is_access_token_expired
        assert not retrieved_token.is_refresh_token_expired
        assert not retrieved_token.is_revoked
