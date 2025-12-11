# Azure PostgreSQL Setup and Migration Guide

## 🐘 Setting up Azure PostgreSQL Flexible Server with FaltuAI Backend

### Step 1: Get Your Azure PostgreSQL Connection Details

You'll need these details from your Azure PostgreSQL Flexible Server:

1. **Server Name**: `your-server-name.postgres.database.azure.com`
2. **Database Name**: `faltuai_db` (or your chosen name)
3. **Username**: `your_admin_user`
4. **Password**: `your_secure_password`
5. **Port**: `5432` (default)
6. **SSL Mode**: `require` (Azure default)

### Step 2: Create Database Connection String

For Azure PostgreSQL Flexible Server, your connection string should be:

```bash
# Standard PostgreSQL URL
DATABASE_URL=postgresql://your_admin_user:your_secure_password@your-server-name.postgres.database.azure.com:5432/faltuai_db?sslmode=require

# Async version for SQLAlchemy (used by the app)
ASYNC_DATABASE_URL=postgresql+asyncpg://your_admin_user:your_secure_password@your-server-name.postgres.database.azure.com:5432/faltuai_db?sslmode=require
```

### Step 3: Configure Environment Variables

**For Local Development/Migration:**
```bash
# Add to your .env file or export directly
export DATABASE_URL="postgresql://your_admin_user:your_secure_password@your-server-name.postgres.database.azure.com:5432/faltuai_db?sslmode=require"
```

**For Azure Container App (Production):**
```bash
# Add these as environment variables in Container App
DATABASE_URL=postgresql://your_admin_user:your_secure_password@your-server-name.postgres.database.azure.com:5432/faltuai_db?sslmode=require
ASYNC_DATABASE_URL=postgresql+asyncpg://your_admin_user:your_secure_password@your-server-name.postgres.database.azure.com:5432/faltuai_db?sslmode=require
```

### Step 4: Test Connection

First, test if you can connect to your Azure PostgreSQL:

```bash
# Install psql client if not already installed
# Windows: Download from PostgreSQL website
# Linux: apt-get install postgresql-client
# macOS: brew install postgresql

# Test connection
psql "postgresql://your_admin_user:your_secure_password@your-server-name.postgres.database.azure.com:5432/faltuai_db?sslmode=require"
```

### Step 5: Install Required Dependencies

Ensure you have the required Python packages:

```bash
cd backend
pip install asyncpg psycopg2-binary alembic
```

### Step 6: Update Alembic Configuration

Your `alembic.ini` should automatically pick up the DATABASE_URL from environment.
If needed, you can temporarily update it:

```ini
# In backend/alembic.ini
sqlalchemy.url = postgresql+asyncpg://your_admin_user:your_secure_password@your-server-name.postgres.database.azure.com:5432/faltuai_db?sslmode=require
```

### Step 7: Create and Run Migrations

Now you can create and apply migrations:

```bash
cd backend

# Check current migration status
alembic current

# Create initial migration (if not already created)
alembic revision --autogenerate -m "Initial migration with users and resume_roast tables"

# Apply migrations to Azure PostgreSQL
alembic upgrade head
```

### Step 8: Verify Migration Success

Connect to your database and verify tables were created:

```sql
-- Connect via psql and run:
\l                          -- List databases
\c faltuai_db              -- Connect to your database
\dt                        -- List tables
\d users                   -- Describe users table
\d resume_roast_sessions   -- Describe resume roast table
```

### Step 9: Configure Container App Environment Variables

Add these environment variables to your Azure Container App:

```bash
az containerapp update \
  --name faltuai-backend-app \
  --resource-group faltuai-rg \
  --set-env-vars \
    "DATABASE_URL=postgresql://your_admin_user:your_secure_password@your-server-name.postgres.database.azure.com:5432/faltuai_db?sslmode=require" \
    "ASYNC_DATABASE_URL=postgresql+asyncpg://your_admin_user:your_secure_password@your-server-name.postgres.database.azure.com:5432/faltuai_db?sslmode=require"
```

## 🔧 Alternative: Use Azure CLI for Database Setup

### Create Database and User (if needed)

```bash
# Connect to your PostgreSQL server
az postgres flexible-server connect \
  --name your-server-name \
  --admin-user your_admin_user \
  --database-name postgres

# Then in PostgreSQL prompt:
CREATE DATABASE faltuai_db;
CREATE USER faltuai_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE faltuai_db TO faltuai_user;
\q
```

## 🐳 Using the Migration Script

You can also use the provided migration script:

```bash
# Set environment variable
export DATABASE_URL="postgresql://your_admin_user:your_secure_password@your-server-name.postgres.database.azure.com:5432/faltuai_db?sslmode=require"

# Run migration script
python migrate_db.py
```

## 🔒 Security Best Practices

### 1. Use Connection Pooling
```python
# Already configured in database.py
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=10,
    max_overflow=20
)
```

### 2. Use Azure Key Vault (Recommended)
```bash
# Store sensitive values in Key Vault
az keyvault secret set \
  --vault-name your-keyvault \
  --name "database-connection-string" \
  --value "postgresql://..."
```

### 3. Use Managed Identity
Configure your Container App to use managed identity for database access.

## 🚨 Troubleshooting Common Issues

### 1. SSL Connection Issues
```bash
# If SSL issues, try different SSL modes:
?sslmode=require
?sslmode=prefer
?sslmode=disable  # Not recommended for production
```

### 2. Firewall Issues
```bash
# Add your IP to PostgreSQL firewall rules
az postgres flexible-server firewall-rule create \
  --resource-group your-rg \
  --name your-server-name \
  --rule-name "AllowMyIP" \
  --start-ip-address YOUR_IP \
  --end-ip-address YOUR_IP
```

### 3. Connection Timeout
```bash
# Add connection timeout to URL
?connect_timeout=30
```

### 4. Migration Conflicts
```bash
# If migrations fail, check current state
alembic current
alembic history
alembic show head

# Force to specific revision if needed
alembic stamp head
```

## ✅ Verification Checklist

- [ ] Azure PostgreSQL Flexible Server is running
- [ ] Database `faltuai_db` exists
- [ ] User has proper permissions
- [ ] Firewall allows connections
- [ ] SSL certificate is valid
- [ ] Environment variables are set
- [ ] Dependencies are installed
- [ ] Migrations run successfully
- [ ] Container App can connect to database
- [ ] Application starts without database errors

## 📚 Next Steps

After successful migration:

1. **Test Application**: Verify all endpoints work with database
2. **Set up Monitoring**: Configure Azure monitoring for database
3. **Backup Strategy**: Set up automated backups
4. **Performance Tuning**: Configure connection pools and indexes
5. **Security Audit**: Review permissions and access controls

Your Azure PostgreSQL database is now ready for production use! 🚀