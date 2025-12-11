"# FaltuAI Fun - Backend API

FastAPI backend with Google OAuth authentication, JWT tokens, and AI-powered resume roasting.

## 🚀 Quick Start

### Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker

```bash
# Build image
docker build -t faltuai-backend .

# Run container
docker run -p 8000:8000 -e OPENAI_API_KEY="your-key" faltuai-backend
```

## 📁 Project Structure

```
app/
├── api/                 # API routes
│   ├── feature1/       # Feature endpoints
│   └── resume_roast/   # Resume roasting API
├── auth/               # Authentication
│   ├── google_oauth.py # Google OAuth integration
│   └── tokens.py       # JWT token management
├── core/               # Core functionality
│   ├── database.py     # Database configuration
│   └── security.py     # Security utilities
├── services/           # Business logic
│   ├── resume_roasting_service.py  # AI resume roasting
│   └── document_processor.py       # File processing
├── schemas/            # Pydantic models
└── main.py             # FastAPI application
```

## 🐳 Container Registry

### Automated Builds

Docker images are automatically built and pushed to Azure Container Registry:

- **Registry**: `faltuaicr.azurecr.io`
- **Image**: `faltuai-backend`
- **Latest**: `faltuaicr.azurecr.io/faltuai-backend:latest`

### Pull Image

```bash
# Login to ACR
az acr login --name faltuaicr

# Pull latest
docker pull faltuaicr.azurecr.io/faltuai-backend:latest
```

## 🔧 Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...

# Optional
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
JWT_SECRET_KEY=your-secret-key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=...
LANGCHAIN_PROJECT=faltuai-fun
```

### Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create OAuth 2.0 credentials
3. Set authorized redirect URI: `http://localhost:8000/auth/google/callback`
4. Add client ID and secret to environment variables

## 🌐 API Endpoints

### Authentication
- `GET /auth/google/login` - Google OAuth login
- `GET /auth/google/callback` - OAuth callback
- `POST /auth/logout` - Logout

### Resume Roasting
- `GET /api/v1/resume-roast/styles` - Available roasting styles
- `POST /api/v1/resume-roast/roast-text` - Roast resume text
- `POST /api/v1/resume-roast/upload-and-roast` - Upload and roast file

### Testing
- `POST /test-roast` - Test endpoint (no auth)
- `POST /test-upload-roast` - Test file upload (no auth)

## 🛠️ Tech Stack

- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM with async support
- **PostgreSQL** - Database
- **LangChain** - AI/LLM integration
- **Google OAuth** - Authentication
- **JWT** - Token-based authorization
- **Docker** - Containerization

For detailed deployment instructions, see [Deployment Guide](.github/DEPLOYMENT.md)." 
