"""
Admin endpoints for managing OAuth clients and other administrative tasks.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.db.session import get_db
from app.models.oauth import OAuthClient
from app.models.user import User
from app.schemas.oauth import OAuthClientCreate, OAuthClientUpdate, OAuthClient as OAuthClientSchema
from app.core.config import settings
from app.utils.logger import logger
from app.utils.admin import verify_admin_credentials

router = APIRouter()

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
