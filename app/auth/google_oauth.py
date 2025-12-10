from urllib.parse import urlencode
from typing import Dict, Any, Optional
import httpx
from fastapi import HTTPException, status
from authlib.integrations.starlette_client import OAuth
from app.config import settings

class GoogleOAuthHandler:
    """
    Google OAuth 2.0 authentication handler
    Manages OAuth flow, token exchange, and user info retrieval
    """
    
    def __init__(self):
        self.oauth = OAuth()
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.google_oauth_redirect_uri
        
        # Register Google OAuth client
        self.google = self.oauth.register(
            name='google',
            client_id=self.client_id,
            client_secret=self.client_secret,
            server_metadata_url='https://accounts.google.com/.well-known/openid_configuration',
            client_kwargs={
                'scope': ' '.join(settings.GOOGLE_OAUTH_SCOPES)
            }
        )
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Generate Google OAuth authorization URL
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            Authorization URL for redirecting user to Google
        """
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(settings.GOOGLE_OAUTH_SCOPES),
            'response_type': 'code',
            'access_type': 'offline',
            'prompt': 'consent'
        }
        
        if state:
            params['state'] = state
            
        return f"{settings.GOOGLE_OAUTH_AUTHORIZE_URL}?{urlencode(params)}"
    
    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token
        
        Args:
            code: Authorization code from Google OAuth callback
            
        Returns:
            Token response from Google
            
        Raises:
            HTTPException: If token exchange fails
        """
        token_data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': self.redirect_uri,
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    settings.GOOGLE_OAUTH_TOKEN_URL,
                    data=token_data,
                    headers={'Accept': 'application/json'}
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to exchange code for token: {str(e)}"
            )
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Retrieve user information from Google using access token
        
        Args:
            access_token: Google access token
            
        Returns:
            User information from Google
            
        Raises:
            HTTPException: If user info retrieval fails
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    settings.GOOGLE_OAUTH_USERINFO_URL,
                    headers={'Authorization': f'Bearer {access_token}'}
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to get user info: {str(e)}"
            )
    
    async def handle_oauth_callback(self, code: str) -> Dict[str, Any]:
        """
        Complete OAuth flow: exchange code for token and get user info
        
        Args:
            code: Authorization code from Google
            
        Returns:
            Dictionary containing user information
            
        Raises:
            HTTPException: If OAuth flow fails at any step
        """
        # Exchange code for token
        token_response = await self.exchange_code_for_token(code)
        
        # Extract access token
        access_token = token_response.get('access_token')
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No access token received from Google"
            )
        
        # Get user information
        user_info = await self.get_user_info(access_token)
        
        # Debug: Print raw user info from Google
        print(f"🔍 Raw Google userinfo API response: {user_info}")
        
        return {
            'email': user_info.get('email'),
            'name': user_info.get('name'),
            'picture': user_info.get('picture'),
            'verified_email': user_info.get('verified_email', False),
            'id': user_info.get('id'),  # Add the Google user ID
            'sub': user_info.get('sub'), # Add OpenID Connect subject
            'access_token': access_token,
            'token_type': token_response.get('token_type', 'Bearer')
        }

# Create global OAuth handler instance
google_oauth = GoogleOAuthHandler()

# Export for easy import
__all__ = ["google_oauth", "GoogleOAuthHandler"]