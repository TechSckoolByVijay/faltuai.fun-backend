# FaltooAI Platform 🚀

> **"Small Extras. Big Productivity"** - A comprehensive full-stack AI-powered productivity platform

**FaltooAI** is a modern, cloud-native platform that combines cutting-edge AI technologies with intuitive user experiences to deliver micro-productivity tools that make a big impact on daily workflows.

## 🛠️ Complete Tech Stack

### Frontend Technologies
- **React 18** - Modern UI library with Hooks and Context API
- **Vite** - Lightning-fast build tool and development server
- **Tailwind CSS** - Utility-first CSS framework
- **React Router** - Hash routing for GitHub Pages compatibility
- **GitHub Pages** - Static site hosting with custom domain (faltooai.fun)
- **GitHub Actions** - Automated CI/CD deployment pipeline

### Backend Technologies
- **FastAPI** - High-performance Python web framework
- **PostgreSQL** - Production-ready relational database
- **SQLAlchemy** - Python SQL toolkit and ORM
- **Alembic** - Database migration management
- **Azure Container Apps** - Serverless container hosting
- **Azure Container Registry** - Container image storage

### AI & Machine Learning
- **OpenAI GPT Models** - Advanced language processing and generation
- **LangChain** - LLM application development framework
- **LangSmith** - LLM monitoring, debugging, and performance analytics
- **Azure Document Intelligence** - PDF and document processing OCR

### Authentication & Security
- **Google OAuth 2.0** - Secure social authentication via Google Cloud
- **JWT Tokens** - Stateless session management
- **CORS Configuration** - Cross-origin request security
- **HTTPS Enforcement** - End-to-end encryption

### Development & Deployment
- **Docker & Docker Compose** - Containerization and orchestration
- **GitHub Actions** - Automated testing and deployment
- **ESLint & Black** - Code quality and formatting
- **Pytest** - Comprehensive testing framework

## 🏗️ Platform Architecture

```
FaltooAI Platform
│
├── Frontend (React + Tailwind)
│   ├── Landing Page - Marketing & Feature Showcase
│   ├── Dashboard - User Control Center
│   ├── Resume Roaster - AI-Powered Resume Feedback
│   ├── Feature Tools - Productivity Micro-Services
│   └── Authentication - Google OAuth Integration
│
├── Backend (FastAPI + PostgreSQL)
│   ├── Authentication Service - JWT & OAuth Management
│   ├── AI Services - OpenAI & LangChain Integration
│   ├── Document Processing - Azure Document Intelligence
│   ├── Database Layer - SQLAlchemy & PostgreSQL
│   └── LangSmith Monitoring - LLM Performance Tracking
│
└── Cloud Infrastructure
    ├── GitHub Pages (Frontend Hosting)
    ├── Azure Container Apps (Backend Hosting)
    ├── Azure PostgreSQL (Database)
    ├── Azure Container Registry (Image Storage)
    └── GitHub Actions (CI/CD Pipeline)
```

## ✨ Platform Features

### Core Productivity Tools
- **🔥 Resume Roaster** - AI-powered resume analysis with constructive feedback
- **⚡ Feature 1** - Advanced productivity tool with intelligent automation
- **📋 Snippet Wizard** - Smart code and text snippet management (Coming Soon)
- **📹 Auto Caption** - Intelligent video captioning with timestamps (Coming Soon)
- **💡 Idea Spark** - Creative brainstorming assistant (Coming Soon)

### Platform Capabilities
- **🔐 Secure Authentication** - Google OAuth with JWT session management
- **🎨 Adaptive Theming** - Dark/Light mode with persistent preferences
- **📱 Responsive Design** - Seamless mobile and desktop experiences
- **🚀 Real-time Processing** - Fast AI-powered responses
- **📊 Usage Analytics** - LangSmith monitoring and performance insights
- **🔒 Data Security** - End-to-end encryption and secure data handling

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Git

### Setup & Run

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd faltuai.fun
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your Google OAuth credentials (optional for testing)
   ```

3. **Start the application**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## 🔧 Development Setup

### Without Docker

**Backend Setup:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend Setup:**
```bash
cd frontend
npm install
npm run dev
```

### With Docker (Recommended)

```bash
docker-compose up --build
```

## 🌐 Google OAuth Setup

To enable real Google authentication:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Set authorized redirect URI: `http://localhost:8000/auth/google/callback`
6. Update `.env` file with your credentials:
   ```
   GOOGLE_CLIENT_ID=your-actual-client-id
   GOOGLE_CLIENT_SECRET=your-actual-client-secret
   ```

## 📁 Project Structure

### Frontend (`/frontend`)

```
src/
├── auth/              # Authentication utilities
│   ├── authService.js # Authentication service
│   └── useAuth.js     # Authentication React hook
├── components/        # Reusable UI components
│   ├── Navbar.jsx     # Navigation component
│   └── ProtectedRoute.jsx # Route protection
├── features/          # Feature-specific components
│   └── feature1/      # Feature 1 implementation
├── pages/             # Page components
│   ├── LandingPage.jsx    # Home/landing page
│   ├── Dashboard.jsx      # User dashboard
│   └── LoginCallback.jsx  # OAuth callback handler
├── config/            # Configuration files
│   └── backend.js     # Backend API configuration
└── App.jsx           # Main application component
```

### Backend (`/backend`)

```
app/
├── auth/              # Authentication modules
│   ├── google_oauth.py # Google OAuth handler
│   └── tokens.py       # JWT token management
├── api/               # API route modules
│   └── feature1/       # Feature 1 API endpoints
├── core/              # Core utilities
│   └── security.py     # Security dependencies
├── schemas/           # Pydantic data models
│   └── user.py         # User schemas
├── db/                # Database configuration
│   └── database.py     # Database setup (future)
├── config.py          # Application configuration
└── main.py           # FastAPI application entry
```

## 🔄 API Endpoints

### Authentication
- `GET /auth/google/login` - Initiate Google OAuth
- `GET /auth/google/callback` - OAuth callback handler
- `POST /auth/logout` - Logout (client-side token removal)

### Feature 1
- `GET /api/v1/feature1/hello` - Protected hello endpoint
- `GET /api/v1/feature1/status` - Feature status information

### System
- `GET /` - API information
- `GET /health` - Health check
- `GET /docs` - API documentation (development only)

## 🎯 Adding New Features

### Frontend Feature

1. Create feature directory: `frontend/src/features/feature2/`
2. Add feature component: `Feature2Page.jsx`
3. Add route in `App.jsx`
4. Update navigation in `Navbar.jsx`

### Backend Feature

1. Create API module: `backend/app/api/feature2/router.py`
2. Include router in `main.py`
3. Add authentication as needed

## 🛠️ Technology Stack

### Frontend
- **React 18** - Modern React with Hooks
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **React Router v6** - Client-side routing
- **Axios** - HTTP client for API calls

### Backend
- **FastAPI** - Modern, fast Python web framework
- **Pydantic** - Data validation using Python type hints
- **Authlib** - OAuth library for Google authentication
- **PyJWT** - JSON Web Token implementation
- **Uvicorn** - ASGI server implementation

### DevOps
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration

## 🔒 Security Features

- JWT token-based authentication
- Google OAuth 2.0 integration
- CORS protection
- Input validation with Pydantic
- Protected API routes
- Secure token storage

## 📝 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | `dummy-google-id` |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret | `dummy-google-secret` |
| `FRONTEND_URL` | Frontend application URL | `http://localhost:5173` |
| `VITE_BACKEND_URL` | Backend API URL | `http://localhost:8000` |
| `JWT_SECRET_KEY` | JWT signing secret | `dummysecret` |
| `DEBUG` | Enable debug mode | `true` |

## 🚀 Deployment

### Production Environment

1. **Update environment variables:**
   ```bash
   # Set production URLs and secure secrets
   FRONTEND_URL=https://your-domain.com
   VITE_BACKEND_URL=https://api.your-domain.com
   JWT_SECRET_KEY=your-super-secure-secret
   DEBUG=false
   ```

2. **Build and deploy:**
   ```bash
   docker-compose -f docker-compose.prod.yml up --build
   ```

### GitHub Pages (Frontend Only)

The frontend is configured with HashRouter for GitHub Pages compatibility.

## 🧪 Testing

```bash
# Backend tests (when implemented)
cd backend
pytest

# Frontend tests (when implemented)  
cd frontend
npm test
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes
4. Commit: `git commit -m 'Add new feature'`
5. Push: `git push origin feature/new-feature`
6. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

1. **OAuth not working:**
   - Check Google OAuth credentials in `.env`
   - Verify redirect URI in Google Console
   - Ensure backend is running on port 8000

2. **Docker issues:**
   - Run `docker-compose down` and `docker-compose up --build`
   - Check port conflicts (8000, 5173)

3. **Frontend not connecting to backend:**
   - Verify `VITE_BACKEND_URL` in environment
   - Check CORS settings in backend

## 📞 Support

For support and questions:
- Create an issue in this repository
- Check the API documentation at `/docs`
- Review the troubleshooting section above

---

Built with ❤️ using React, FastAPI, and modern web technologies.