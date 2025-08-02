#!/bin/bash
# UV Production Run Script

set -e

echo "🚀 Starting MarketFlow with UV..."

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

# Install or update dependencies
echo "⬇️  Installing dependencies with UV..."
uv pip install -e .

# Create data directory if it doesn't exist
mkdir -p data

# Run the application
echo "🏃 Running MarketFlow..."
exec uv run python main.py "$@"