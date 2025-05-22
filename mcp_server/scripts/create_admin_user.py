#!/usr/bin/env python
"""
Script to create an admin user for the MCP server.
"""
import os
import sys
import hashlib
from sqlalchemy.orm import Session

# Add the parent directory to the path so we can import the app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models.user import User
from app.core.config import settings

def create_admin_user():
    """Create an admin user for the MCP server."""
    db = SessionLocal()
    
    try:
        # Check if admin user already exists
        admin_user = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()
        
        if admin_user:
            print(f"Admin user '{settings.ADMIN_USERNAME}' already exists.")
            print(f"Email: {admin_user.email}")
            print(f"Is superuser: {admin_user.is_superuser}")
            return
        
        # Create admin user
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
        
        print(f"Created admin user:")
        print(f"Username: {settings.ADMIN_USERNAME}")
        print(f"Password: {settings.ADMIN_PASSWORD}")
        print(f"Email: {settings.ADMIN_EMAIL}")
        print(f"Is superuser: {admin_user.is_superuser}")
        print("\nIMPORTANT: Change these credentials in production!")
        
    except Exception as e:
        print(f"Error creating admin user: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()
