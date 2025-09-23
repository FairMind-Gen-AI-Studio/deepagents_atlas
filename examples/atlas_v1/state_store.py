# Atlas V1 State Store - External Persistence Solution
# Provides persistent file storage across agent phases without modifying core deepagents

"""
Atlas State Store

This module provides a singleton state store for Atlas V1 that maintains
virtual filesystem persistence across agent phases. This solution works
around the core deepagents state mutation issue without requiring
modifications to the core framework.

The AtlasStateStore acts as an external persistence layer that:
1. Maintains files across agent invocations
2. Provides thread-safe operations
3. Integrates seamlessly with existing Atlas architecture
4. Preserves backward compatibility

Usage:
    store = AtlasStateStore.get_instance()
    store.update_files({"new_file.md": "content"})
    files = store.get_files()
"""

import threading
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class AtlasStateStore:
    """
    Singleton state store for Atlas V1 virtual filesystem persistence.

    This class provides a thread-safe, persistent storage mechanism for
    virtual files that survives across agent phase transitions. It works
    by maintaining an external state store that the atlas_coordinator
    can sync with before and after agent invocations.

    Key Features:
    - Singleton pattern ensures single source of truth
    - Thread-safe operations for concurrent access
    - Seamless integration with existing Atlas workflow
    - No modifications required to core deepagents
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._files: Dict[str, str] = {}
            self._state_lock = threading.RLock()  # Reentrant lock for nested operations
            self._thread_id: Optional[str] = None
            self._initialized = True
            logger.info("AtlasStateStore initialized")

    @classmethod
    def get_instance(cls) -> "AtlasStateStore":
        """Get the singleton instance of AtlasStateStore."""
        return cls()

    def set_thread_id(self, thread_id: str) -> None:
        """
        Set the thread ID for this session.

        Args:
            thread_id: Unique identifier for the current Atlas session
        """
        with self._state_lock:
            if self._thread_id != thread_id:
                logger.info(f"AtlasStateStore: Switching to thread_id {thread_id}")
                self._thread_id = thread_id
                # Note: We keep files across thread switches for now
                # In future, could implement per-thread isolation if needed

    def get_files(self) -> Dict[str, str]:
        """
        Get a copy of all files in the store.

        Returns:
            Dictionary mapping file paths to content
        """
        with self._state_lock:
            return self._files.copy()

    def update_files(self, new_files: Dict[str, str]) -> None:
        """
        Update the store with new files, merging with existing files.

        Args:
            new_files: Dictionary of file paths to content to add/update
        """
        with self._state_lock:
            print(f"💾 update_files called with {len(new_files) if new_files else 0} files")
            if new_files:
                print(f"💾 Files to update: {list(new_files.keys())}")

                # Track which files are new vs updated
                new_file_names = [name for name in new_files.keys() if name not in self._files]
                updated_file_names = [name for name in new_files.keys() if name in self._files]

                # Log before update
                files_before = list(self._files.keys())
                print(f"💾 Store had {len(files_before)} files before update: {files_before}")

                self._files.update(new_files)

                # Log after update
                files_after = list(self._files.keys())
                print(f"💾 Store has {len(files_after)} files after update: {files_after}")

                if new_file_names:
                    print(f"💾 Added {len(new_file_names)} NEW files: {new_file_names}")
                if updated_file_names:
                    print(f"💾 Updated {len(updated_file_names)} EXISTING files: {updated_file_names}")

                # Log file sizes for verification
                for fname, content in new_files.items():
                    print(f"💾   {fname}: {len(content)} characters")

            else:
                print("💾 No files to update (empty or None dict provided)")

    def sync_from_agent_state(self, agent_state: Dict[str, Any]) -> None:
        """
        Sync files from an agent state into the store.

        This method extracts files from a DeepAgentState and merges them
        into the persistent store.

        Args:
            agent_state: The agent state containing files to sync
        """
        if "files" in agent_state and agent_state["files"]:
            self.update_files(agent_state["files"])

    def sync_to_agent_state(self, agent_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sync files from the store into an agent state.

        This method injects the persistent files into a DeepAgentState
        before passing it to an agent.

        Args:
            agent_state: The agent state to inject files into

        Returns:
            Updated agent state with files from the store
        """
        with self._state_lock:
            # Create a copy of the state and inject our files
            updated_state = agent_state.copy()

            # Merge existing files with store files (store takes precedence)
            existing_files = updated_state.get("files", {})
            merged_files = {**existing_files, **self._files}
            updated_state["files"] = merged_files

            logger.debug(f"AtlasStateStore: Synced {len(merged_files)} files to agent state")
            return updated_state

    def clear_files(self) -> None:
        """Clear all files from the store."""
        with self._state_lock:
            cleared_count = len(self._files)
            self._files.clear()
            logger.info(f"AtlasStateStore: Cleared {cleared_count} files")

    def has_file(self, file_path: str) -> bool:
        """
        Check if a file exists in the store.

        Args:
            file_path: Path to check

        Returns:
            True if file exists, False otherwise
        """
        with self._state_lock:
            return file_path in self._files

    def get_file_content(self, file_path: str) -> Optional[str]:
        """
        Get content of a specific file.

        Args:
            file_path: Path of file to retrieve

        Returns:
            File content if exists, None otherwise
        """
        with self._state_lock:
            return self._files.get(file_path)

    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of the state store.

        Returns:
            Status dictionary with file count and list
        """
        with self._state_lock:
            return {
                "thread_id": self._thread_id,
                "file_count": len(self._files),
                "files": list(self._files.keys()),
                "total_content_size": sum(len(content) for content in self._files.values())
            }


# Convenience functions for easy access
def get_atlas_store() -> AtlasStateStore:
    """Get the Atlas state store instance."""
    return AtlasStateStore.get_instance()


def sync_files_from_result(result: Dict[str, Any]) -> None:
    """
    Convenience function to sync files from an agent result.

    Handles both direct file locations (result["files"]) and
    LangGraph Command update locations (result["update"]["files"]).

    Args:
        result: Agent execution result containing files
    """
    store = get_atlas_store()

    # DEBUG: Force visibility with print statements
    print(f"🔄🔄🔄 SYNC_FILES_FROM_RESULT CALLED - result type: {type(result)}")

    # DEBUG: Log what we received in detail
    print(f"🔄 sync_files_from_result called with result type: {type(result)}")
    if isinstance(result, dict):
        print(f"🔄 Result has keys: {list(result.keys())}")
    else:
        print(f"🔄 Result is not a dict: {result}")
        return

    files_synced = False

    # Check direct location first (result["files"])
    if "files" in result:
        if result["files"]:
            file_list = list(result["files"].keys())
            print(f"🔄 Found {len(file_list)} files at result['files']: {file_list}")
            store.update_files(result["files"])
            files_synced = True
        else:
            print("🔄 result['files'] exists but is empty")
    else:
        print("🔄 No 'files' key at top level of result")

    # Check LangGraph Command update location (result["update"]["files"])
    if "update" in result:
        print(f"🔄 Found 'update' key, type: {type(result['update'])}")
        if isinstance(result["update"], dict):
            update_keys = list(result["update"].keys()) if result["update"] else []
            print(f"🔄 Update has keys: {update_keys}")
            if "files" in result["update"]:
                if result["update"]["files"]:
                    file_list = list(result["update"]["files"].keys())
                    print(f"🔄 Found {len(file_list)} files at result['update']['files']: {file_list}")
                    store.update_files(result["update"]["files"])
                    files_synced = True
                else:
                    print("🔄 result['update']['files'] exists but is empty")
            else:
                print("🔄 No 'files' key in result['update']")
        else:
            print(f"🔄 result['update'] is not a dict, it's: {type(result['update'])}")
    else:
        print("🔄 No 'update' key in result")

    if not files_synced:
        print("🔄 WARNING: No files found to sync in agent result")
        # Log detailed structure for debugging
        if isinstance(result, dict):
            for key in result.keys():
                value_type = type(result[key])
                if isinstance(result[key], dict):
                    sub_keys = list(result[key].keys())
                    print(f"🔄   result['{key}'] is dict with keys: {sub_keys}")
                else:
                    print(f"🔄   result['{key}'] type: {value_type}")
    else:
        print(f"🔄 Files successfully synced to store")


def prepare_state_with_files(initial_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to prepare state with persistent files.

    Args:
        initial_state: Initial state dictionary

    Returns:
        State with files from persistent store
    """
    store = get_atlas_store()
    return store.sync_to_agent_state(initial_state)