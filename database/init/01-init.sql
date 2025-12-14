-- Database initialization script for FaltuAI
-- This script is run when PostgreSQL container starts for the first time

-- Create the database if it doesn't exist (usually handled by Docker environment)
-- Note: This script runs as postgres user and the database is already created
-- by POSTGRES_DB environment variable

-- Set default timezone
SET timezone = 'UTC';

-- Create extensions that might be useful
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Grant privileges to the application user (created by Docker)
-- The user is created by POSTGRES_USER environment variable
GRANT ALL PRIVILEGES ON DATABASE faltuai_db TO faltuai_user;

-- Switch to the application database
\c faltuai_db

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO faltuai_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO faltuai_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO faltuai_user;

-- Note: Tables will be created by Alembic migrations from the FastAPI application