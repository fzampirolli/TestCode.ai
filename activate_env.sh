#!/bin/bash
# Quick script to activate the virtual environment

if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Run the setup script first."
    exit 1
fi

source .venv/bin/activate
echo "✅ Virtual environment activated"
echo "📍 Current environment: $VIRTUAL_ENV"
echo "🐍 Python version: $(python --version)"
echo ""
echo "To deactivate, simply run: deactivate"
