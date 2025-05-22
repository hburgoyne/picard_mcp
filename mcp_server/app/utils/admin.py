"""
Admin utilities for authentication and authorization.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
import secrets
import hashlib

from app.db.session import get_db
from app.models.user import User
from app.core.config import settings
from app.utils.logger import logger

# Basic authentication for admin endpoints
security = HTTPBasic()

def verify_admin_credentials(
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Verify admin credentials for protected admin endpoints.
    
    Args:
        credentials: HTTP Basic Auth credentials
        db: Database session
        
    Returns:
        User object if credentials are valid
        
    Raises:
        HTTPException: If credentials are invalid
    """
    # Find user by username
    user = db.query(User).filter(User.username == credentials.username).first()
    
    if not user:
        logger.warning(f"Admin authentication failed: User {credentials.username} not found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    # Verify password (in a real system, use proper password hashing)
    # This is a simple implementation for demonstration purposes
    password_hash = hashlib.sha256(credentials.password.encode()).hexdigest()
    is_correct_password = secrets.compare_digest(user.hashed_password, password_hash)
    
    if not is_correct_password:
        logger.warning(f"Admin authentication failed: Invalid password for user {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    # Check if user is a superuser
    if not user.is_superuser:
        logger.warning(f"Admin authentication failed: User {credentials.username} is not a superuser")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access admin endpoints",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return user

def get_admin_user(db: Session = Depends(get_db)):
    """
    Get or create an admin user.
    
    Args:
        db: Database session
        
    Returns:
        Admin user object
    """
    # Check if admin user exists
    admin_user = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()
    
    if admin_user:
        return admin_user
    
    # Create admin user if it doesn't exist
    admin_password_hash = hashlib.sha256(settings.ADMIN_PASSWORD.encode()).hexdigest()
    admin_user = User(
        username=settings.ADMIN_USERNAME,
        email=settings.ADMIN_EMAIL,
        hashed_password=admin_password_hash,
        is_active=True,
        is_superuser=True
    )
    
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    
    logger.info(f"Created admin user: {settings.ADMIN_USERNAME}")
    return admin_user

def create_admin_user(db: Session):
    """
    Create an admin user for command-line usage.
    
    Args:
        db: Database session
        
    Returns:
        Admin user object
    """
    return get_admin_user(db)
