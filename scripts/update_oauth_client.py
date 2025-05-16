#!/usr/bin/env python
import sys
import os
import asyncio
from sqlalchemy import select, update

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.models.oauth import OAuthClient
from app.database import SessionLocal

async def update_oauth_client():
    """Update the OAuth client redirect URI in the database."""
    print("Updating OAuth client...")
    
    # Create database session
    async with SessionLocal() as session:
        # Find the client
        result = await session.execute(
            select(OAuthClient).where(OAuthClient.client_id == settings.OAUTH_CLIENT_ID)
        )
        client = result.scalars().first()
        
        if not client:
            print(f"Error: OAuth client with ID {settings.OAUTH_CLIENT_ID} not found")
            return
        
        # Update the redirect URI
        client.redirect_uri = settings.OAUTH_REDIRECT_URI
        await session.commit()
        
        print(f"Updated OAuth client {client.client_id} with redirect URI: {client.redirect_uri}")
        print(f"New redirect URI: {settings.OAUTH_REDIRECT_URI}")
        
        # Verify the update
        result = await session.execute(
            select(OAuthClient).where(OAuthClient.client_id == settings.OAUTH_CLIENT_ID)
        )
        updated_client = result.scalars().first()
        print(f"Verified redirect URI in database: {updated_client.redirect_uri}")
        
        return updated_client

if __name__ == "__main__":
    asyncio.run(update_oauth_client())
