from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from fastapi import HTTPException, status
from app.config import settings

class TokenManager:
    """
    JWT Token management utilities
    Handles token creation, validation, and user info extraction
    """
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a new JWT access token
        
        Args:
            data: Dictionary containing user data to encode in token
            expires_delta: Optional custom expiration time
            
        Returns:
            Encoded JWT token string
        """
        to_encode = data.copy()
        
        # Set expiration time
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # Add expiration to token payload
        to_encode.update({"exp": expire})
        
        # Encode and return JWT token
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.JWT_SECRET_KEY, 
            algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """
        Verify and decode JWT token
        
        Args:
            token: JWT token string to verify
            
        Returns:
            Decoded token payload
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            # Decode JWT token
            payload = jwt.decode(
                token, 
                settings.JWT_SECRET_KEY, 
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            # Extract user email from token
            email: str = payload.get("sub")
            if email is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: missing user email",
                    headers={"WWW-Authenticate": "Bearer"},
                )
                
            return payload
            
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    @staticmethod
    def create_dummy_token(email: str, name: str = "Test User") -> str:
        """
        Create a dummy JWT token for testing purposes
        
        Args:
            email: User email address
            name: User display name
            
        Returns:
            JWT token string
        """
        token_data = {
            "sub": email,  # Subject (user email)
            "name": name,
            "email": email,
            "iat": datetime.utcnow(),  # Issued at
            "type": "access_token"
        }
        
        return TokenManager.create_access_token(token_data)

# Create global token manager instance
token_manager = TokenManager()

# Export for easy import
__all__ = ["token_manager", "TokenManager"]