from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.tokens import token_manager
from app.schemas.user import User
from app.core.database import get_db
from app.services.database.user_service import UserService

# Create HTTP Bearer security scheme
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    FastAPI dependency to extract and validate current user from JWT token
    
    Args:
        credentials: HTTP Authorization credentials (Bearer token)
        db: Database session
        
    Returns:
        User object with validated information from database
        
    Raises:
        HTTPException: If token is invalid or user cannot be authenticated
    """
    # Extract token from credentials
    token = credentials.credentials
    
    # Verify and decode token
    try:
        payload = token_manager.verify_token(token)
        
        # Extract user information from token payload
        email = payload.get("sub")
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing email",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from database
        db_user = await UserService.get_user_by_email(db, email)
        
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found in database",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Convert database user to schema user
        return User(
            id=db_user.id,
            email=db_user.email,
            full_name=db_user.full_name,
            avatar_url=db_user.avatar_url,
            google_id=db_user.google_id,
            is_active=db_user.is_active,
            is_premium=db_user.is_premium,
            created_at=db_user.created_at,
            last_login=db_user.last_login
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions from token verification
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    FastAPI dependency to ensure user is active
    
    Args:
        current_user: User object from get_current_user dependency
        
    Returns:
        Active user object
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

async def optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    FastAPI dependency to optionally extract current user
    Returns None if no valid token is provided
    
    Args:
        credentials: Optional HTTP Authorization credentials
        db: Database session
        
    Returns:
        User object if valid token provided, None otherwise
    """
    if not credentials:
        return None
        
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None

# Export dependencies
__all__ = [
    "get_current_user", 
    "get_current_active_user", 
    "optional_current_user",
    "security"
]