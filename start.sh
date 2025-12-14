#!/bin/bash

# FaltuAI Fun - Quick Start Script
# This script helps you get the application running quickly

echo "🚀 FaltuAI Fun - Quick Start"
echo "=============================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

# Create .env file from example if it doesn't exist
if [ ! -f .env ]; then
    echo "📋 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created. You can edit it to add real Google OAuth credentials."
else
    echo "✅ .env file already exists."
fi

# Start the application
echo ""
echo "🐳 Starting the application with Docker Compose..."
echo "   This may take a few minutes on first run..."
echo ""

docker-compose up --build

echo ""
echo "🎉 Application started!"
echo ""
echo "📱 Frontend: http://localhost:5173"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "To stop the application, press Ctrl+C"
echo ""
echo "🔧 To set up Google OAuth:"
echo "   1. Visit https://console.cloud.google.com/"
echo "   2. Create OAuth 2.0 credentials"
echo "   3. Update .env file with real credentials"
echo "   4. Restart with: docker-compose up --build"