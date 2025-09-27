#!/bin/bash

# AI Agent Platform Setup Script

set -e

echo "🚀 AI Agent Platform Setup"
echo "========================="

# Check for required tools
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "❌ $1 is not installed. Please install it first."
        exit 1
    fi
}

echo "Checking prerequisites..."
check_command docker
check_command docker-compose
check_command node
check_command python3

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your OPENAI_API_KEY"
    echo "   Press Enter to continue after adding the key..."
    read
fi

# Check if OPENAI_API_KEY is set
source .env
if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" == "your-openai-api-key-here" ]; then
    echo "❌ OPENAI_API_KEY not set in .env file"
    echo "   Please add your OpenAI API key to the .env file"
    exit 1
fi

# Generate SECRET_KEY if not set
if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" == "your-secret-key-change-this-in-production" ]; then
    echo "🔐 Generating SECRET_KEY..."
    SECRET_KEY=$(openssl rand -hex 32)
    sed -i.bak "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
    echo "✅ SECRET_KEY generated and saved to .env"
fi

# Install backend dependencies
echo "📦 Installing backend dependencies..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend
npm install
npm install tailwindcss-animate
cd ..

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p backend/data
mkdir -p logs

# Build Docker images
echo "🐳 Building Docker images..."
docker-compose build

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the application:"
echo "  1. With Docker:     docker-compose up -d"
echo "  2. Without Docker:"
echo "     - Backend:       cd backend && python -m app.main"
echo "     - Frontend:      cd frontend && npm run dev"
echo ""
echo "Access the application:"
echo "  - Frontend:        http://localhost:3000"
echo "  - Backend API:     http://localhost:8000"
echo "  - API Docs:        http://localhost:8000/docs"
echo ""
echo "Default login (demo mode):"
echo "  - Username: any username"
echo "  - Password: any password"
echo ""
echo "⚠️  For production, please:"
echo "  - Use a real authentication system"
echo "  - Set up HTTPS"
echo "  - Use PostgreSQL instead of SQLite"
echo "  - Review DEPLOYMENT.md for full instructions"