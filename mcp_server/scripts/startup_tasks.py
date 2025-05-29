#!/usr/bin/env python
"""
Startup tasks for MCP server on Render.
This script handles database setup and admin user creation.
"""
import os
import sys
import subprocess
import hashlib
from pathlib import Path

# Add the parent directory to the path so we can import the app modules
sys.path.append(str(Path(__file__).parent.parent))

def setup_database():
    """Set up the database and run migrations."""
    print("Setting up database...")
    
    # Check if we can connect to the database
    try:
        from app.db.session import SessionLocal
        from sqlalchemy import text
        
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        print("Database connection successful")
    except Exception as e:
        print(f"Database connection failed: {e}")
        sys.exit(1)
    
    # Install pgvector extension if needed
    try:
        from app.db.session import SessionLocal
        from sqlalchemy import text
        
        db = SessionLocal()
        db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        db.commit()
        db.close()
        print("pgvector extension enabled")
    except Exception as e:
        print(f"Warning: Could not enable pgvector extension: {e}")
    
    # Run Alembic migrations
    print("Running Alembic migrations...")
    try:
        result = subprocess.run(['alembic', 'upgrade', 'head'], 
                              capture_output=True, text=True, check=True)
        print("Migrations completed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Migration error: {e.stderr}")
        sys.exit(1)
    
    print("Database setup completed")

def create_admin_user():
    """Create an admin user for the MCP server."""
    print("Creating admin user...")
    
    try:
        from app.db.session import SessionLocal
        from app.models.user import User
        from app.core.config import settings
        
        db = SessionLocal()
        
        # Check if admin user already exists
        admin_user = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()
        
        if admin_user:
            print(f"Admin user '{settings.ADMIN_USERNAME}' already exists.")
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
        
        print(f"Created admin user: {settings.ADMIN_USERNAME}")
        
    except Exception as e:
        print(f"Error creating admin user: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    setup_database()
    create_admin_user()
    print("MCP server startup tasks completed successfully")
