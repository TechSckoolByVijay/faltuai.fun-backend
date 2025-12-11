# Setup Backend Repository for Azure Container Registry
# PowerShell script to help setup backend as standalone repository

Write-Host "🐳 Setting up Backend for Azure Container Registry Deployment" -ForegroundColor Green
Write-Host "=" * 60

# Check if we're in the backend directory
if (!(Test-Path "app/main.py")) {
    Write-Host "❌ Error: Please run this script from the backend directory" -ForegroundColor Red
    Write-Host "Usage: cd backend; .\setup-acr.ps1"
    exit 1
}

# Variables
$RepoName = "faltuai-backend"
$GitHubUsername = Read-Host "Enter your GitHub username"
$AcrName = "faltuaicr"

if ([string]::IsNullOrEmpty($GitHubUsername)) {
    Write-Host "❌ GitHub username is required" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "📋 Setup Instructions:" -ForegroundColor Yellow
Write-Host "=" * 25

Write-Host ""
Write-Host "1. Create a new repository on GitHub:" -ForegroundColor Cyan
Write-Host "   - Go to https://github.com/new"
Write-Host "   - Repository name: $RepoName (or your preferred name)"
Write-Host "   - Make it public or private as needed"
Write-Host "   - Don't initialize with README (we'll push our own)"

Write-Host ""
Write-Host "2. Copy this backend directory to a new location:" -ForegroundColor Cyan
Write-Host "   mkdir ..\\$RepoName"
Write-Host "   Copy-Item -Recurse -Path . -Destination ..\\$RepoName\\"
Write-Host "   cd ..\\$RepoName"

Write-Host ""
Write-Host "3. Initialize git and connect to your new repo:" -ForegroundColor Cyan
Write-Host "   git init"
Write-Host "   git add ."
Write-Host "   git commit -m 'Initial backend setup'"
Write-Host "   git branch -M main"
Write-Host "   git remote add origin https://github.com/$GitHubUsername/$RepoName.git"
Write-Host "   git push -u origin main"

Write-Host ""
Write-Host "4. Setup Azure Container Registry secrets in GitHub:" -ForegroundColor Cyan
Write-Host "   - Go to your repo Settings → Secrets and variables → Actions"
Write-Host "   - Click 'New repository secret'"
Write-Host "   - Add these secrets:"
Write-Host "     • ACR_USERNAME: $AcrName"
Write-Host "     • ACR_PASSWORD: <get from: az acr credential show --name $AcrName>"

Write-Host ""
Write-Host "5. Get ACR credentials (run in Azure CLI):" -ForegroundColor Cyan
Write-Host "   az acr credential show --name $AcrName"

Write-Host ""
Write-Host "6. Enable Admin User (if needed):" -ForegroundColor Cyan
Write-Host "   az acr update --name $AcrName --admin-enabled true"

Write-Host ""
Write-Host "✅ After setup, your images will be available at:" -ForegroundColor Green
Write-Host "   $AcrName.azurecr.io/faltuai-backend:latest"

Write-Host ""
Write-Host "🚀 Deployment Options:" -ForegroundColor Blue
Write-Host "   - Azure Container Instances"
Write-Host "   - Azure App Service"
Write-Host "   - Azure Kubernetes Service"
Write-Host "   - Any Docker-compatible platform"

Write-Host ""
Write-Host "📚 For more details, see .github\\DEPLOYMENT.md" -ForegroundColor Blue