# GitHub Copilot Instructions — BACKEND (FastAPI)

You are generating a FastAPI backend with Google OAuth, JWT authentication, and modular feature routing.

==================================================
PROJECT STRUCTURE
==================================================

app/
    main.py
    config.py
    auth/
      google_oauth.py
      tokens.py
    api/
      feature1/
        router.py
    core/
      security.py
    schemas/
      user.py
    db/
      database.py
  requirements.txt
  Dockerfile

==================================================
GENERAL BACKEND RULES
==================================================

- Always follow FastAPI best practices
- Use APIRouter for all routes
- Use Dependency Injection for JWT verification
- Use environment variables via config.py
- Never hardcode secrets or URLs — use settings from config

==================================================
GOOGLE OAUTH RULES
==================================================

- /auth/google/login:
  Redirect user to Google OAuth consent page using Authlib

- /auth/google/callback:
  - Exchange authorization code for tokens
  - Extract user email + profile
  - Create JWT using create_access_token()
  - Redirect to `${settings.FRONTEND_URL}/#/auth/callback?token=<jwt>`

==================================================
JWT RULES
==================================================

- Always sign JWT using:
  - SECRET: settings.JWT_SECRET_KEY
  - ALGO: settings.JWT_ALGORITHM

- Payload format:
  { "sub": email, "name": name }

- Expire tokens in 8 hours

==================================================
PROTECTED ROUTES RULES
==================================================

Use:

from app.core.security import verify_jwt

@router.get("/example")
def example(user=Depends(verify_jwt)):
    return {...}

==================================================
FEATURE DEVELOPMENT RULES
==================================================

Every new feature must have:

backend/app/api/<featureName>/router.py

Define:

router = APIRouter(prefix="/<featureName>")

All new features must be registered in main.py:

app.include_router(featureName_router)

==================================================
CORS RULES
==================================================

Allow:

- http://localhost:5173
- Github Pages domain (later)

==================================================
DOCKER RULES
==================================================

- Use python:3.11-slim
- Install dependencies from requirements.txt
- Run with Uvicorn:
    CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

==================================================
END OF BACKEND INSTRUCTIONS
==================================================
