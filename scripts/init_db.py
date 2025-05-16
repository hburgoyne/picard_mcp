import asyncio
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import init_db, close_db
from app.models.user import User
from app.models.oauth import OAuthClient
from app.config import settings

async def create_default_client(db: AsyncSession):
    """Create default OAuth client if it doesn't exist"""
    # Check if client already exists
    client_result = await db.execute(
        select(OAuthClient).where(OAuthClient.client_id == settings.OAUTH_CLIENT_ID)
    )
    client = client_result.scalars().first()
    
    if client:
        print(f"OAuth client already exists: {client.client_id}")
        return client
    
    # Create new client
    client = OAuthClient(
        client_id=settings.OAUTH_CLIENT_ID,
        client_secret=settings.OAUTH_CLIENT_SECRET,
        redirect_uris=[settings.OAUTH_REDIRECT_URI],
        allowed_scopes=["memories:read", "memories:write", "memories:admin"]
    )
    db.add(client)
    await db.commit()
    await db.refresh(client)
    
    print(f"Created OAuth client: {client.client_id}")
    return client

async def create_test_user(db: AsyncSession):
    """Create test user if it doesn't exist"""
    # Check if user already exists
    user_result = await db.execute(
        select(User).where(User.username == "test_user")
    )
    user = user_result.scalars().first()
    
    if user:
        print(f"Test user already exists: {user.username}")
        return user
    
    # Create new user
    user = User(
        username="test_user",
        email="test@example.com",
        hashed_password="hashed_password"  # In production, use proper hashing
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    print(f"Created test user: {user.username}")
    return user

async def main():
    """Initialize database with default data"""
    # Initialize database
    db = await init_db()
    
    try:
        # Create default OAuth client
        await create_default_client(db)
        
        # Create test user
        await create_test_user(db)
        
        print("Database initialization complete")
    finally:
        # Close database connection
        await close_db(db)

if __name__ == "__main__":
    asyncio.run(main())
