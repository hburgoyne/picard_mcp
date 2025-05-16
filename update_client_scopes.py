import asyncio
from sqlalchemy import select
from app.database import get_db
from app.models.oauth import OAuthClient

async def update_client_scopes():
    """Update the picard_client with the correct scopes"""
    print("Updating client scopes...")
    
    async for db in get_db():
        # Find the client
        result = await db.execute(
            select(OAuthClient).where(OAuthClient.client_id == "picard_client")
        )
        client = result.scalars().first()
        
        if client:
            print(f"Found client: {client.client_id}")
            print(f"Current scopes: {client.allowed_scopes}")
            
            # Update the scopes
            client.allowed_scopes = ["memories:read", "memories:write", "memories:admin"]
            await db.commit()
            
            print(f"Updated scopes: {client.allowed_scopes}")
            print("Client scopes updated successfully!")
        else:
            print("Client 'picard_client' not found!")

if __name__ == "__main__":
    asyncio.run(update_client_scopes())
