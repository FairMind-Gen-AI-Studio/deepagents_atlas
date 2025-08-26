#!/usr/bin/env python3
"""
Test script to verify OpenPipe ART installation and functionality.
Run this to diagnose OpenPipe ART installation issues.
"""

import sys
import os
from pathlib import Path

print("=" * 60)
print("OpenPipe ART Installation Test")
print("=" * 60)

# Check Python version
print(f"\n1. Python Version: {sys.version}")
print(f"   Python Executable: {sys.executable}")

# Check if we're in a virtual environment
print(f"\n2. Virtual Environment:")
if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
    print(f"   ✅ Running in virtual environment")
    print(f"   Environment: {sys.prefix}")
else:
    print(f"   ⚠️  Not in virtual environment (or conda base)")

# Test basic imports
print(f"\n3. Testing Core Imports:")

dependencies = {
    "langchain": "LangChain",
    "langgraph": "LangGraph", 
    "langchain_openai": "LangChain OpenAI",
    "langchain_anthropic": "LangChain Anthropic",
    "wandb": "Weights & Biases",
    "weave": "Weave",
}

for module, name in dependencies.items():
    try:
        __import__(module)
        print(f"   ✅ {name} imported successfully")
    except ImportError as e:
        print(f"   ❌ {name} import failed: {e}")

# Test OpenPipe ART import
print(f"\n4. Testing OpenPipe ART:")
try:
    import art
    print(f"   ✅ art module imported successfully")
    print(f"   Version: {getattr(art, '__version__', 'unknown')}")
    
    # Test init_chat_model import
    try:
        from art.langgraph import init_chat_model
        print(f"   ✅ init_chat_model imported successfully")
        
        # Test wrapping a mock model
        try:
            from langchain_openai import ChatOpenAI
            
            # Create a minimal model (won't actually call API)
            mock_model = ChatOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key="test_key",
                model="test_model",
                temperature=0.7
            )
            
            # Try to wrap it
            wrapped_model = init_chat_model(
                mock_model,
                project_name="test_project"
            )
            
            print(f"   ✅ Model wrapping succeeded")
            print(f"   Wrapped model type: {type(wrapped_model).__name__}")
            
        except Exception as e:
            print(f"   ⚠️  Model wrapping failed: {e}")
            
    except ImportError as e:
        print(f"   ❌ init_chat_model import failed: {e}")
        
except ImportError as e:
    print(f"   ❌ art module import failed: {e}")
    print(f"\n   Detailed error:")
    import traceback
    traceback.print_exc()

# Check environment variables
print(f"\n5. Environment Variables:")
env_vars = {
    "ENABLE_OPENPIPE_ART": "OpenPipe ART Enable Flag",
    "OPENPIPE_PROJECT": "OpenPipe Project Name",
    "OPENROUTER_API_KEY": "OpenRouter API Key",
    "ANTHROPIC_API_KEY": "Anthropic API Key",
    "OPENAI_API_KEY": "OpenAI API Key",
}

for var, desc in env_vars.items():
    value = os.getenv(var)
    if value:
        if "KEY" in var:
            # Mask API keys
            masked = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
            print(f"   ✅ {var}: {masked}")
        else:
            print(f"   ✅ {var}: {value}")
    else:
        print(f"   ⚠️  {var}: Not set")

# Try to import our model wrapper
print(f"\n6. Testing Atlas V1 ART Components:")
sys.path.insert(0, str(Path(__file__).parent))

try:
    from reinforcement.model_wrapper import get_art_enabled_model
    print(f"   ✅ model_wrapper imported successfully")
    
    # Try to create a model
    try:
        model = get_art_enabled_model()
        print(f"   ✅ Model created: {type(model).__name__}")
        
        # Check if it's wrapped
        if "art" in str(type(model)).lower() or "openpipe" in str(type(model)).lower():
            print(f"   ✅ Model is ART-wrapped!")
        else:
            print(f"   ⚠️  Model is not ART-wrapped (check ENABLE_OPENPIPE_ART env var)")
            
    except Exception as e:
        print(f"   ❌ Model creation failed: {e}")
        
except ImportError as e:
    print(f"   ❌ model_wrapper import failed: {e}")

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

# Determine status
can_use_art = False
try:
    from art.langgraph import init_chat_model
    can_use_art = True
    status = "✅ OpenPipe ART is installed and importable"
except:
    status = "❌ OpenPipe ART is NOT installed or cannot be imported"

print(status)

if not can_use_art:
    print("\nTo install OpenPipe ART, try:")
    print("  pip install openpipe-art[langgraph] --no-deps")
    print("  pip install wandb weave gql graphql-core")
    print("\nOr for minimal installation:")
    print("  pip install openpipe-art --no-deps")
    print("  pip install wandb weave")
else:
    if os.getenv("ENABLE_OPENPIPE_ART", "false").lower() != "true":
        print("\n⚠️  OpenPipe ART is installed but not enabled!")
        print("Set ENABLE_OPENPIPE_ART=true in your .env file to activate it.")

print("=" * 60)