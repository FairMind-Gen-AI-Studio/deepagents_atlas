#!/usr/bin/env python3

"""
Atlas V1 Utilities

Collection of utility functions specific to Atlas V1 implementation,
including file persistence and cache management helpers.
"""


def clear_interrupt_cache():
    """
    Clear the global interrupt cache after successful recovery.

    This function provides a way to clean up the interrupt cache
    after files have been successfully recovered and persisted.
    It's called by Atlas V1 after successful cache recovery.

    Returns:
        int: Number of files cleared from cache
    """
    try:
        # Import the global cache from tools module
        import sys
        import os
        core_path = os.path.join(os.path.dirname(__file__), '..', '..', 'src')
        if core_path not in sys.path:
            sys.path.insert(0, core_path)
        from deepagents.tools import _interrupt_file_cache

        # Check if the cache exists and is a dictionary
        if _interrupt_file_cache is not None and isinstance(_interrupt_file_cache, dict):
            cache_size = len(_interrupt_file_cache)
            if cache_size > 0:
                _interrupt_file_cache.clear()
                print(f"🧹 ATLAS CACHE CLEANUP: Cleared {cache_size} files from interrupt cache")
            else:
                print(f"🧹 ATLAS CACHE CLEANUP: Cache was already empty")
            return cache_size
        else:
            print(f"🧹 ATLAS CACHE CLEANUP: Cache not found or not a dictionary")
            return 0
    except (ImportError, NameError, AttributeError) as e:
        print(f"🧹 ATLAS CACHE CLEANUP: Could not access cache ({e})")

    return 0


def get_interrupt_cache_status():
    """
    Get status of the global interrupt cache.

    Returns:
        dict: Cache status information
    """
    try:
        # Import the global cache from tools module
        import sys
        import os
        core_path = os.path.join(os.path.dirname(__file__), '..', '..', 'src')
        if core_path not in sys.path:
            sys.path.insert(0, core_path)
        from deepagents.tools import _interrupt_file_cache

        return {
            "cache_exists": _interrupt_file_cache is not None and isinstance(_interrupt_file_cache, dict),
            "file_count": len(_interrupt_file_cache) if _interrupt_file_cache else 0,
            "files": list(_interrupt_file_cache.keys()) if _interrupt_file_cache else []
        }
    except (ImportError, NameError) as e:
        return {
            "cache_exists": False,
            "file_count": 0,
            "files": [],
            "error": str(e)
        }