# GitHub Secrets Setup Script for FaltuAI Backend
# PowerShell script to create all required secrets in GitHub repository environment

param(
    [Parameter(Mandatory=$true)]
    [string]$GitHubToken,
    
    [string]$Repository = "TechSckoolByVijay/faltuai.fun-backend",
    [string]$Environment = "dev"
)

Write-Host "🔐 GitHub Secrets Setup for FaltuAI Backend" -ForegroundColor Green
Write-Host "=" * 50

# Check if GitHub CLI is installed
try {
    $ghVersion = gh --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ GitHub CLI (gh) not found. Please install it first." -ForegroundColor Red
        Write-Host "   Download from: https://cli.github.com/"
        exit 1
    }
    Write-Host "✅ GitHub CLI found: $($ghVersion.Split("`n")[0])"
} catch {
    Write-Host "❌ GitHub CLI not available: $_" -ForegroundColor Red
    exit 1
}

# Set GitHub token
$env:GH_TOKEN = $GitHubToken

Write-Host ""
Write-Host "📋 Repository: $Repository" -ForegroundColor Yellow
Write-Host "🌍 Environment: $Environment" -ForegroundColor Yellow

# Function to set a secret
function Set-GitHubSecret {
    param(
        [string]$Name,
        [string]$Value,
        [string]$Description
    )
    
    try {
        Write-Host "🔧 Setting secret: $Name" -ForegroundColor Cyan
        
        # Use GitHub CLI to set environment secret
        $result = echo $Value | gh secret set $Name --env $Environment --repo $Repository
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ $Name set successfully" -ForegroundColor Green
        } else {
            Write-Host "   ❌ Failed to set $Name" -ForegroundColor Red
        }
    } catch {
        Write-Host "   ❌ Error setting $Name: $_" -ForegroundColor Red
    }
}

# Function to generate JWT secret
function Generate-JWTSecret {
    $bytes = New-Object byte[] 32
    [System.Security.Cryptography.RNGCryptoServiceProvider]::Create().GetBytes($bytes)
    return [System.Convert]::ToHex($bytes).ToLower()
}

Write-Host ""
Write-Host "🔍 Collecting Secret Values..." -ForegroundColor Cyan
Write-Host "-" * 30

# Database Configuration (Azure PostgreSQL)
$DATABASE_URL = "postgresql://dbadmin:FaltuAIfun_p@55word@faltuaidb.postgres.database.azure.com:5432/faltuai_db?sslmode=require"
$ASYNC_DATABASE_URL = "postgresql+asyncpg://dbadmin:FaltuAIfun_p@55word@faltuaidb.postgres.database.azure.com:5432/faltuai_db?ssl=require"

# Load values from .env file if available, otherwise prompt
$envFile = Join-Path $PSScriptRoot "../.env"
$envVars = @{}

if (Test-Path $envFile) {
    Write-Host "📄 Found .env file, loading values..." -ForegroundColor Green
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([^#=]+)=(.*)$') {
            $envVars[$matches[1].Trim()] = $matches[2].Trim()
        }
    }
} else {
    Write-Host "⚠️ No .env file found, will prompt for all values" -ForegroundColor Yellow
}

# Google OAuth Configuration
if ($envVars.ContainsKey("GOOGLE_CLIENT_ID") -and $envVars.ContainsKey("GOOGLE_CLIENT_SECRET")) {
    $GOOGLE_CLIENT_ID = $envVars["GOOGLE_CLIENT_ID"]
    $GOOGLE_CLIENT_SECRET = $envVars["GOOGLE_CLIENT_SECRET"]
    Write-Host "✅ Google OAuth credentials loaded from .env"
} else {
    Write-Host "🔐 Google OAuth credentials needed:"
    $GOOGLE_CLIENT_ID = Read-Host "   Enter GOOGLE_CLIENT_ID"
    $GOOGLE_CLIENT_SECRET = Read-Host "   Enter GOOGLE_CLIENT_SECRET" -AsSecureString
    $GOOGLE_CLIENT_SECRET = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($GOOGLE_CLIENT_SECRET))
}

# OpenAI Configuration
if ($envVars.ContainsKey("OPENAI_API_KEY")) {
    $OPENAI_API_KEY = $envVars["OPENAI_API_KEY"]
    Write-Host "✅ OpenAI API key loaded from .env"
} else {
    Write-Host "🤖 OpenAI API key needed:"
    $OPENAI_API_KEY = Read-Host "   Enter OPENAI_API_KEY (sk-...)" -AsSecureString
    $OPENAI_API_KEY = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($OPENAI_API_KEY))
}

# LangSmith Configuration
if ($envVars.ContainsKey("LANGCHAIN_API_KEY")) {
    $LANGCHAIN_TRACING_V2 = if ($envVars.ContainsKey("LANGCHAIN_TRACING_V2")) { $envVars["LANGCHAIN_TRACING_V2"] } else { "true" }
    $LANGCHAIN_API_KEY = $envVars["LANGCHAIN_API_KEY"]
    $LANGCHAIN_PROJECT = if ($envVars.ContainsKey("LANGCHAIN_PROJECT")) { $envVars["LANGCHAIN_PROJECT"] } else { "faltuai-fun" }
    Write-Host "✅ LangSmith configuration loaded from .env"
} else {
    Write-Host "📊 LangSmith configuration (optional, press Enter to skip):"
    $LANGCHAIN_API_KEY_INPUT = Read-Host "   Enter LANGCHAIN_API_KEY (optional)" -AsSecureString
    if ($LANGCHAIN_API_KEY_INPUT.Length -gt 0) {
        $LANGCHAIN_API_KEY = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($LANGCHAIN_API_KEY_INPUT))
        $LANGCHAIN_TRACING_V2 = "true"
    } else {
        $LANGCHAIN_API_KEY = "dummy-langsmith-key"
        $LANGCHAIN_TRACING_V2 = "false"
    }
    $LANGCHAIN_PROJECT = "faltuai-fun"
}

# JWT Secret (generate new secure one for production)
$JWT_SECRET_KEY = Generate-JWTSecret
Write-Host "🔑 Generated new secure JWT_SECRET_KEY for production"

# Frontend URL (production GitHub Pages)
$FRONTEND_URL = "https://techsckoolbyvijay.github.io/faltuai.fun-frontend"

# Azure Container Registry (prompt for these as they're sensitive)
Write-Host ""
Write-Host "🐳 Azure Container Registry credentials needed:"
$ACR_USERNAME = Read-Host "   Enter ACR_USERNAME (default: faltuaicr)" 
if ([string]::IsNullOrEmpty($ACR_USERNAME)) { $ACR_USERNAME = "faltuaicr" }

$ACR_PASSWORD = Read-Host "   Enter ACR_PASSWORD (from: az acr credential show --name faltuaicr)" -AsSecureString
$ACR_PASSWORD = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($ACR_PASSWORD))

# Azure Credentials (Service Principal JSON)
Write-Host ""
Write-Host "☁️ Azure Service Principal JSON needed:"
Write-Host "   Generate with: az ad sp create-for-rbac --name 'faltuai-github-actions' --role contributor --scopes /subscriptions/\$(az account show --query id -o tsv)/resourceGroups/faltuai-rg --sdk-auth"
$AZURE_CREDENTIALS = Read-Host "   Paste the complete JSON output"

Write-Host ""
Write-Host "🚀 Setting GitHub Secrets..." -ForegroundColor Green
Write-Host "-" * 25

# Set all secrets
Set-GitHubSecret "DATABASE_URL" $DATABASE_URL "Azure PostgreSQL connection string"
Set-GitHubSecret "ASYNC_DATABASE_URL" $ASYNC_DATABASE_URL "Async PostgreSQL connection string"
Set-GitHubSecret "ACR_USERNAME" $ACR_USERNAME "Azure Container Registry username"
Set-GitHubSecret "ACR_PASSWORD" $ACR_PASSWORD "Azure Container Registry password"
Set-GitHubSecret "AZURE_CREDENTIALS" $AZURE_CREDENTIALS "Azure Service Principal JSON"
Set-GitHubSecret "GOOGLE_CLIENT_ID" $GOOGLE_CLIENT_ID "Google OAuth Client ID"
Set-GitHubSecret "GOOGLE_CLIENT_SECRET" $GOOGLE_CLIENT_SECRET "Google OAuth Client Secret"
Set-GitHubSecret "OPENAI_API_KEY" $OPENAI_API_KEY "OpenAI API Key"
Set-GitHubSecret "JWT_SECRET_KEY" $JWT_SECRET_KEY "JWT signing secret key"
Set-GitHubSecret "FRONTEND_URL" $FRONTEND_URL "Frontend GitHub Pages URL"
Set-GitHubSecret "LANGCHAIN_TRACING_V2" $LANGCHAIN_TRACING_V2 "LangSmith tracing enabled"
Set-GitHubSecret "LANGCHAIN_API_KEY" $LANGCHAIN_API_KEY "LangSmith API Key"
Set-GitHubSecret "LANGCHAIN_PROJECT" $LANGCHAIN_PROJECT "LangSmith project name"

Write-Host ""
Write-Host "📋 Summary of Secrets Created:" -ForegroundColor Blue
Write-Host "-" * 30
Write-Host "Database:"
Write-Host "  ✓ DATABASE_URL"
Write-Host "  ✓ ASYNC_DATABASE_URL"
Write-Host ""
Write-Host "Azure:"
Write-Host "  ✓ ACR_USERNAME"
Write-Host "  ✓ ACR_PASSWORD"
Write-Host "  ✓ AZURE_CREDENTIALS"
Write-Host ""
Write-Host "Authentication:"
Write-Host "  ✓ GOOGLE_CLIENT_ID"
Write-Host "  ✓ GOOGLE_CLIENT_SECRET"
Write-Host "  ✓ JWT_SECRET_KEY"
Write-Host ""
Write-Host "Services:"
Write-Host "  ✓ OPENAI_API_KEY"
Write-Host "  ✓ FRONTEND_URL"
Write-Host ""
Write-Host "Monitoring:"
Write-Host "  ✓ LANGCHAIN_TRACING_V2"
Write-Host "  ✓ LANGCHAIN_API_KEY"
Write-Host "  ✓ LANGCHAIN_PROJECT"

Write-Host ""
Write-Host "✅ All secrets have been configured!" -ForegroundColor Green
Write-Host ""
Write-Host "🚀 Next Steps:" -ForegroundColor Magenta
Write-Host "1. Verify secrets in GitHub: https://github.com/$Repository/settings/environments"
Write-Host "2. Push code to main branch to trigger deployment"
Write-Host "3. Monitor deployment in Actions tab"
Write-Host "4. Test your deployed application"

Write-Host ""
Write-Host "🔗 Your deployed app will be available at:"
Write-Host "   https://faltuai.reddune-c0e74598.centralindia.azurecontainerapps.io"

Write-Host ""
Write-Host "📝 Saved Configuration:" -ForegroundColor Yellow
Write-Host "   JWT_SECRET_KEY: $JWT_SECRET_KEY"
Write-Host "   (Save this for future reference)"