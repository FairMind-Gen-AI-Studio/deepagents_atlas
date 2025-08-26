#!/bin/bash
# Installation script for OpenPipe ART with Atlas V1
# This script handles the complex dependency issues with OpenPipe ART

echo "=========================================="
echo "OpenPipe ART Installation for Atlas V1"
echo "=========================================="

# Check if we're in a virtual environment
if [[ -z "$VIRTUAL_ENV" ]] && [[ -z "$CONDA_DEFAULT_ENV" ]]; then
    echo "⚠️  WARNING: Not in a virtual environment!"
    echo "It's recommended to use a virtual environment:"
    echo "  conda create -n atlas_art python=3.12"
    echo "  conda activate atlas_art"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "Step 1: Installing base dependencies..."
echo "-----------------------------------------"
pip install langchain>=0.2.0 langgraph>=0.1.0 langchain-anthropic>=0.1.0 langchain-openai>=0.1.0

echo ""
echo "Step 2: Installing utilities..."
echo "-----------------------------------------"
pip install pydantic>=2.0.0 pydantic-settings>=2.0.0 python-dotenv>=1.0.0 pyyaml>=6.0.0

echo ""
echo "Step 3: Installing data processing libraries..."
echo "-----------------------------------------"
pip install numpy>=1.24.0 pandas>=2.0.0 jsonlines>=3.1.0

echo ""
echo "Step 4: Attempting OpenPipe ART installation..."
echo "-----------------------------------------"

# Try full installation first
echo "Trying full OpenPipe ART installation..."
if pip install openpipe-art[langgraph] 2>/dev/null; then
    echo "✅ OpenPipe ART installed successfully with langgraph extra!"
else
    echo "⚠️  Full installation failed, trying minimal installation..."
    
    # Try without extras
    if pip install openpipe-art --no-deps 2>/dev/null; then
        echo "✅ OpenPipe ART core installed (without extras)"
        echo "Installing required dependencies..."
        pip install wandb weave gql graphql-core 2>/dev/null
    else
        echo "❌ OpenPipe ART installation failed"
        echo ""
        echo "Manual installation steps:"
        echo "1. Try: pip install openpipe-art==0.4.8 --no-deps"
        echo "2. Then: pip install wandb weave"
        echo ""
        echo "The system will still work without OpenPipe ART,"
        echo "but reinforcement learning features won't be available."
    fi
fi

echo ""
echo "Step 5: Installing LangGraph CLI..."
echo "-----------------------------------------"
pip install langgraph-cli

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="

# Test the installation
echo ""
echo "Testing installation..."
python test_openpipe.py

echo ""
echo "Next steps:"
echo "1. Copy .env.example to .env and configure your API keys"
echo "2. Run: langgraph dev"
echo "3. Open http://localhost:8123 in your browser"
echo ""
echo "To enable OpenPipe ART, set in your .env file:"
echo "  ENABLE_OPENPIPE_ART=true"