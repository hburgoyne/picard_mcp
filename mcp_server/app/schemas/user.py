from pydantic import BaseModel, EmailStr, UUID4, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    """Base schema for user data."""
    email: EmailStr
    username: str

class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str

class UserUpdate(BaseModel):
    """Schema for updating a user."""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None

class UserInDBBase(UserBase):
    """Base schema for user data from database."""
    id: UUID4
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class User(UserInDBBase):
    """Schema for user data returned to client."""
    pass

class UserInDB(UserInDBBase):
    """Schema for user data stored in database (includes hashed password)."""
    hashed_password: str
