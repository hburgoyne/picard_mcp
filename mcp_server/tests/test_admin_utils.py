"""
Tests for the admin utilities.
"""
import pytest
from sqlalchemy.orm import Session
import hashlib

from app.models.user import User
from app.utils.admin import get_admin_user, verify_admin_credentials
from app.core.config import settings
from fastapi import HTTPException


def test_get_admin_user(db_session: Session):
    """Test that get_admin_user creates or returns an admin user."""
    # First call should create the admin user
    admin_user = get_admin_user(db_session)
    
    assert admin_user is not None
    assert admin_user.username == settings.ADMIN_USERNAME
    assert admin_user.email == settings.ADMIN_EMAIL
    assert admin_user.is_superuser is True
    
    # Second call should return the existing admin user
    admin_user_2 = get_admin_user(db_session)
    assert admin_user.id == admin_user_2.id


def test_verify_admin_credentials_success(db_session: Session, monkeypatch):
    """Test that verify_admin_credentials accepts valid admin credentials."""
    from fastapi.security import HTTPBasicCredentials
    
    # Create admin user
    admin_password_hash = hashlib.sha256(settings.ADMIN_PASSWORD.encode()).hexdigest()
    admin_user = User(
        username=settings.ADMIN_USERNAME,
        email=settings.ADMIN_EMAIL,
        hashed_password=admin_password_hash,
        is_active=True,
        is_superuser=True
    )
    db_session.add(admin_user)
    db_session.commit()
    
    # Create valid credentials
    credentials = HTTPBasicCredentials(
        username=settings.ADMIN_USERNAME,
        password=settings.ADMIN_PASSWORD
    )
    
    # Verify credentials
    user = verify_admin_credentials(credentials, db_session)
    assert user is not None
    assert user.username == settings.ADMIN_USERNAME
    assert user.is_superuser is True


def test_verify_admin_credentials_invalid_username(db_session: Session):
    """Test that verify_admin_credentials rejects invalid username."""
    from fastapi.security import HTTPBasicCredentials
    
    # Create credentials with invalid username
    credentials = HTTPBasicCredentials(
        username="invalid_username",
        password=settings.ADMIN_PASSWORD
    )
    
    # Verify credentials should raise HTTPException
    with pytest.raises(HTTPException) as excinfo:
        verify_admin_credentials(credentials, db_session)
    
    assert excinfo.value.status_code == 401


def test_verify_admin_credentials_invalid_password(db_session: Session):
    """Test that verify_admin_credentials rejects invalid password."""
    from fastapi.security import HTTPBasicCredentials
    
    # Create admin user
    admin_password_hash = hashlib.sha256(settings.ADMIN_PASSWORD.encode()).hexdigest()
    admin_user = User(
        username=settings.ADMIN_USERNAME,
        email=settings.ADMIN_EMAIL,
        hashed_password=admin_password_hash,
        is_active=True,
        is_superuser=True
    )
    db_session.add(admin_user)
    db_session.commit()
    
    # Create credentials with invalid password
    credentials = HTTPBasicCredentials(
        username=settings.ADMIN_USERNAME,
        password="invalid_password"
    )
    
    # Verify credentials should raise HTTPException
    with pytest.raises(HTTPException) as excinfo:
        verify_admin_credentials(credentials, db_session)
    
    assert excinfo.value.status_code == 401


def test_verify_admin_credentials_not_superuser(db_session: Session):
    """Test that verify_admin_credentials rejects non-superuser."""
    from fastapi.security import HTTPBasicCredentials
    
    # Create non-admin user with same password hash mechanism
    password = "regular_password"
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    regular_user = User(
        username="regular_user",
        email="regular@example.com",
        hashed_password=password_hash,
        is_active=True,
        is_superuser=False  # Not a superuser
    )
    db_session.add(regular_user)
    db_session.commit()
    
    # Create credentials for regular user
    credentials = HTTPBasicCredentials(
        username="regular_user",
        password="regular_password"
    )
    
    # Verify credentials should raise HTTPException
    with pytest.raises(HTTPException) as excinfo:
        verify_admin_credentials(credentials, db_session)
    
    assert excinfo.value.status_code == 403
