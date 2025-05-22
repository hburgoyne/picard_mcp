"""
Script to register a test OAuth client for development purposes.
"""
import uuid
import secrets
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.oauth import OAuthClient
from app.utils.logger import logger

def register_test_client(db: Session):
    """Register a test OAuth client and print its details."""
    # Generate client ID and secret
    client_id = uuid.uuid4()
    client_secret = secrets.token_urlsafe(32)
    
    # Create new OAuth client
    new_client = OAuthClient(
        client_id=client_id,
        client_secret=client_secret,
        client_name="Test Client",
        redirect_uris=["http://localhost:8000/callback"],
        scopes=["memories:read", "memories:write", "profile:read"],
        is_confidential=True
    )
    
    # Check if client already exists
    existing_client = db.query(OAuthClient).filter(OAuthClient.client_name == "Test Client").first()
    if existing_client:
        print(f"Test client already exists:")
        print(f"Client ID: {existing_client.client_id}")
        print(f"Client Secret: {existing_client.client_secret}")
        print(f"Redirect URIs: {existing_client.redirect_uris}")
        print(f"Scopes: {existing_client.scopes}")
        return
    
    # Add to database
    db.add(new_client)
    db.commit()
    db.refresh(new_client)
    
    print(f"Registered new OAuth client:")
    print(f"Client ID: {new_client.client_id}")
    print(f"Client Secret: {new_client.client_secret}")
    print(f"Redirect URIs: {new_client.redirect_uris}")
    print(f"Scopes: {new_client.scopes}")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        register_test_client(db)
    finally:
        db.close()
