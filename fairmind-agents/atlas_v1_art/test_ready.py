#!/usr/bin/env python3
"""
Final readiness test for Atlas V1 ART with LangGraph.
"""

import os
import sys
import warnings
from pathlib import Path

# Suppress async warnings
warnings.filterwarnings('ignore', message='.*async.*')
warnings.filterwarnings('ignore', message='.*RuntimeError.*')
warnings.filterwarnings('ignore', message='.*Exception ignored.*')

# Setup paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))

# Set minimal logging
import logging
logging.basicConfig(level=logging.WARNING, format='%(message)s')
logging.getLogger('httpcore').setLevel(logging.ERROR)
logging.getLogger('httpx').setLevel(logging.ERROR)

print("=" * 60)
print("Atlas V1 ART - LangGraph Readiness Test")
print("=" * 60)

# Test 1: Environment
print("\n1. Environment Check:")
checks = {
    "OPENROUTER_API_KEY": os.getenv("OPENROUTER_API_KEY"),
    "OPENROUTER_MODEL": os.getenv("OPENROUTER_MODEL"),
    "FAIRMIND_MCP_URL": os.getenv("FAIRMIND_MCP_URL")
}

for key, value in checks.items():
    if value:
        print(f"   ✅ {key}: Set")
    else:
        print(f"   ⚠️ {key}: Not set")

# Test 2: Graph Creation
print("\n2. Graph Creation:")
try:
    # Silence all output during import
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    
    import io
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()
    
    from graph import graph
    
    sys.stdout = old_stdout
    sys.stderr = old_stderr
    
    print(f"   ✅ Graph created: {type(graph).__name__}")
    
    if hasattr(graph, 'nodes'):
        nodes = list(graph.nodes.keys())
        print(f"   ✅ Nodes: {len(nodes)} nodes configured")
        
except Exception as e:
    sys.stdout = old_stdout
    sys.stderr = old_stderr
    print(f"   ❌ Error: {str(e)[:100]}")

# Test 3: Instructions
print("\n3. Running Instructions:")
print("   To run with LangGraph Studio:")
print("   ```")
print("   langgraph dev --allow-blocking")
print("   ```")
print()
print("   The --allow-blocking flag prevents blocking I/O errors")
print("   from OpenPipe ART's synchronous file operations.")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

success = True
if not checks["OPENROUTER_API_KEY"]:
    print("⚠️ OpenRouter API key not set - model won't work")
    success = False
    
if not checks["FAIRMIND_MCP_URL"]:
    print("⚠️ MCP not configured - limited functionality")

if success and 'graph' in locals():
    print("✅ System is READY for LangGraph!")
    print("   Run: langgraph dev --allow-blocking")
else:
    print("❌ Please fix the issues above before running")

print("=" * 60)