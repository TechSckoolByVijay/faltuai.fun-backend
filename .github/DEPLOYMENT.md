# Backend Deployment to Azure Container Registry

This document explains how the FastAPI backend is automatically built and deployed as Docker images to Azure Container Registry.

## Overview

- **Registry**: `faltuaicr.azurecr.io`
- **Image Name**: `faltuai-backend`
- **Supported Platforms**: `linux/amd64`, `linux/arm64`

## Workflow Triggers

The Docker build workflow runs on:

- **Push to main/develop**: Builds and pushes with branch name tag + `latest` (main only)
- **Tags (v*)**: Builds and pushes with semantic version tags
- **Pull Requests**: Builds only (no push) for validation
- **Manual**: Can be triggered manually from GitHub Actions

## Image Tags

Images are tagged with:

- `main` - Latest main branch build
- `develop` - Latest develop branch build  
- `v1.0.0`, `v1.0`, `v1` - Semantic version tags
- `commit-abc1234` - Git commit SHA
- `latest` - Latest stable release (main branch)
- `pr-123` - Pull request builds

## Required Secrets

Set these secrets in your GitHub repository settings:

### Azure Container Registry Credentials

```bash
# Get ACR credentials
az acr credential show --name faltuaicr

# Set in GitHub Secrets:
ACR_USERNAME=faltuaicr  # Registry name
ACR_PASSWORD=<password>  # From ACR credential show
```

### Setting GitHub Secrets

1. Go to **Repository Settings → Secrets and variables → Actions**
2. Click **New repository secret**
3. Add the following secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `ACR_USERNAME` | `faltuaicr` | Azure Container Registry username |
| `ACR_PASSWORD` | `<your-acr-password>` | Azure Container Registry password |

## Usage Examples

### Pull Latest Image

```bash
# Login to ACR
az acr login --name faltuaicr

# Pull latest image
docker pull faltuaicr.azurecr.io/faltuai-backend:latest
```

### Run Container

```bash
# Run the backend container
docker run -d \
  --name faltuai-backend \
  -p 8000:8000 \
  -e OPENAI_API_KEY="your-key" \
  -e GOOGLE_CLIENT_ID="your-client-id" \
  -e GOOGLE_CLIENT_SECRET="your-secret" \
  faltuaicr.azurecr.io/faltuai-backend:latest
```

### Azure Container Instances

```bash
# Deploy to Azure Container Instances
az container create \
  --resource-group your-rg \
  --name faltuai-backend \
  --image faltuaicr.azurecr.io/faltuai-backend:latest \
  --registry-login-server faltuaicr.azurecr.io \
  --registry-username faltuaicr \
  --registry-password <password> \
  --dns-name-label faltuai-backend \
  --ports 8000 \
  --environment-variables \
    OPENAI_API_KEY="your-key" \
    GOOGLE_CLIENT_ID="your-client-id"
```

### Azure App Service

```bash
# Deploy to Azure App Service
az webapp create \
  --resource-group your-rg \
  --plan your-app-service-plan \
  --name faltuai-backend \
  --deployment-container-image-name faltuaicr.azurecr.io/faltuai-backend:latest

# Configure ACR credentials
az webapp config container set \
  --name faltuai-backend \
  --resource-group your-rg \
  --docker-custom-image-name faltuaicr.azurecr.io/faltuai-backend:latest \
  --docker-registry-server-url https://faltuaicr.azurecr.io \
  --docker-registry-server-user faltuaicr \
  --docker-registry-server-password <password>
```

## Workflow Features

- ✅ **Multi-platform builds** (AMD64 + ARM64)
- ✅ **Docker layer caching** for faster builds
- ✅ **Automatic tagging** based on git refs
- ✅ **Pull request validation** (build without push)
- ✅ **Security scanning** ready
- ✅ **Build summaries** with pull commands

## Environment Variables

The container expects these environment variables:

```bash
# Required
OPENAI_API_KEY=sk-...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...

# Optional (with defaults)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/db
JWT_SECRET_KEY=your-jwt-secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Monitoring

- **GitHub Actions**: Monitor builds at `/actions`
- **ACR**: View images at Azure Portal → Container Registry
- **Logs**: Check container logs with `docker logs <container-id>`

## Troubleshooting

### Build Failures

1. Check GitHub Actions logs
2. Verify ACR credentials in secrets
3. Ensure Dockerfile is valid
4. Check for dependency issues

### Push Failures

1. Verify ACR permissions
2. Check if registry exists
3. Validate credentials

### Runtime Issues

1. Check environment variables
2. Verify port mappings
3. Review application logs

For more details, see the [workflow file](.github/workflows/docker-build-push.yml).