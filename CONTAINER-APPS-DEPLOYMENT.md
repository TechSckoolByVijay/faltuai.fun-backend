# Azure Container Apps Deployment Guide

## Overview

This repository includes automated deployment to Azure Container Apps using GitHub Actions. Every push to the main branch will:

1. **Build** Docker image and push to Azure Container Registry (ACR)
2. **Deploy** automatically to Azure Container Apps
3. **Create** new revision with zero-downtime deployment

## Best Practices for Always Latest Code

### 🔄 Continuous Deployment Strategy

- **Automatic Triggers**: Push to `main` branch triggers build → deploy
- **Latest Tag**: Always deploys `latest` tag for main branch
- **Revision Management**: Container Apps automatically creates new revisions
- **Zero Downtime**: Traffic switches to new revision seamlessly

### 🏷️ Image Tagging Strategy

```yaml
# Our workflow creates these tags:
- faltuaicr.azurecr.io/faltuai-backend:latest          # Always latest main
- faltuaicr.azurecr.io/faltuai-backend:main            # Branch name
- faltuaicr.azurecr.io/faltuai-backend:commit-abc123   # Commit SHA
- faltuaicr.azurecr.io/faltuai-backend:v1.0.0         # Semantic versions
```

## Setup Instructions

### 1. Azure Infrastructure Setup

Run the PowerShell setup script:
```powershell
.\setup-container-apps.ps1
```

Or manually execute these Azure CLI commands:

```bash
# Variables
RESOURCE_GROUP="faltuai-rg"
LOCATION="eastus"
CONTAINER_APP_ENV="faltuai-env"
CONTAINER_APP_NAME="faltuai-backend-app"
ACR_NAME="faltuaicr"

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Container Apps environment
az containerapp env create \
  --name $CONTAINER_APP_ENV \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# Create Container App
az containerapp create \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment $CONTAINER_APP_ENV \
  --image $ACR_NAME.azurecr.io/faltuai-backend:latest \
  --target-port 8000 \
  --ingress external \
  --registry-server $ACR_NAME.azurecr.io \
  --registry-username $ACR_NAME \
  --registry-password $(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv) \
  --cpu 1.0 \
  --memory 2.0Gi \
  --min-replicas 1 \
  --max-replicas 3
```

### 2. Google OAuth Configuration

**Update Google Cloud Console** with your Container App URL:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to APIs & Services → Credentials
3. Edit your OAuth 2.0 Client ID
4. Add authorized redirect URI:
   ```
   https://faltuai.reddune-c0e74598.centralindia.azurecontainerapps.io/auth/google/callback
   ```

### 3. GitHub Secrets Setup

Create Azure service principal for GitHub Actions:

```bash
az ad sp create-for-rbac \
  --name "faltuai-github-actions" \
  --role contributor \
  --scopes /subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP \
  --sdk-auth
```

Add the JSON output as `AZURE_CREDENTIALS` secret in GitHub:
- Go to Repository Settings → Secrets and variables → Actions
- Click "New repository secret"
- Name: `AZURE_CREDENTIALS`
- Value: [JSON output from above command]

### 4. Required GitHub Secrets

Make sure these secrets are set in your dev environment:

| Secret Name | Description | How to Get |
|-------------|-------------|------------|
| `ACR_USERNAME` | Azure Container Registry username | `faltuaicr` |
| `ACR_PASSWORD` | Azure Container Registry password | `az acr credential show --name faltuaicr` |
| `AZURE_CREDENTIALS` | Service principal credentials | See setup above |

## Deployment Workflow

### Automatic Deployment (Recommended)

1. **Push to main branch**:
   ```bash
   git push origin main
   ```

2. **GitHub Actions will**:
   - Build Docker image
   - Push to ACR with multiple tags
   - Deploy to Container Apps (main branch only)
   - Create new revision automatically

3. **Zero-downtime deployment**:
   - New revision gets 100% traffic
   - Old revision remains for rollback
   - Health checks ensure stability

### Manual Deployment

Trigger deployment manually:
```bash
# Via GitHub UI: Actions → Build and Push → Run workflow
# Or via Azure CLI:
az containerapp update \
  --name faltuai-backend-app \
  --resource-group faltuai-rg \
  --image faltuaicr.azurecr.io/faltuai-backend:latest
```

## Monitoring & Management

### Access Your App

After deployment, your app will be available at:
```
https://faltuai-backend-app.faltuai-env.eastus.azurecontainerapps.io
```

### View Deployments

```bash
# List revisions
az containerapp revision list \
  --name faltuai-backend-app \
  --resource-group faltuai-rg

# View logs
az containerapp logs show \
  --name faltuai-backend-app \
  --resource-group faltuai-rg \
  --follow
```

### Scale Configuration

```bash
# Update scaling rules
az containerapp update \
  --name faltuai-backend-app \
  --resource-group faltuai-rg \
  --min-replicas 2 \
  --max-replicas 10
```

## Rollback Strategy

### Quick Rollback
```bash
# List revisions to find previous version
az containerapp revision list --name faltuai-backend-app --resource-group faltuai-rg

# Split traffic to previous revision
az containerapp ingress traffic set \
  --name faltuai-backend-app \
  --resource-group faltuai-rg \
  --revision-weight [old-revision-name]=100 [current-revision]=0
```

### Rollback via Re-deployment
```bash
# Deploy specific image version
az containerapp update \
  --name faltuai-backend-app \
  --resource-group faltuai-rg \
  --image faltuaicr.azurecr.io/faltuai-backend:commit-[previous-sha]
```

## Environment Variables

Configure app settings:
```bash
az containerapp update \
  --name faltuai-backend-app \
  --resource-group faltuai-rg \
  --set-env-vars \
    "DATABASE_URL=postgresql://..." \
    "API_KEY=secretvalue" \
    "ENV=production"
```

## Troubleshooting

### Common Issues

1. **Deployment fails**: Check Azure credentials and resource names
2. **App not accessible**: Verify ingress is enabled and target port is correct
3. **Image pull errors**: Ensure ACR credentials are correct
4. **Health check failures**: Check app starts correctly on port 8000

### Debug Commands

```bash
# Check container app status
az containerapp show --name faltuai-backend-app --resource-group faltuai-rg

# View recent logs
az containerapp logs show --name faltuai-backend-app --resource-group faltuai-rg --tail 100

# Check revision status
az containerapp revision list --name faltuai-backend-app --resource-group faltuai-rg
```

## Cost Optimization

- **Auto-scaling**: Scales to 0 when no traffic (saves money)
- **Resource limits**: Configured for 1 CPU, 2GB RAM per replica
- **Min replicas**: Set to 1 for always-available service
- **Max replicas**: Set to 3 to control costs

Your backend is now configured for continuous deployment with best practices! 🚀