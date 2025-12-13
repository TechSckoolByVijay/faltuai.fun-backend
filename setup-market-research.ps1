# Setup Script for Real Market Research System

Write-Host "=== Real Market Research System Setup ===" -ForegroundColor Cyan
Write-Host ""

# Check if .env file exists in root directory
$envFile = "../.env"
if (-not (Test-Path $envFile)) {
    Write-Host "ERROR: .env file not found in root directory!" -ForegroundColor Red
    Write-Host "Please create a .env file in the project root first." -ForegroundColor Yellow
    exit 1
}

Write-Host "Current API Configuration:" -ForegroundColor Yellow
Write-Host ""

# Read current env file
$envContent = Get-Content $envFile -Raw

# Check each API key
$apis = @(
    @{Name="Serper API"; EnvVar="SERPER_API_KEY"; Required=$true; Url="https://serper.dev/"},
    @{Name="YouTube Data API"; EnvVar="YOUTUBE_API_KEY"; Required=$false; Url="https://console.cloud.google.com/"},
    @{Name="GitHub Token"; EnvVar="GITHUB_TOKEN"; Required=$false; Url="https://github.com/settings/tokens"}
)

$missingRequired = $false

foreach ($api in $apis) {
    if ($envContent -match "$($api.EnvVar)=(.+)") {
        $value = $matches[1].Trim()
        if ($value -and $value -ne "") {
            Write-Host "✓ $($api.Name): Configured" -ForegroundColor Green
        } else {
            if ($api.Required) {
                Write-Host "✗ $($api.Name): MISSING (REQUIRED)" -ForegroundColor Red
                $missingRequired = $true
            } else {
                Write-Host "○ $($api.Name): Not configured (optional)" -ForegroundColor Yellow
            }
            Write-Host "  Get key from: $($api.Url)" -ForegroundColor Gray
        }
    } else {
        if ($api.Required) {
            Write-Host "✗ $($api.Name): NOT IN .env FILE (REQUIRED)" -ForegroundColor Red
            $missingRequired = $true
        } else {
            Write-Host "○ $($api.Name): Not in .env (optional)" -ForegroundColor Yellow
        }
        Write-Host "  Add to .env: $($api.EnvVar)=your_key_here" -ForegroundColor Gray
        Write-Host "  Get key from: $($api.Url)" -ForegroundColor Gray
    }
    Write-Host ""
}

if ($missingRequired) {
    Write-Host "⚠️  REQUIRED API keys are missing!" -ForegroundColor Red
    Write-Host "The system will not work without Serper API." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To get Serper API key:" -ForegroundColor Cyan
    Write-Host "1. Go to https://serper.dev/" -ForegroundColor White
    Write-Host "2. Sign up (get $5 free credit)" -ForegroundColor White
    Write-Host "3. Copy your API key" -ForegroundColor White
    Write-Host "4. Add to .env: SERPER_API_KEY=your_key_here" -ForegroundColor White
    Write-Host ""
    exit 1
}

Write-Host "=== Running Database Migration ===" -ForegroundColor Cyan
Write-Host ""

# Check if we're in backend directory
if (-not (Test-Path "alembic.ini")) {
    Write-Host "ERROR: Not in backend directory!" -ForegroundColor Red
    Write-Host "Please run this script from the backend directory." -ForegroundColor Yellow
    exit 1
}

# Create migration
Write-Host "Creating migration for market research cache..." -ForegroundColor Yellow
$migrationResult = docker exec backend-api alembic revision --autogenerate -m "Add market research cache table" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Migration created" -ForegroundColor Green
} else {
    Write-Host "✗ Migration creation failed" -ForegroundColor Red
    Write-Host $migrationResult
}

# Run migration
Write-Host "Running migration..." -ForegroundColor Yellow
$upgradeResult = docker exec backend-api alembic upgrade head 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Migration applied" -ForegroundColor Green
} else {
    Write-Host "✗ Migration failed" -ForegroundColor Red
    Write-Host $upgradeResult
}

Write-Host ""
Write-Host "=== Testing API Connections ===" -ForegroundColor Cyan
Write-Host ""

# Create test script
$testScript = @"
import asyncio
import sys
sys.path.append('/app')

from app.services.data_sources.serper_agent import serper_agent
from app.services.data_sources.github_trends_agent import github_trends_agent
from app.services.data_sources.youtube_agent import youtube_agent

async def test_apis():
    print('Testing Serper API...')
    try:
        result = await serper_agent.search('python developer jobs', num_results=5)
        if result.get('organic'):
            print(f'✓ Serper: Found {len(result["organic"])} results')
        else:
            print(f'✗ Serper: {result.get("error", "Unknown error")}')
    except Exception as e:
        print(f'✗ Serper: {e}')
    
    print('\nTesting GitHub API...')
    try:
        result = await github_trends_agent.search_repositories('python tutorial', per_page=5)
        print(f'✓ GitHub: Found {len(result)} repositories')
    except Exception as e:
        print(f'✗ GitHub: {e}')
    
    print('\nTesting YouTube API...')
    try:
        result = await youtube_agent.search_videos('python tutorial', max_results=5)
        if result:
            print(f'✓ YouTube: Found {len(result)} videos')
        else:
            print('○ YouTube: API key not configured (optional)')
    except Exception as e:
        print(f'○ YouTube: {e}')
    
    await serper_agent.close()
    await github_trends_agent.close()
    await youtube_agent.close()

asyncio.run(test_apis())
"@

$testScript | Out-File -FilePath "test_apis.py" -Encoding UTF8

# Run test
docker exec backend-api python test_apis.py

# Clean up
Remove-Item "test_apis.py" -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "=== Setup Complete! ===" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Restart backend: docker-compose restart backend-api" -ForegroundColor White
Write-Host "2. Test learning plan generation" -ForegroundColor White
Write-Host "3. Check REAL-MARKET-RESEARCH.md for detailed documentation" -ForegroundColor White
Write-Host ""
Write-Host "Cost estimate: ~$75/month for 1,000 learning plans" -ForegroundColor Yellow
Write-Host "With caching: ~$35-50/month" -ForegroundColor Yellow
Write-Host ""
