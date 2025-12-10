from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    """
    Base user schema with common fields
    """
    email: EmailStr
    name: Optional[str] = None

class UserCreate(UserBase):
    """
    Schema for creating a new user
    """
    pass

class User(UserBase):
    """
    User schema for API responses
    """
    is_active: bool = True
    
    class Config:
        from_attributes = True

class UserInDB(User):
    """
    User schema for database operations (if needed in future)
    """
    hashed_password: Optional[str] = None

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