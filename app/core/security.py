from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.auth.tokens import token_manager
from app.schemas.user import User

# Create HTTP Bearer security scheme
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """
    FastAPI dependency to extract and validate current user from JWT token
    
    Args:
        credentials: HTTP Authorization credentials (Bearer token)
        
    Returns:
        User object with validated information
        
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
        name = payload.get("name")
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing email",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create and return User object
        return User(
            email=email,
            name=name or "Unknown User",
            is_active=True
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

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
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

def optional_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[User]:
    """
    FastAPI dependency to optionally extract current user
    Returns None if no valid token is provided
    
    Args:
        credentials: Optional HTTP Authorization credentials
        
    Returns:
        User object if valid token provided, None otherwise
    """
    if not credentials:
        return None
        
    try:
        return get_current_user(credentials)
    except HTTPException:
        return None

# Export dependencies
__all__ = [
    "get_current_user", 
    "get_current_active_user", 
    "optional_current_user",
    "security"
]