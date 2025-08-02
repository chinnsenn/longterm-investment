#!/bin/bash
# UV Development Run Script

set -e

echo "🛠️  Starting MarketFlow in Development Mode with UV..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ UV is not installed. Please install uv first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please copy .env.example to .env and configure it."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment with UV..."
    uv venv
fi

# Install or update dependencies with dev extras
echo "⬇️  Installing dependencies (including dev) with UV..."
uv pip install -e ".[dev]"

# Create data directory if it doesn't exist
mkdir -p data

# Run the application with debug flag
echo "🏃 Running MarketFlow in development mode..."
exec uv run python main.py --debug "$@"