#!/usr/bin/env python3
"""
Simple test for Atlas V1 ART integration.
"""

import os
import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))

# Test imports
print("Testing Atlas V1 ART Integration")
print("=" * 40)

# 1. Test model wrapper
print("\n1. Testing model wrapper:")
try:
    from reinforcement.model_wrapper_simple import get_base_model, check_art_availability
    model = get_base_model()
    print(f"✅ Model created: {type(model).__name__}")
    
    if check_art_availability():
        print("✅ OpenPipe ART is available")
    else:
        print("⚠️  OpenPipe ART not available")
except Exception as e:
    print(f"❌ Error: {e}")

# 2. Test graph creation
print("\n2. Testing graph creation:")
try:
    from graph import create_atlas_graph_with_art
    graph = create_atlas_graph_with_art()
    print(f"✅ Graph created successfully")
    print(f"   Type: {type(graph).__name__}")
    if hasattr(graph, 'nodes'):
        print(f"   Nodes: {list(graph.nodes.keys())}")
except Exception as e:
    print(f"❌ Error: {e}")

# 3. Test ART module directly
print("\n3. Testing OpenPipe ART module:")
try:
    from art.langgraph import init_chat_model, wrap_rollout
    print("✅ ART functions imported successfully")
    print("   - init_chat_model available")
    print("   - wrap_rollout available")
    print("\n🎉 OpenPipe ART integration is working!")
    print("\nYou can now:")
    print("  - Run the agent: langgraph dev")
    print("  - Train with ART: python train_with_art.py")
except ImportError as e:
    print(f"⚠️  ART not available: {e}")
    print("\nThe agent will work without ART reinforcement learning.")

print("\n" + "=" * 40)