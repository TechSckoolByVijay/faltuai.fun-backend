# Quick Setup Command for GitHub Secrets
# Run this command to set up all GitHub secrets using your .env values

# STEP 1: Get GitHub Personal Access Token
# 1. Go to https://github.com/settings/tokens
# 2. Click "Generate new token (classic)"
# 3. Select scopes: repo, admin:org (for repository secrets)
# 4. Copy the token

# STEP 2: Get Azure Credentials
# Run this to get your Azure service principal:
az ad sp create-for-rbac --name "faltuai-github-actions" --role contributor --scopes /subscriptions/$(az account show --query id -o tsv)/resourceGroups/faltuai-rg --sdk-auth

# STEP 3: Get ACR Password
# Run this to get your container registry password:
az acr credential show --name faltuaicr --query "passwords[0].value" -o tsv

# STEP 4: Run the Setup Script
# Replace YOUR_GITHUB_TOKEN with your actual token:
.\setup-github-secrets.ps1 -GitHubToken "YOUR_GITHUB_TOKEN"

# STEP 5: Verify Setup
# Check that all secrets are configured:
.\check-github-secrets.ps1 -GitHubToken "YOUR_GITHUB_TOKEN"

# STEP 6: Deploy
# Push to main branch to trigger deployment:
git push origin main

# Your app will be available at:
# https://faltuai.reddune-c0e74598.centralindia.azurecontainerapps.io