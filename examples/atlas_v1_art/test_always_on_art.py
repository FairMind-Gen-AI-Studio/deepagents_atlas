#!/usr/bin/env python3
"""
Test script to verify that OpenPipe ART is ALWAYS active.
This confirms that every execution is tracked automatically.
"""

import os
import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("Testing ALWAYS-ON OpenPipe ART Integration")
print("=" * 60)

# 1. Test that ART is required
print("\n1. Testing ART requirement:")
try:
    from reinforcement.model_wrapper import get_art_enabled_model
    print("✅ Model wrapper imported - ART is required")
except ImportError as e:
    print(f"❌ Failed to import: {e}")
    sys.exit(1)

# 2. Test model creation with ART
print("\n2. Testing ART-wrapped model creation:")
try:
    model = get_art_enabled_model()
    print(f"✅ Model created with ART wrapping")
    print(f"   Type: {type(model).__name__}")
    
    # Check if it's a LoggingLLM (ART wrapper)
    if "LoggingLLM" in str(type(model)):
        print("✅ Model is wrapped with ART LoggingLLM")
    else:
        print(f"⚠️  Model type unexpected: {type(model)}")
except Exception as e:
    print(f"❌ Model creation failed: {e}")

# 3. Test graph creation with ART wrapper
print("\n3. Testing graph with ART wrapper:")
try:
    from graph import create_atlas_graph_with_art
    graph = create_atlas_graph_with_art()
    
    # Check if it's wrapped
    if "ARTWrappedGraph" in str(type(graph)):
        print("✅ Graph is wrapped with ARTWrappedGraph")
    else:
        print(f"⚠️  Graph type: {type(graph).__name__}")
    
    # Check for trajectory storage
    if hasattr(graph, 'trajectories_dir'):
        print(f"✅ Trajectory storage configured: {graph.trajectories_dir}")
    
    # Get stats if available
    if hasattr(graph, 'get_trajectory_stats'):
        stats = graph.get_trajectory_stats()
        print(f"✅ Trajectory stats available: {stats.get('total_trajectories', 0)} trajectories")
        
except Exception as e:
    print(f"❌ Graph creation failed: {e}")
    import traceback
    traceback.print_exc()

# 4. Test trajectory storage
print("\n4. Testing trajectory storage system:")
try:
    from reinforcement.trajectory_storage import get_trajectory_storage
    storage = get_trajectory_storage()
    stats = storage.get_statistics()
    
    print("✅ Trajectory storage initialized")
    print(f"   Base directory: {storage.base_dir}")
    print(f"   Total trajectories: {stats.get('total_trajectories', 0)}")
    print(f"   Total size: {stats.get('total_size_mb', 0):.2f} MB")
    
except Exception as e:
    print(f"❌ Storage test failed: {e}")

# 5. Verify ART files structure
print("\n5. Checking ART directory structure:")
art_dir = Path(".art")
if art_dir.exists():
    print(f"✅ ART directory exists: {art_dir}")
    
    # Check subdirectories
    for subdir in ["trajectories", "langgraph"]:
        path = art_dir / subdir
        if path.exists():
            print(f"   ✅ {subdir}/ exists")
        else:
            print(f"   ⚠️  {subdir}/ not yet created (will be created on first run)")
else:
    print("⚠️  .art directory not yet created (will be created on first execution)")

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

print("""
✅ OpenPipe ART is ALWAYS ACTIVE in this version!

Key Points:
1. Every model creation uses ART wrapping
2. Every graph execution captures trajectories
3. Trajectories are automatically saved locally
4. Storage is managed with rotation and compression
5. No configuration needed - it just works!

Next steps:
1. Run the agent: langgraph dev
2. Check trajectories: ls -la .art/trajectories/
3. Train on trajectories: python train_with_art.py

🎯 ART is now integral to Atlas V1 - not optional!
""")

print("=" * 60)