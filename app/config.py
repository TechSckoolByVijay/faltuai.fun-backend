import os
from typing import Optional

class Settings:
    """
    Application configuration settings
    Uses environment variables with fallback defaults
    """
    
    # Google OAuth Configuration
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "dummy-google-id")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "dummy-google-secret")
    
    # Frontend URL for redirects
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    
    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dummysecret")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Application Configuration
    APP_NAME: str = "FaltuAI Fun Backend"
    APP_VERSION: str = "1.0.1"  # Updated after database schema fix
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # CORS Configuration
    ALLOWED_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        FRONTEND_URL,
        "https://techsckoolbyvijay.github.io",  # GitHub Pages root
    ]
    
    # Database Configuration (for future use)
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "dummy-openai-key")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    
    # LangSmith Configuration
    LANGCHAIN_TRACING_V2: bool = os.getenv("LANGCHAIN_TRACING_V2", "True").lower() == "true"
    LANGCHAIN_API_KEY: str = os.getenv("LANGCHAIN_API_KEY", "dummy-langsmith-key")
    LANGCHAIN_PROJECT: str = os.getenv("LANGCHAIN_PROJECT", "faltuai-fun")
    LANGCHAIN_ENDPOINT: str = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
    
    # Azure Document Intelligence Configuration
    AZURE_DOC_INTELLIGENCE_ENDPOINT: str = os.getenv("AZURE_DOC_INTELLIGENCE_ENDPOINT", "dummy-endpoint")
    AZURE_DOC_INTELLIGENCE_KEY: str = os.getenv("AZURE_DOC_INTELLIGENCE_KEY", "dummy-key")
    
    # File Upload Configuration
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: list = ["application/pdf", "text/plain"]
    
    # OAuth URLs
    GOOGLE_OAUTH_AUTHORIZE_URL: str = "https://accounts.google.com/o/oauth2/auth"
    GOOGLE_OAUTH_TOKEN_URL: str = "https://oauth2.googleapis.com/token"
    GOOGLE_OAUTH_USERINFO_URL: str = "https://www.googleapis.com/oauth2/v2/userinfo"
    
    # OAuth Scopes
    GOOGLE_OAUTH_SCOPES: list = [
        "openid",
        "email", 
        "profile"
    ]

    @property
    def google_oauth_redirect_uri(self) -> str:
        """Generate the OAuth redirect URI"""
        # Check if we're in production environment
        environment = os.getenv('ENVIRONMENT', 'development').lower()
        if environment == 'production':
            return "https://faltuai.reddune-c0e74598.centralindia.azurecontainerapps.io/auth/google/callback"
        return "http://localhost:8000/auth/google/callback"

# Create global settings instance
settings = Settings()

# Export for easy import
__all__ = ["settings"]