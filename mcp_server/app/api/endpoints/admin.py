"""
Admin endpoints for managing OAuth clients and other administrative tasks.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import secrets

from app.db.session import get_db
from app.models.oauth import OAuthClient
from app.models.user import User
from app.schemas.oauth import OAuthClientCreate, OAuthClientUpdate, OAuthClient as OAuthClientSchema, OAuthClientRegisterResponse
from app.core.config import settings
from app.utils.logger import logger
from app.utils.admin import verify_admin_credentials
from app.utils.oauth import OAuthError

router = APIRouter()

@router.post("/clients/register", response_model=OAuthClientRegisterResponse)
async def register_client(
    client_data: OAuthClientCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(verify_admin_credentials)
):
    """
    Register a new OAuth client.
    
    Args:
        client_data: Client registration data
        db: Database session
        admin_user: Authenticated admin user
        
    Returns:
        Registered client information with client credentials
    """
    try:
        # Generate client secret
        client_secret = secrets.token_urlsafe(32)
        
        # Create new OAuth client
        new_client = OAuthClient(
            client_id=uuid.uuid4(),
            client_secret=client_secret,
            client_name=client_data.client_name,
            redirect_uris=client_data.redirect_uris,
            scopes=client_data.scopes,
            is_confidential=client_data.is_confidential
        )
        
        db.add(new_client)
        db.commit()
        db.refresh(new_client)
        
        logger.info(f"Registered new OAuth client: {new_client.client_name}")
        
        # Return client credentials
        return {
            "client_id": str(new_client.client_id),
            "client_secret": new_client.client_secret,
            "client_name": new_client.client_name,
            "redirect_uris": new_client.redirect_uris,
            "scopes": new_client.scopes,
            "is_confidential": new_client.is_confidential
        }
    except Exception as e:
        logger.error(f"Error registering OAuth client: {str(e)}")
        raise OAuthError("client_registration_failed", "Failed to register OAuth client")


@router.get("/clients", response_model=List[OAuthClientSchema])
async def list_oauth_clients(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin_user: User = Depends(verify_admin_credentials)
):
    """
    List all registered OAuth clients.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        
    Returns:
        List of OAuth clients
    """
    clients = db.query(OAuthClient).offset(skip).limit(limit).all()
    return clients

@router.get("/clients/{client_id}", response_model=OAuthClientSchema)
async def get_oauth_client(
    client_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin_user: User = Depends(verify_admin_credentials)
):
    """
    Get a specific OAuth client by ID.
    
    Args:
        client_id: UUID of the client to retrieve
        db: Database session
        
    Returns:
        OAuth client details
    """
    client = db.query(OAuthClient).filter(OAuthClient.client_id == client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OAuth client not found"
        )
    return client

@router.put("/clients/{client_id}", response_model=OAuthClientSchema)
async def update_oauth_client(
    client_id: uuid.UUID,
    client_data: OAuthClientUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(verify_admin_credentials)
):
    """
    Update an existing OAuth client.
    
    Args:
        client_id: UUID of the client to update
        client_data: Updated client data
        db: Database session
        
    Returns:
        Updated OAuth client details
    """
    client = db.query(OAuthClient).filter(OAuthClient.client_id == client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OAuth client not found"
        )
    
    # Update client fields if provided
    if client_data.client_name is not None:
        client.client_name = client_data.client_name
    if client_data.redirect_uris is not None:
        client.redirect_uris = client_data.redirect_uris
    if client_data.scopes is not None:
        client.scopes = client_data.scopes
    if client_data.is_confidential is not None:
        client.is_confidential = client_data.is_confidential
    
    db.commit()
    db.refresh(client)
    return client

@router.delete("/clients/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_oauth_client(
    client_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin_user: User = Depends(verify_admin_credentials)
):
    """
    Delete an OAuth client.
    
    Args:
        client_id: UUID of the client to delete
        db: Database session
        
    Returns:
        204 No Content on success
    """
    client = db.query(OAuthClient).filter(OAuthClient.client_id == client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OAuth client not found"
        )
    
    db.delete(client)
    db.commit()
    return None
