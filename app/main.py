from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import uvicorn

# Import configuration and routers
from app.config import settings
from app.auth.google_oauth import google_oauth
from app.auth.tokens import token_manager
from app.api.feature1.router import router as feature1_router

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API for FaltuAI Fun application with Google OAuth and JWT authentication",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware (security)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # TODO: Restrict this in production
)

# Include API routers
app.include_router(feature1_router, prefix="/api/v1")

# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint - API information
    """
    return {
        "message": "FaltuAI Fun Backend API",
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs" if settings.DEBUG else "disabled in production",
        "auth": {
            "type": "Google OAuth + JWT",
            "login_url": "/auth/google/login"
        }
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring
    """
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",  # TODO: Add real timestamp
        "version": settings.APP_VERSION
    }

# Authentication routes
@app.get("/auth/google/login")
async def google_login(request: Request):
    """
    Initiate Google OAuth login flow
    Redirects user to Google authorization page
    """
    try:
        # Generate OAuth authorization URL
        auth_url = google_oauth.get_authorization_url()
        
        # Redirect user to Google OAuth
        return RedirectResponse(url=auth_url)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initiate OAuth login: {str(e)}"
        )

@app.get("/auth/google/callback")
async def google_callback(code: str = None, error: str = None):
    """
    Handle Google OAuth callback
    Exchange authorization code for user info and generate JWT token
    
    Args:
        code: Authorization code from Google
        error: Error message if OAuth failed
        
    Returns:
        Redirect to frontend with JWT token or error
    """
    # Handle OAuth errors
    if error:
        error_url = f"{settings.FRONTEND_URL}/#/auth/callback?error={error}"
        return RedirectResponse(url=error_url)
    
    # Validate authorization code
    if not code:
        error_url = f"{settings.FRONTEND_URL}/#/auth/callback?error=no_code"
        return RedirectResponse(url=error_url)
    
    try:
        # Complete OAuth flow and get user info
        user_info = await google_oauth.handle_oauth_callback(code)
        
        # Extract user details
        email = user_info.get('email')
        name = user_info.get('name', 'Unknown User')
        
        if not email:
            raise HTTPException(status_code=400, detail="No email received from Google")
        
        # Generate JWT token for our application
        jwt_token = token_manager.create_dummy_token(email=email, name=name)
        
        # Redirect to frontend with token
        success_url = f"{settings.FRONTEND_URL}/#/auth/callback?token={jwt_token}"
        return RedirectResponse(url=success_url)
        
    except Exception as e:
        print(f"OAuth callback error: {str(e)}")  # TODO: Use proper logging
        error_url = f"{settings.FRONTEND_URL}/#/auth/callback?error=oauth_failed"
        return RedirectResponse(url=error_url)

@app.post("/auth/logout")
async def logout():
    """
    Logout endpoint (placeholder)
    In a stateless JWT system, logout is handled client-side by removing the token
    """
    return {
        "message": "Logout successful",
        "instruction": "Remove JWT token from client storage"
    }

# TODO: Add more authentication endpoints as needed
# Examples:
# @app.post("/auth/refresh") - Refresh JWT token
# @app.get("/auth/me") - Get current user info
# @app.post("/auth/verify") - Verify JWT token

# Exception handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Custom 404 handler"""
    return {
        "error": "Not Found",
        "message": "The requested endpoint does not exist",
        "path": str(request.url),
        "method": request.method
    }

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    """Custom 500 handler"""
    return {
        "error": "Internal Server Error", 
        "message": "Something went wrong on our end",
        "path": str(request.url)
    }

# Run the application
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )