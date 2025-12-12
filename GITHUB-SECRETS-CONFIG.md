# GitHub Secrets Configuration for Azure Deployment

## 🔐 Required GitHub Secrets

Add these secrets to your GitHub repository's **"dev" environment**:

### 1. Database Configuration (CRITICAL - Just Added)
```
DATABASE_URL=postgresql://dbadmin:FaltuAIfun_p@55word@faltuaidb.postgres.database.azure.com:5432/faltuai_db?sslmode=require

ASYNC_DATABASE_URL=postgresql+asyncpg://dbadmin:FaltuAIfun_p@55word@faltuaidb.postgres.database.azure.com:5432/faltuai_db?ssl=require
```

### 2. Azure Container Registry (Already Set)
```
ACR_USERNAME=faltuaicr
ACR_PASSWORD=<get from: az acr credential show --name faltuaicr>
```

### 3. Azure Deployment
```
AZURE_CREDENTIALS=<JSON from service principal creation>
```

### 4. Google OAuth Configuration
```
GOOGLE_CLIENT_ID=<your-google-client-id>
GOOGLE_CLIENT_SECRET=<your-google-client-secret>
```

### 5. OpenAI Configuration
```
OPENAI_API_KEY=<your-openai-api-key>
```

### 6. JWT Security
```
JWT_SECRET_KEY=<generate-secure-random-key>
```

### 7. Frontend URL
```
FRONTEND_URL=https://faltooai.fun
```

### 8. LangSmith (Optional)
```
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=<your-langsmith-api-key>
LANGCHAIN_PROJECT=faltuai-fun
```

## 🚀 How to Add GitHub Secrets

1. Go to your repository: `https://github.com/TechSckoolByVijay/faltuai.fun-backend`
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Select **Environment secrets** tab
4. Choose **"dev" environment**
5. Click **"Add secret"** for each variable above

## 🛠️ Generate Missing Values

### JWT Secret Key
```bash
# Generate a secure random key
openssl rand -hex 32
# Or use Python
python -c "import secrets; print(secrets.token_hex(32))"
```

### Azure Service Principal (if not created)
```bash
az ad sp create-for-rbac \
  --name "faltuai-github-actions" \
  --role contributor \
  --scopes /subscriptions/$(az account show --query id -o tsv)/resourceGroups/faltuai-rg \
  --sdk-auth
```

### ACR Password (if needed)
```bash
az acr credential show --name faltuaicr --query passwords[0].value -o tsv
```

## 📋 Complete Secrets Checklist

- [ ] `DATABASE_URL` - Azure PostgreSQL connection
- [ ] `ASYNC_DATABASE_URL` - Async PostgreSQL connection  
- [ ] `ACR_USERNAME` - Container registry username
- [ ] `ACR_PASSWORD` - Container registry password
- [ ] `AZURE_CREDENTIALS` - Service principal JSON
- [ ] `GOOGLE_CLIENT_ID` - Google OAuth client ID
- [ ] `GOOGLE_CLIENT_SECRET` - Google OAuth client secret
- [ ] `OPENAI_API_KEY` - OpenAI API key
- [ ] `JWT_SECRET_KEY` - JWT signing secret
- [ ] `FRONTEND_URL` - Frontend GitHub Pages URL
- [ ] `LANGCHAIN_TRACING_V2` - LangSmith tracing (optional)
- [ ] `LANGCHAIN_API_KEY` - LangSmith API key (optional)
- [ ] `LANGCHAIN_PROJECT` - LangSmith project name (optional)

## 🎯 Deployment Flow

Once secrets are configured:

1. **Push to main branch** → Triggers GitHub Actions
2. **Build Docker image** → Push to ACR
3. **Deploy to Container Apps** → With all environment variables
4. **Application starts** → Connected to Azure PostgreSQL

## 🔍 Verify Deployment

After deployment, check:

1. **Container App logs**: 
   ```bash
   az containerapp logs show --name faltuai-backend-app --resource-group faltuai-rg --follow
   ```

2. **Database connectivity**: 
   ```bash
   curl https://faltuai.reddune-c0e74598.centralindia.azurecontainerapps.io/health
   ```

3. **API endpoints**:
   ```bash
   curl https://faltuai.reddune-c0e74598.centralindia.azurecontainerapps.io/
   ```

## ⚠️ Security Notes

- Never commit secrets to code
- Use GitHub environment protection rules
- Rotate secrets regularly
- Monitor access logs
- Use least-privilege principles

Your backend will now be deployed with full Azure PostgreSQL integration! 🚀