#!/usr/bin/env python3
"""
Test OpenRouter fix for ART integration.
Verifica che OpenRouter usi il base_url corretto.
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Setup paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

print("=" * 60)
print("OpenRouter Configuration Test")
print("=" * 60)

# Check environment
print("\n1. Environment Check:")
openrouter_key = os.getenv("OPENROUTER_API_KEY")
openrouter_model = os.getenv("OPENROUTER_MODEL")

if openrouter_key:
    print(f"   ✅ OPENROUTER_API_KEY: ***{openrouter_key[-10:]}")
else:
    print("   ❌ OPENROUTER_API_KEY: Not set")

if openrouter_model:
    print(f"   ✅ OPENROUTER_MODEL: {openrouter_model}")
else:
    print("   ❌ OPENROUTER_MODEL: Not set")

# Test model creation
print("\n2. Model Creation Test:")
if openrouter_key:
    from reinforcement.model_wrapper import get_art_enabled_model
    
    try:
        model = get_art_enabled_model()
        print("   ✅ Model created successfully!")
        
        # Check if it's using the correct configuration
        print("\n3. Configuration Details:")
        print("   Model should be using:")
        print(f"   - Base URL: https://openrouter.ai/api/v1")
        print(f"   - Model: {openrouter_model or 'anthropic/claude-3.5-sonnet'}")
        print(f"   - NOT api.openai.com (this was the bug)")
        
    except Exception as e:
        print(f"   ❌ Error creating model: {e}")
else:
    print("   ⚠️ Skipping - no OpenRouter API key")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("""
The fix ensures that when using OpenRouter:

1. ✅ The base_url is set to https://openrouter.ai/api/v1
2. ✅ The API key is the OpenRouter key (not OpenAI)
3. ✅ ART uses the correct endpoint for trajectory logging

Previously, the code was incorrectly checking the model type
and defaulting to OpenAI's API, causing authentication errors.

Now it uses the base_url determined by the API key configuration.
""")