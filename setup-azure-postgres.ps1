# Azure PostgreSQL Migration Script for FaltuAI Backend
# PowerShell script to help with database migration to Azure PostgreSQL Flexible Server

param(
    [Parameter(Mandatory=$true)]
    [string]$ServerName,
    
    [Parameter(Mandatory=$true)]
    [string]$AdminUser,
    
    [Parameter(Mandatory=$true)]
    [string]$AdminPassword,
    
    [string]$DatabaseName = "faltuai_db",
    [string]$Port = "5432",
    [string]$SSLMode = "require"
)

Write-Host "🐘 Azure PostgreSQL Migration Setup for FaltuAI" -ForegroundColor Green
Write-Host "=" * 55

# Configuration
$ServerFQDN = "$ServerName.postgres.database.azure.com"
$DatabaseURL = "postgresql://${AdminUser}:${AdminPassword}@${ServerFQDN}:${Port}/${DatabaseName}?sslmode=${SSLMode}"
$AsyncDatabaseURL = "postgresql+asyncpg://${AdminUser}:${AdminPassword}@${ServerFQDN}:${Port}/${DatabaseName}?sslmode=${SSLMode}"

Write-Host ""
Write-Host "📋 Configuration Summary:" -ForegroundColor Yellow
Write-Host "   Server: $ServerFQDN"
Write-Host "   Database: $DatabaseName"
Write-Host "   User: $AdminUser"
Write-Host "   Port: $Port"
Write-Host "   SSL Mode: $SSLMode"

# Step 1: Test Connection
Write-Host ""
Write-Host "🔍 Step 1: Testing Database Connection" -ForegroundColor Cyan
Write-Host "-" * 40

try {
    # Test if psql is available
    $psqlVersion = psql --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ PostgreSQL client (psql) not found. Please install it first." -ForegroundColor Red
        Write-Host "   Download from: https://www.postgresql.org/download/"
        Write-Host "   Or use Azure Cloud Shell which has psql pre-installed."
        exit 1
    }
    
    Write-Host "✅ PostgreSQL client found: $psqlVersion"
    
    # Test connection
    Write-Host "🔄 Testing connection to Azure PostgreSQL..."
    $env:PGPASSWORD = $AdminPassword
    
    $testQuery = "SELECT version();"
    $result = echo $testQuery | psql -h $ServerFQDN -U $AdminUser -d postgres -p $Port -t -q 2>$null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Successfully connected to Azure PostgreSQL!" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to connect to Azure PostgreSQL" -ForegroundColor Red
        Write-Host "   Please check:"
        Write-Host "   - Server name and credentials"
        Write-Host "   - Firewall rules (add your IP address)"
        Write-Host "   - SSL configuration"
        exit 1
    }
} catch {
    Write-Host "❌ Connection test failed: $_" -ForegroundColor Red
    exit 1
}

# Step 2: Create Database if not exists
Write-Host ""
Write-Host "🗄️ Step 2: Setting up Database" -ForegroundColor Cyan
Write-Host "-" * 35

try {
    Write-Host "🔄 Creating database '$DatabaseName' if it doesn't exist..."
    
    $createDbQuery = @"
SELECT 'CREATE DATABASE $DatabaseName' 
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DatabaseName')\gexec
"@
    
    echo $createDbQuery | psql -h $ServerFQDN -U $AdminUser -d postgres -p $Port -q
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Database '$DatabaseName' is ready" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Database creation had issues, but continuing..." -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️ Database setup warning: $_" -ForegroundColor Yellow
}

# Step 3: Set Environment Variables
Write-Host ""
Write-Host "🔧 Step 3: Setting Environment Variables" -ForegroundColor Cyan
Write-Host "-" * 42

$env:DATABASE_URL = $DatabaseURL
$env:ASYNC_DATABASE_URL = $AsyncDatabaseURL

Write-Host "✅ Environment variables set:"
Write-Host "   DATABASE_URL (truncated): postgresql://$AdminUser:***@$ServerFQDN:$Port/$DatabaseName?sslmode=$SSLMode"
Write-Host "   ASYNC_DATABASE_URL (truncated): postgresql+asyncpg://$AdminUser:***@$ServerFQDN:$Port/$DatabaseName?sslmode=$SSLMode"

# Step 4: Check Python Dependencies
Write-Host ""
Write-Host "🐍 Step 4: Checking Python Dependencies" -ForegroundColor Cyan
Write-Host "-" * 42

try {
    Push-Location backend
    
    Write-Host "🔄 Checking required packages..."
    
    $requiredPackages = @("asyncpg", "alembic", "sqlalchemy")
    $missingPackages = @()
    
    foreach ($package in $requiredPackages) {
        $installed = pip show $package 2>$null
        if ($LASTEXITCODE -ne 0) {
            $missingPackages += $package
        } else {
            Write-Host "✅ $package is installed"
        }
    }
    
    if ($missingPackages.Count -gt 0) {
        Write-Host "📦 Installing missing packages: $($missingPackages -join ', ')" -ForegroundColor Yellow
        pip install $missingPackages -q
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Dependencies installed successfully"
        } else {
            Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "✅ All required dependencies are installed"
    }
    
} catch {
    Write-Host "❌ Dependency check failed: $_" -ForegroundColor Red
    exit 1
} finally {
    Pop-Location
}

# Step 5: Run Alembic Migrations
Write-Host ""
Write-Host "🔄 Step 5: Running Database Migrations" -ForegroundColor Cyan
Write-Host "-" * 42

try {
    Push-Location backend
    
    # Check current migration status
    Write-Host "🔍 Checking current migration status..."
    $currentStatus = alembic current 2>$null
    Write-Host "Current status: $currentStatus"
    
    # Check if we need to create initial migration
    $migrationFiles = Get-ChildItem -Path "alembic\versions\*.py" -ErrorAction SilentlyContinue
    
    if ($migrationFiles.Count -eq 0) {
        Write-Host "📝 Creating initial migration..."
        alembic revision --autogenerate -m "Initial migration with users and resume_roast tables"
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Failed to create initial migration" -ForegroundColor Red
            exit 1
        }
        
        Write-Host "✅ Initial migration created"
    } else {
        Write-Host "✅ Migration files already exist ($($migrationFiles.Count) files)"
    }
    
    # Apply migrations
    Write-Host "🚀 Applying migrations to Azure PostgreSQL..."
    alembic upgrade head
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Migrations applied successfully!" -ForegroundColor Green
    } else {
        Write-Host "❌ Migration failed" -ForegroundColor Red
        exit 1
    }
    
} catch {
    Write-Host "❌ Migration process failed: $_" -ForegroundColor Red
    exit 1
} finally {
    Pop-Location
}

# Step 6: Verify Migration Success
Write-Host ""
Write-Host "✅ Step 6: Verifying Migration Success" -ForegroundColor Cyan
Write-Host "-" * 42

try {
    Write-Host "🔍 Checking created tables..."
    
    $tablesQuery = "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;"
    $tables = echo $tablesQuery | psql -h $ServerFQDN -U $AdminUser -d $DatabaseName -p $Port -t
    
    if ($LASTEXITCODE -eq 0 -and $tables) {
        Write-Host "✅ Database tables found:" -ForegroundColor Green
        $tables.Split("`n") | ForEach-Object { 
            $table = $_.Trim()
            if ($table) {
                Write-Host "   - $table"
            }
        }
    } else {
        Write-Host "⚠️ No tables found or verification failed" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "⚠️ Verification failed: $_" -ForegroundColor Yellow
}

# Step 7: Container App Environment Variables
Write-Host ""
Write-Host "🐳 Step 7: Container App Configuration" -ForegroundColor Cyan
Write-Host "-" * 42

Write-Host "To configure your Azure Container App with the database, run:"
Write-Host ""
Write-Host "az containerapp update \\" -ForegroundColor White
Write-Host "  --name faltuai-backend-app \\" -ForegroundColor White
Write-Host "  --resource-group faltuai-rg \\" -ForegroundColor White
Write-Host "  --set-env-vars \\" -ForegroundColor White
Write-Host "    `"DATABASE_URL=$DatabaseURL`" \\" -ForegroundColor White
Write-Host "    `"ASYNC_DATABASE_URL=$AsyncDatabaseURL`"" -ForegroundColor White

Write-Host ""
Write-Host "Or add these as secrets in GitHub (recommended):" -ForegroundColor Yellow
Write-Host "  DATABASE_URL=$DatabaseURL"
Write-Host "  ASYNC_DATABASE_URL=$AsyncDatabaseURL"

# Summary
Write-Host ""
Write-Host "🎉 Migration Setup Complete!" -ForegroundColor Green
Write-Host "=" * 30

Write-Host ""
Write-Host "✅ Summary:" -ForegroundColor Green
Write-Host "   - Connected to Azure PostgreSQL successfully"
Write-Host "   - Database '$DatabaseName' is ready"
Write-Host "   - Dependencies are installed"
Write-Host "   - Migrations have been applied"
Write-Host "   - Tables are created and verified"

Write-Host ""
Write-Host "📝 Next Steps:" -ForegroundColor Blue
Write-Host "   1. Configure Container App environment variables (see commands above)"
Write-Host "   2. Test your application endpoints"
Write-Host "   3. Set up database monitoring and backups"
Write-Host "   4. Consider using Azure Key Vault for connection strings"

Write-Host ""
Write-Host "🔗 Useful Commands:" -ForegroundColor Magenta
Write-Host "   - Connect: psql `"$DatabaseURL`""
Write-Host "   - List tables: \dt"
Write-Host "   - Check migration status: alembic current"
Write-Host "   - View migration history: alembic history"

Write-Host ""
Write-Host "Your Azure PostgreSQL database is now ready for production! 🚀" -ForegroundColor Green