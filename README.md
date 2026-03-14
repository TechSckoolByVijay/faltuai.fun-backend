"# FaltooAI Backend Documentation

> **FastAPI-powered backend for the FaltooAI productivity platform**

## 🚀 Overview

FaltooAI Backend is a modern, high-performance API built with FastAPI that powers the FaltooAI productivity platform. It provides AI-powered services including resume roasting, document processing, and various micro-productivity tools. The backend features Google OAuth authentication, JWT token management, PostgreSQL database integration, and comprehensive monitoring with LangSmith.

## 🛠️ Tech Stack

### Core Framework
- **FastAPI** - Modern, high-performance web framework for Python
- **Uvicorn** - Lightning-fast ASGI server
- **Python 3.11+** - Latest Python features and performance
- **Pydantic** - Data validation and serialization

### Database & ORM
- **PostgreSQL** - Production-ready relational database
- **SQLAlchemy** - Python SQL toolkit and ORM
- **Alembic** - Database migration management
- **AsyncPG** - High-performance async PostgreSQL driver

### AI & Machine Learning
- **OpenAI GPT Models** - AI-powered text processing and generation
- **LangChain** - LLM application development framework
- **LangSmith** - LLM monitoring, debugging, and analytics
- **Azure Document Intelligence** - PDF and document processing

### Authentication & Security
- **Google OAuth 2.0** - Secure social authentication
- **JWT (JSON Web Tokens)** - Stateless authentication
- **Passlib** - Password hashing and verification
- **Python-Jose** - JWT implementation for Python

### Cloud Infrastructure
- **Azure Container Apps** - Serverless container hosting
- **Azure Container Registry (ACR)** - Container image storage
- **Azure PostgreSQL** - Managed database service
- **GitHub Actions** - CI/CD pipeline automation

### Monitoring & Observability
- **LangSmith Tracing** - LLM call monitoring and debugging
- **FastAPI Logging** - Application performance monitoring
- **Health Checks** - Service availability monitoring

### Development Tools
- **Docker** - Containerization and deployment
- **Pytest** - Testing framework
- **Black** - Code formatting
- **Flake8** - Code linting

## 🏗️ Architecture

### Project Structure
```
backend/
├── app/
│   ├── api/                        # API route definitions
│   │   ├── resume_roast/          # Resume roasting endpoints
│   │   │   └── router.py          # Resume roast API routes
│   │   ├── stock_analysis/        # Stock analysis endpoints
│   │   │   └── router.py
│   │   ├── newsletter/            # Newsletter endpoints
│   │   │   └── router.py
│   │   ├── skill_assessment/      # Skill assessment endpoints
│   │   │   └── router.py
│   │   └── v1/endpoints/          # Versioned endpoint modules
│   │       └── cringe_meter.py    # LinkedIn cringe analyzer endpoint
│   ├── auth/                      # Authentication modules
│   │   ├── google_oauth.py        # Google OAuth integration
│   │   └── tokens.py              # JWT token management
│   ├── core/                      # Core application modules
│   │   ├── database.py            # Database configuration
│   │   └── security.py            # Security utilities
│   ├── models/                    # SQLAlchemy database models
│   │   ├── __init__.py           # Model exports
│   │   ├── user.py               # User model
│   │   └── resume_roast.py       # Resume roast model
│   ├── schemas/                   # Pydantic schemas
│   │   ├── user.py               # User data schemas
│   │   ├── resume.py             # Resume data schemas
│   │   └── cringe.py             # Cringe analyzer request/response schemas
│   ├── services/                  # Business logic services
│   │   ├── document_processor.py  # Document processing service
│   │   ├── resume_roasting_service.py # AI resume roasting
│   │   ├── cringe_service.py      # Cringe analyzer LLM service
│   │   └── database/             # Database services
│   │       ├── user_service.py   # User database operations
│   │       └── resume_roast_service.py # Resume roast DB ops
│   ├── config.py                 # Application configuration
│   ├── main.py                   # FastAPI application entry
│   └── migration_router.py       # Database migration endpoints
├── alembic/                      # Database migrations
│   ├── versions/                 # Migration versions
│   ├── env.py                    # Alembic environment
│   └── script.py.mako           # Migration template
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Container configuration
├── alembic.ini                  # Alembic configuration
└── setup-*.ps1                 # Azure deployment scripts
```

### Service Architecture
- **API Layer** - FastAPI routers and endpoints
- **Business Logic** - Service layer for complex operations
- **Data Access** - Repository pattern with SQLAlchemy
- **External Services** - OpenAI, Azure, Google integrations
- **Authentication** - OAuth and JWT token management

## 🔐 Authentication & Security

### Google OAuth 2.0 Flow
1. **Client Registration** - Google Cloud Console configuration
2. **Authorization Request** - Redirect to Google OAuth
3. **Token Exchange** - Authorization code to access token
4. **User Profile** - Fetch user information from Google
5. **JWT Generation** - Create application-specific tokens

### Security Features
- **CORS Configuration** - Cross-origin request security
- **HTTPS Enforcement** - Secure data transmission
- **JWT Expiration** - Automatic token refresh
- **Input Validation** - Pydantic schema validation
- **SQL Injection Prevention** - ORM parameterized queries

## 🤖 AI Services Integration

### OpenAI Integration
- **GPT Models** - Text generation and analysis
- **Prompt Engineering** - Optimized AI interactions
- **Token Management** - Cost optimization strategies
- **Error Handling** - Graceful AI service failures

### LangChain Framework
- **Chain Composition** - Complex AI workflows
- **Memory Management** - Conversation context
- **Tool Integration** - External service connections
- **Prompt Templates** - Reusable prompt patterns

### LangSmith Monitoring
- **Trace Collection** - LLM call tracking
- **Performance Analytics** - Response time and quality metrics
- **Debug Information** - Detailed execution logs
- **Cost Tracking** - AI service usage monitoring

### Azure Document Intelligence
- **PDF Processing** - Extract text from documents
- **OCR Capabilities** - Image-to-text conversion
- **Form Recognition** - Structured data extraction
- **Multi-format Support** - Various document types

## 🗄️ Database Design

### PostgreSQL Schema
- **Users Table** - User profiles and authentication data
- **Resume Roasts** - AI-generated feedback and metadata
- **Sessions** - User session management
- **Audit Logs** - System activity tracking

### Migration Management
```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migrations
alembic downgrade -1
```

## 🚀 Deployment

### Azure Container Apps
- **Serverless Scaling** - Automatic resource management
- **Container Registry** - Image storage and versioning
- **Environment Variables** - Secure configuration management
- **Health Monitoring** - Application availability checks

### GitHub Actions CI/CD
```yaml
# Automated workflow
1. Code Push → GitHub
2. Build → Docker Image
3. Push → Azure Container Registry
4. Deploy → Azure Container Apps
5. Health Check → Verify Deployment
```

### Environment Configuration
```env
# Database
DATABASE_URL=postgresql://user:pass@host:5432/db
ASYNC_DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db

# Authentication
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
JWT_SECRET_KEY=your-jwt-secret

# AI Services
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=gpt-3.5-turbo

# LangSmith
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langsmith-key
LANGCHAIN_PROJECT=faltooai-fun

# Azure Services
AZURE_DOC_INTELLIGENCE_ENDPOINT=your-endpoint
AZURE_DOC_INTELLIGENCE_KEY=your-key
```

## 🔧 Development Setup

### Prerequisites
- Docker & Docker Compose
- Git for version control

### Docker Development
```bash
# Build and run full stack (from repository root)
docker compose up --build

# Run specific services
docker compose up database backend

# View logs
docker compose logs -f backend
```

### Test `Cringe-o-Meter` Endpoint (Docker)
```bash
# From repository root (backend container must be running)
docker compose exec backend curl -X POST "http://localhost:8000/api/v1/cringe/analyze" -H "Content-Type: application/json" -H "Authorization: Bearer <jwt_token>" -d '{"content":"Thrilled to announce I am humbled and honored to begin this transformational journey as a thought leader."}'
```

## 📊 API Documentation

### Interactive Documentation
- **Swagger UI** - http://localhost:8000/docs
- **ReDoc** - http://localhost:8000/redoc
- **OpenAPI Schema** - http://localhost:8000/openapi.json

### Key Endpoints
```python
# Authentication
POST /auth/google/login     # Google OAuth login
POST /auth/refresh          # Refresh JWT token

# LinkedIn Cringe-o-Meter
POST /api/v1/cringe/analyze # Analyze post and return structured cringe report
POST /auth/logout           # User logout

# Resume Roasting
POST /api/resume-roast      # Submit resume for AI feedback
GET /api/resume-roast/{id}  # Get roast results

# User Management
GET /api/users/me           # Get current user profile
PUT /api/users/me           # Update user profile

# Health & Monitoring
GET /health                 # Application health check
GET /metrics               # Performance metrics
```

## 🧪 Testing

### Test Structure
```bash
tests/
├── test_auth.py           # Authentication tests
├── test_resume_roast.py   # Resume roasting tests
├── test_database.py       # Database operation tests
└── conftest.py            # Test configuration
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v
```

## 📈 Monitoring & Observability

### LangSmith Integration
- **Trace Visualization** - LLM call flow analysis
- **Performance Metrics** - Response time tracking
- **Cost Analysis** - Token usage optimization
- **Error Tracking** - AI service failure analysis

### Application Monitoring
- **Health Checks** - Endpoint availability monitoring
- **Database Connections** - Connection pool management
- **Error Logging** - Structured application logs
- **Performance Metrics** - Response time analysis

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for new functionality
4. Implement feature with proper documentation
5. Run tests and ensure they pass
6. Commit changes (`git commit -m 'Add amazing feature'`)
7. Push to branch (`git push origin feature/amazing-feature`)
8. Open Pull Request

### Code Standards
- **PEP 8** - Python code style guidelines
- **Type Hints** - Full type annotation coverage
- **Docstrings** - Comprehensive documentation
- **Testing** - Unit and integration test coverage

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [LangChain Documentation](https://python.langchain.com/)
- [Azure Container Apps](https://docs.microsoft.com/azure/container-apps/)

---

**FaltooAI Backend** - Intelligent APIs powering productivity tools 🚀

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
