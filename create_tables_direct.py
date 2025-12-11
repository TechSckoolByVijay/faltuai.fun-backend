#!/usr/bin/env python3
"""
Direct table creation for Azure PostgreSQL without Alembic
"""
import asyncio
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

import asyncpg

# SQL to create all tables based on your models
CREATE_TABLES_SQL = """
-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    google_id VARCHAR(255) UNIQUE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

-- Create resume_roast_sessions table
CREATE TABLE IF NOT EXISTS resume_roast_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    roasting_style VARCHAR(50) NOT NULL,
    original_filename VARCHAR(255),
    extracted_text TEXT,
    roasted_content TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Create user_activity_logs table
CREATE TABLE IF NOT EXISTS user_activity_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create system_metrics table
CREATE TABLE IF NOT EXISTS system_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value NUMERIC,
    metric_unit VARCHAR(20),
    tags JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create Alembic version table for future migrations
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Insert initial version (we'll mark this as the base migration)
INSERT INTO alembic_version (version_num) 
VALUES ('base_manual_creation')
ON CONFLICT (version_num) DO NOTHING;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);
CREATE INDEX IF NOT EXISTS idx_resume_roast_sessions_user_id ON resume_roast_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_resume_roast_sessions_session_token ON resume_roast_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_user_id ON user_activity_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_action ON user_activity_logs(action);
CREATE INDEX IF NOT EXISTS idx_system_metrics_metric_name ON system_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_system_metrics_created_at ON system_metrics(created_at);
"""

async def create_tables_directly():
    """Create tables directly using SQL"""
    try:
        print("🚀 Creating tables directly in Azure PostgreSQL...")
        
        # Connect to database
        conn = await asyncpg.connect(
            host="faltuaidb.postgres.database.azure.com",
            port=5432,
            user="dbadmin",
            password="FaltuAIfun_p@55word",
            database="faltuai_db",
            ssl='require'
        )
        
        print("✅ Connected to database successfully")
        
        # Execute table creation SQL
        print("📝 Creating tables...")
        await conn.execute(CREATE_TABLES_SQL)
        
        print("✅ Tables created successfully!")
        
        # Verify tables were created
        tables = await conn.fetch("""
            SELECT tablename, schemaname
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        
        print(f"\n📊 Created {len(tables)} tables:")
        for table in tables:
            print(f"   ✓ {table['tablename']}")
            
        # Check Alembic version
        version = await conn.fetchval("SELECT version_num FROM alembic_version")
        print(f"\n🔖 Alembic version: {version}")
        
        # Get table details
        print("\n📋 Table Details:")
        for table in tables:
            if table['tablename'] != 'alembic_version':
                columns = await conn.fetch(f"""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = '{table['tablename']}'
                    AND table_schema = 'public'
                    ORDER BY ordinal_position
                """)
                print(f"\n   {table['tablename']} ({len(columns)} columns):")
                for col in columns:
                    nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                    print(f"     - {col['column_name']}: {col['data_type']} {nullable}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

async def test_table_operations():
    """Test basic CRUD operations on created tables"""
    try:
        print("\n🧪 Testing table operations...")
        
        conn = await asyncpg.connect(
            host="faltuaidb.postgres.database.azure.com",
            port=5432,
            user="dbadmin",
            password="FaltuAIfun_p@55word",
            database="faltuai_db",
            ssl='require'
        )
        
        # Test inserting a user
        user_id = await conn.fetchval("""
            INSERT INTO users (email, name, google_id)
            VALUES ($1, $2, $3)
            RETURNING id
        """, "test@example.com", "Test User", "google_test_123")
        
        print(f"✅ Created test user with ID: {user_id}")
        
        # Test selecting the user
        user = await conn.fetchrow("""
            SELECT * FROM users WHERE id = $1
        """, user_id)
        
        print(f"✅ Retrieved user: {user['name']} ({user['email']})")
        
        # Test creating a resume roast session
        session_id = await conn.fetchval("""
            INSERT INTO resume_roast_sessions (user_id, session_token, roasting_style, status)
            VALUES ($1, $2, $3, $4)
            RETURNING id
        """, user_id, "test_session_123", "professional", "pending")
        
        print(f"✅ Created resume roast session with ID: {session_id}")
        
        # Test activity log
        await conn.execute("""
            INSERT INTO user_activity_logs (user_id, action, resource_type, resource_id)
            VALUES ($1, $2, $3, $4)
        """, user_id, "test_action", "resume_session", str(session_id))
        
        print(f"✅ Created activity log entry")
        
        # Test system metrics
        await conn.execute("""
            INSERT INTO system_metrics (metric_name, metric_value, metric_unit)
            VALUES ($1, $2, $3)
        """, "test_metric", 42.5, "units")
        
        print(f"✅ Created system metric entry")
        
        # Clean up test data
        await conn.execute("DELETE FROM user_activity_logs WHERE user_id = $1", user_id)
        await conn.execute("DELETE FROM resume_roast_sessions WHERE user_id = $1", user_id)
        await conn.execute("DELETE FROM users WHERE id = $1", user_id)
        await conn.execute("DELETE FROM system_metrics WHERE metric_name = 'test_metric'")
        
        print("✅ Test data cleaned up")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error testing tables: {e}")
        return False

async def main():
    """Main function"""
    print("🐘 Azure PostgreSQL Direct Table Creation")
    print("=" * 45)
    
    # Create tables
    if not await create_tables_directly():
        print("\n❌ Table creation failed")
        return
    
    # Test operations
    if not await test_table_operations():
        print("\n❌ Table testing failed")
        return
    
    print("\n🎉 Database setup completed successfully!")
    print("\nYour database is now ready with:")
    print("✓ Users table for authentication")
    print("✓ Resume roast sessions table")
    print("✓ User activity logs table") 
    print("✓ System metrics table")
    print("✓ Alembic version tracking")
    print("✓ Performance indexes")
    
    print("\n📝 Next Steps:")
    print("1. Update your Container App with database environment variables")
    print("2. Test your application endpoints")
    print("3. Set up proper Alembic migrations for future schema changes")
    
    print("\n🔗 Connection String for Container App:")
    print("DATABASE_URL=postgresql://dbadmin:FaltuAIfun_p@55word@faltuaidb.postgres.database.azure.com:5432/faltuai_db?sslmode=require")
    print("ASYNC_DATABASE_URL=postgresql+asyncpg://dbadmin:FaltuAIfun_p@55word@faltuaidb.postgres.database.azure.com:5432/faltuai_db?ssl=require")

if __name__ == "__main__":
    asyncio.run(main())