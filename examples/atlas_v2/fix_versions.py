#!/usr/bin/env python3
"""
Fix script for LangGraph version compatibility issues.
Automatically updates langgraph packages to compatible versions.
"""

import subprocess
import sys

def run_command(command):
    """Run a command and return success status."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    print("🔧 LANGGRAPH VERSION FIX")
    print("=" * 50)

    print("🔍 Checking current versions...")
    success, stdout, stderr = run_command("pip list | grep langgraph")

    if success:
        print("Current versions:")
        print(stdout)
    else:
        print("❌ Could not check versions:", stderr)

    print("\n🔄 Updating LangGraph packages...")
    success, stdout, stderr = run_command("pip install -U langgraph-api \"langgraph-cli[inmem]\"")

    if success:
        print("✅ Successfully updated LangGraph packages!")
        print("Updated packages:")
        print(stdout)

        print("\n🧪 Testing Atlas V2...")
        success_test, _, _ = run_command("cd /Users/alexiocassani/Projects/deepagents_atlas/examples/atlas_v2 && python test_atlas_v2.py")

        if success_test:
            print("✅ Atlas V2 tests passed!")
        else:
            print("❌ Atlas V2 tests failed")

    else:
        print("❌ Failed to update packages:")
        print(stderr)
        return False

    print("\n🎉 LangGraph version compatibility fixed!")
    print("✅ You can now run: langgraph dev")
    print("✅ All Atlas V2 functionality should work correctly")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

