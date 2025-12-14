@echo off
REM FaltuAI Fun - Quick Start Script for Windows
REM This script helps you get the application running quickly

echo 🚀 FaltuAI Fun - Quick Start
echo ==============================

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not installed. Please install Docker first.
    echo    Visit: https://docs.docker.com/get-docker/
    pause
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose is not installed. Please install Docker Compose first.
    echo    Visit: https://docs.docker.com/compose/install/
    pause
    exit /b 1
)

REM Create .env file from example if it doesn't exist
if not exist .env (
    echo 📋 Creating .env file from template...
    copy .env.example .env >nul
    echo ✅ .env file created. You can edit it to add real Google OAuth credentials.
) else (
    echo ✅ .env file already exists.
)

REM Start the application
echo.
echo 🐳 Starting the application with Docker Compose...
echo    This may take a few minutes on first run...
echo.

docker-compose up --build

echo.
echo 🎉 Application started!
echo.
echo 📱 Frontend: http://localhost:5173
echo 🔧 Backend API: http://localhost:8000
echo 📚 API Docs: http://localhost:8000/docs
echo.
echo To stop the application, press Ctrl+C
echo.
echo 🔧 To set up Google OAuth:
echo    1. Visit https://console.cloud.google.com/
echo    2. Create OAuth 2.0 credentials
echo    3. Update .env file with real credentials
echo    4. Restart with: docker-compose up --build
pause