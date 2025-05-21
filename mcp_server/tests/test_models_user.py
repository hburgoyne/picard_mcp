"""Tests for the User model."""
import pytest
import uuid
from sqlalchemy.exc import IntegrityError
from app.models.user import User


def test_user_creation(db_session):
    """Test that a user can be created."""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password"
    )
    db_session.add(user)
    db_session.commit()
    
    # Query the user
    db_user = db_session.query(User).filter(User.email == "test@example.com").first()
    
    assert db_user is not None
    assert db_user.email == "test@example.com"
    assert db_user.username == "testuser"
    assert db_user.hashed_password == "hashed_password"
    assert db_user.is_active is True
    assert db_user.is_superuser is False
    assert isinstance(db_user.id, uuid.UUID)
    assert db_user.created_at is not None
    assert db_user.updated_at is not None


def test_user_unique_constraints(db_session):
    """Test that unique constraints are enforced."""
    # Create first user
    user1 = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password"
    )
    db_session.add(user1)
    db_session.commit()
    
    # Try to create user with same email
    user2 = User(
        email="test@example.com",
        username="different_user",
        hashed_password="hashed_password"
    )
    db_session.add(user2)
    
    # Should raise IntegrityError for duplicate email
    with pytest.raises(IntegrityError):
        db_session.commit()
    
    # Rollback for next test
    db_session.rollback()
    
    # Try to create user with same username
    user3 = User(
        email="different@example.com",
        username="testuser",
        hashed_password="hashed_password"
    )
    db_session.add(user3)
    
    # Should raise IntegrityError for duplicate username
    with pytest.raises(IntegrityError):
        db_session.commit()
