from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    """
    Base user schema with common fields
    """
    email: EmailStr
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None

class UserCreate(UserBase):
    """
    Schema for creating a new user
    """
    google_id: str

class UserUpdate(BaseModel):
    """
    Schema for updating user information
    """
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_premium: Optional[bool] = None

class User(UserBase):
    """
    User schema for API responses
    """
    id: int
    google_id: str
    is_active: bool = True
    is_premium: bool = False
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserInDB(User):
    """
    User schema for database operations (backward compatibility)
    """
    pass

class Token(BaseModel):
    """
    Schema for JWT token responses
    """
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None

class TokenData(BaseModel):
    """
    Schema for token payload data
    """
    email: Optional[str] = None
    name: Optional[str] = None

# Export schemas
__all__ = [
    "User", 
    "UserCreate", 
    "UserBase", 
    "UserInDB", 
    "Token", 
    "TokenData"
]