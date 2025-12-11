import logging

# Configure application-wide logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)

from fastapi import FastAPI, Request, HTTPException, File, Form, UploadFile, Depends
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import uvicorn
import asyncio

# Import configuration and routers
from app.config import settings
from app.auth.google_oauth import google_oauth
from app.auth.tokens import token_manager
from app.api.feature1.router import router as feature1_router
from app.api.resume_roast.router import router as resume_roast_router

# Import database configuration
from app.core.database import init_db, close_db, get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.database.user_service import UserService
from app.schemas.user import UserCreate
from sqlalchemy.ext.asyncio import AsyncSession

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

# Database startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        await init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        # Don't fail startup if database is not available
        # This allows the app to run without database for testing

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connections on shutdown"""
    try:
        await close_db()
        print("✅ Database connections closed")
    except Exception as e:
        print(f"❌ Database shutdown error: {e}")

# Include API routers
app.include_router(feature1_router, prefix="/api/v1")
app.include_router(resume_roast_router, prefix="/api/v1")

# Debug router (temporary for troubleshooting)
if settings.APP_VERSION == "1.0.2":
    from app.debug_router import debug_router
    from app.migration_router import migration_router
    app.include_router(debug_router, prefix="/api/v1")
    app.include_router(migration_router, prefix="/api/v1")

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
    from datetime import datetime
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": settings.APP_VERSION
    }

@app.get("/health/db")
async def database_health_check():
    """
    Database health check endpoint
    """
    try:
        # Import here to avoid startup issues
        from app.core.database import AsyncSessionLocal
        from sqlalchemy import text
        from datetime import datetime
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            row = result.fetchone()
            
            if row and row[0] == 1:
                return {
                    "status": "healthy",
                    "database": "connected",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            else:
                return {
                    "status": "unhealthy", 
                    "database": "query_failed",
                    "error": "Query did not return expected result"
                }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "connection_failed",
            "error": str(e)
        }

# Test endpoint for LangSmith tracing without authentication
@app.post("/test-roast")
async def test_roast(request: dict):
    """
    Test endpoint for resume roasting without authentication
    FOR TESTING LANGSMITH TRACING ONLY
    """
    try:
        from app.services.resume_roasting_service import resume_roasting_service
        
        resume_text = request.get('resume_text', '')
        roast_style = request.get('roast_style', 'brutally_honest')
        
        if not resume_text:
            raise HTTPException(status_code=400, detail="resume_text is required")
        
        print(f"🧪 Test roast request - Style: {roast_style}, Resume length: {len(resume_text)} chars")
        
        # Call the roasting service
        result = await resume_roasting_service.roast_resume(
            resume_text=resume_text,
            style=roast_style
        )
        
        print(f"✅ Test roast completed - Response length: {len(result.get('roast', ''))} chars")
        
        return {
            "roast": result.get('roast', 'No roast generated'),
            "suggestions": result.get('suggestions', []),
            "rating": result.get('rating', 'N/A'),
            "test_mode": True,
            "langsmith_trace": "Check https://smith.langchain.com for trace details"
        }
        
    except Exception as e:
        logger.error(f"Test roast error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Roasting failed: {str(e)}")

# Test endpoint for file upload tracing without authentication
@app.post("/test-upload-roast")
async def test_upload_roast(file: UploadFile = File(...), roast_style: str = Form("funny")):
    """
    Test endpoint for file upload roasting without authentication
    FOR TESTING LANGSMITH TRACING WITH FILE UPLOADS
    """
    try:
        from app.services.resume_roasting_service import resume_roasting_service
        from app.services.document_processor import DocumentProcessor
        from fastapi import File, Form, UploadFile
        
        print(f"🧪 Test file upload - Filename: {file.filename}, Style: {roast_style}")
        
        # Process the uploaded file
        document_processor = DocumentProcessor()
        extracted_text = await document_processor.process_file(file)
        
        print(f"📄 Text extracted - Length: {len(extracted_text)} chars")
        
        if len(extracted_text) < 10:  # Lower threshold for testing
            raise HTTPException(
                status_code=422,
                detail="Extracted text is too short for testing"
            )
        
        # Call the roasting service (this should generate traces)
        result = await resume_roasting_service.roast_resume(
            resume_text=extracted_text,
            style=roast_style
        )
        
        print(f"✅ Test file roast completed - Response length: {len(result.get('roast', ''))} chars")
        
        return {
            "roast": result.get('roast', 'No roast generated'),
            "suggestions": result.get('suggestions', []),
            "rating": result.get('rating', 'N/A'),
            "extracted_text_length": len(extracted_text),
            "original_filename": file.filename,
            "test_mode": True,
            "langsmith_trace": "Check https://smith.langchain.com for trace details"
        }
        
    except Exception as e:
        logger.error(f"Test file upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"File upload roasting failed: {str(e)}")

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
        print(f"🔍 Google user info received: {user_info}")
        email = user_info.get('email')
        name = user_info.get('name', 'Unknown User')
        # Use email as the unique identifier if Google ID is not available
        google_id = user_info.get('sub') or user_info.get('id') or email
        avatar_url = user_info.get('picture')
        
        print(f"📧 Extracted - Email: {email}, Google ID: {google_id}, Name: {name}")
        
        if not email:
            raise HTTPException(status_code=400, detail=f"Missing required email from Google. Available fields: {list(user_info.keys())}")
        
        # Create database session
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            try:
                # Check if user already exists
                existing_user = await UserService.get_user_by_email(db, email)
                
                if not existing_user:
                    # Create new user
                    user_data = UserCreate(
                        email=email,
                        full_name=name,
                        avatar_url=avatar_url,
                        google_id=google_id
                    )
                    
                    db_user = await UserService.create_user(db, user_data)
                    print(f"✅ Created new user: {email}")
                else:
                    # Update existing user's last login and info
                    db_user = await UserService.update_last_login(db, existing_user.id)
                    print(f"✅ Updated existing user login: {email}")
                    
            except Exception as db_error:
                print(f"Database error in OAuth callback: {db_error}")
                # Continue with token creation even if DB fails
                pass
        
        # Generate JWT token for our application
        jwt_token = token_manager.create_dummy_token(email=email, name=name)
        
        # Redirect to frontend with token
        success_url = f"{settings.FRONTEND_URL}/#/auth/callback?token={jwt_token}"
        return RedirectResponse(url=success_url)
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"OAuth callback error: {str(e)}")
        print(f"Full traceback: {error_details}")
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
from fastapi.responses import JSONResponse

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "The requested endpoint does not exist",
            "path": str(request.url),
            "method": request.method
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    """Custom 500 handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error", 
            "message": "Something went wrong on our end",
            "path": str(request.url)
        }
    )

# Run the application
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )