# GitHub Environment Variables Check Script
# PowerShell script to verify all required secrets are configured

param(
    [Parameter(Mandatory=$true)]
    [string]$GitHubToken,
    
    [string]$Repository = "TechSckoolByVijay/faltuai.fun-backend",
    [string]$Environment = "dev"
)

Write-Host "🔍 GitHub Environment Variables Check" -ForegroundColor Green
Write-Host "=" * 40

# Set GitHub token
$env:GH_TOKEN = $GitHubToken

Write-Host "📋 Repository: $Repository" -ForegroundColor Yellow
Write-Host "🌍 Environment: $Environment" -ForegroundColor Yellow
Write-Host ""

# List of required secrets
$RequiredSecrets = @(
    "DATABASE_URL",
    "ASYNC_DATABASE_URL", 
    "ACR_USERNAME",
    "ACR_PASSWORD",
    "AZURE_CREDENTIALS",
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
    "OPENAI_API_KEY",
    "JWT_SECRET_KEY",
    "FRONTEND_URL",
    "LANGCHAIN_TRACING_V2",
    "LANGCHAIN_API_KEY",
    "LANGCHAIN_PROJECT"
)

Write-Host "🔐 Checking GitHub Environment Secrets..." -ForegroundColor Cyan
Write-Host "-" * 35

try {
    # Get all environment secrets
    $secrets = gh secret list --env $Environment --repo $Repository --json name,updatedAt | ConvertFrom-Json
    
    $foundSecrets = @{}
    foreach ($secret in $secrets) {
        $foundSecrets[$secret.name] = $secret.updatedAt
    }
    
    Write-Host "Found $($secrets.Count) secrets in environment '$Environment'" -ForegroundColor Blue
    Write-Host ""
    
    $missingSecrets = @()
    $foundCount = 0
    
    foreach ($secretName in $RequiredSecrets) {
        if ($foundSecrets.ContainsKey($secretName)) {
            $updatedAt = [DateTime]::Parse($foundSecrets[$secretName]).ToString("yyyy-MM-dd HH:mm")
            Write-Host "✅ $secretName (updated: $updatedAt)" -ForegroundColor Green
            $foundCount++
        } else {
            Write-Host "❌ $secretName (MISSING)" -ForegroundColor Red
            $missingSecrets += $secretName
        }
    }
    
    Write-Host ""
    Write-Host "📊 Summary:" -ForegroundColor Blue
    Write-Host "   Found: $foundCount/$($RequiredSecrets.Count) secrets"
    Write-Host "   Missing: $($missingSecrets.Count) secrets"
    
    if ($missingSecrets.Count -eq 0) {
        Write-Host ""
        Write-Host "🎉 All required secrets are configured!" -ForegroundColor Green
        Write-Host "✅ Your repository is ready for deployment!"
        Write-Host ""
        Write-Host "🚀 Next steps:"
        Write-Host "   1. Push your code to main branch"
        Write-Host "   2. GitHub Actions will automatically:"
        Write-Host "      • Build Docker image"
        Write-Host "      • Push to Azure Container Registry"
        Write-Host "      • Deploy to Azure Container Apps"
        Write-Host "   3. Monitor deployment in Actions tab"
    } else {
        Write-Host ""
        Write-Host "⚠️ Missing secrets found!" -ForegroundColor Yellow
        Write-Host "❌ Missing secrets:" -ForegroundColor Red
        foreach ($secret in $missingSecrets) {
            Write-Host "   • $secret"
        }
        Write-Host ""
        Write-Host "🔧 To fix this, run:"
        Write-Host "   .\setup-github-secrets.ps1 -GitHubToken 'your_token_here'"
    }
    
    # Show extra secrets (not in our required list)
    $extraSecrets = @()
    foreach ($secret in $secrets) {
        if ($secret.name -notin $RequiredSecrets) {
            $extraSecrets += $secret.name
        }
    }
    
    if ($extraSecrets.Count -gt 0) {
        Write-Host ""
        Write-Host "📝 Additional secrets found:" -ForegroundColor Magenta
        foreach ($secret in $extraSecrets) {
            Write-Host "   • $secret"
        }
    }
    
} catch {
    Write-Host "❌ Error checking secrets: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 Possible issues:"
    Write-Host "   • GitHub token expired or invalid"
    Write-Host "   • Repository name incorrect"
    Write-Host "   • Environment name incorrect"
    Write-Host "   • GitHub CLI not authenticated"
}

Write-Host ""
Write-Host "🔗 Useful links:" -ForegroundColor Cyan
Write-Host "   • Repository Secrets: https://github.com/$Repository/settings/environments"
Write-Host "   • GitHub Actions: https://github.com/$Repository/actions"
Write-Host "   • Container App URL: https://faltuai.reddune-c0e74598.centralindia.azurecontainerapps.io"