"""
Trajectory storage and management system for OpenPipe ART.

This module handles the persistent storage, retrieval, and management
of captured trajectories for reinforcement learning and analysis.
"""

import os
import json
import gzip
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Iterator
import logging
from dataclasses import dataclass, asdict
import asyncio
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class TrajectoryMetadata:
    """Metadata for a stored trajectory."""
    execution_id: str
    timestamp: str
    project: str
    phase: Optional[str] = None
    success: bool = False
    reward: float = 0.0
    num_steps: int = 0
    total_tokens: int = 0
    duration_seconds: float = 0.0
    model_name: Optional[str] = None
    error: Optional[str] = None


class TrajectoryStorage:
    """
    Manages persistent storage of trajectories with rotation and compression.
    
    Features:
    - Automatic rotation based on size/age
    - Compression of old trajectories
    - Indexing for fast retrieval
    - Batch operations for efficiency
    - Statistics and analytics
    """
    
    def __init__(
        self,
        base_dir: str = ".art/trajectories",
        max_size_mb: int = 100,
        max_age_days: int = 30,
        compress_after_days: int = 7,
        index_enabled: bool = True
    ):
        """
        Initialize the trajectory storage system.
        
        Args:
            base_dir: Base directory for trajectory storage
            max_size_mb: Maximum total size before rotation
            max_age_days: Maximum age before deletion
            compress_after_days: Compress trajectories older than this
            index_enabled: Whether to maintain an index for fast lookups
        """
        self.base_dir = Path(base_dir)
        self.max_size_mb = max_size_mb
        self.max_age_days = max_age_days
        self.compress_after_days = compress_after_days
        self.index_enabled = index_enabled
        
        # Create directory structure
        self.trajectories_dir = self.base_dir / "raw"
        self.compressed_dir = self.base_dir / "compressed"
        self.index_dir = self.base_dir / "index"
        self.stats_file = self.base_dir / "stats.json"
        
        for dir_path in [self.trajectories_dir, self.compressed_dir, self.index_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Load or initialize index
        self.index = self._load_index() if index_enabled else {}
        
        # Statistics
        self.stats = self._load_stats()
        
        logger.info(f"✅ TrajectoryStorage initialized at {base_dir}")
    
    def save_trajectory(
        self,
        execution_id: str,
        trajectory_data: Dict[str, Any],
        metadata: Optional[TrajectoryMetadata] = None
    ) -> str:
        """
        Save a trajectory to storage.
        
        Args:
            execution_id: Unique identifier for the execution
            trajectory_data: Full trajectory data to save
            metadata: Optional metadata (will be extracted if not provided)
            
        Returns:
            Path to the saved trajectory file
        """
        try:
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{execution_id}.json"
            filepath = self.trajectories_dir / filename
            
            # Extract or create metadata
            if metadata is None:
                metadata = self._extract_metadata(execution_id, trajectory_data)
            
            # Add metadata to trajectory data
            trajectory_data["metadata"] = asdict(metadata)
            
            # Save to file
            with open(filepath, "w") as f:
                json.dump(trajectory_data, f, indent=2, default=str)
            
            # Update index
            if self.index_enabled:
                self._update_index(execution_id, filepath, metadata)
            
            # Update statistics
            self._update_stats("trajectory_saved", metadata)
            
            # Check for maintenance needs
            asyncio.create_task(self._perform_maintenance())
            
            logger.debug(f"💾 Saved trajectory {execution_id} to {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to save trajectory {execution_id}: {e}")
            raise
    
    def load_trajectory(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a trajectory by execution ID.
        
        Args:
            execution_id: The execution ID to load
            
        Returns:
            Trajectory data or None if not found
        """
        try:
            # Check index first
            if self.index_enabled and execution_id in self.index:
                filepath = Path(self.index[execution_id]["filepath"])
                
                # Check if compressed
                if filepath.suffix == ".gz":
                    with gzip.open(filepath, "rt") as f:
                        return json.load(f)
                else:
                    with open(filepath, "r") as f:
                        return json.load(f)
            
            # Fall back to filesystem search
            for filepath in self.trajectories_dir.glob(f"*{execution_id}*.json"):
                with open(filepath, "r") as f:
                    return json.load(f)
            
            # Check compressed directory
            for filepath in self.compressed_dir.glob(f"*{execution_id}*.json.gz"):
                with gzip.open(filepath, "rt") as f:
                    return json.load(f)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to load trajectory {execution_id}: {e}")
            return None
    
    def list_trajectories(
        self,
        phase: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[TrajectoryMetadata]:
        """
        List trajectories with optional filters.
        
        Args:
            phase: Filter by Atlas phase
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of results
            
        Returns:
            List of trajectory metadata
        """
        results = []
        
        try:
            if self.index_enabled:
                # Use index for efficient filtering
                for exec_id, info in self.index.items():
                    metadata = info["metadata"]
                    
                    # Apply filters
                    if phase and metadata.phase != phase:
                        continue
                    
                    if start_date or end_date:
                        timestamp = datetime.fromisoformat(metadata.timestamp)
                        if start_date and timestamp < start_date:
                            continue
                        if end_date and timestamp > end_date:
                            continue
                    
                    results.append(metadata)
                    
                    if len(results) >= limit:
                        break
            else:
                # Scan filesystem
                for filepath in self.trajectories_dir.glob("*.json"):
                    if len(results) >= limit:
                        break
                    
                    try:
                        with open(filepath, "r") as f:
                            data = json.load(f)
                            if "metadata" in data:
                                metadata = TrajectoryMetadata(**data["metadata"])
                                
                                # Apply filters
                                if phase and metadata.phase != phase:
                                    continue
                                
                                results.append(metadata)
                    except:
                        continue
            
            # Sort by timestamp (newest first)
            results.sort(key=lambda m: m.timestamp, reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Failed to list trajectories: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about stored trajectories.
        
        Returns:
            Dictionary with statistics
        """
        try:
            stats = {
                "total_trajectories": len(self.index) if self.index_enabled else 0,
                "total_size_mb": self._calculate_total_size(),
                "by_phase": defaultdict(int),
                "by_success": {"successful": 0, "failed": 0},
                "average_reward": 0.0,
                "average_steps": 0.0,
                "average_duration": 0.0,
                "storage_info": {
                    "raw_count": len(list(self.trajectories_dir.glob("*.json"))),
                    "compressed_count": len(list(self.compressed_dir.glob("*.json.gz"))),
                    "oldest_trajectory": None,
                    "newest_trajectory": None
                }
            }
            
            if self.index_enabled and self.index:
                # Calculate statistics from index
                total_reward = 0
                total_steps = 0
                total_duration = 0
                
                for info in self.index.values():
                    metadata = info["metadata"]
                    
                    # Phase distribution
                    if metadata.phase:
                        stats["by_phase"][metadata.phase] += 1
                    
                    # Success rate
                    if metadata.success:
                        stats["by_success"]["successful"] += 1
                    else:
                        stats["by_success"]["failed"] += 1
                    
                    # Averages
                    total_reward += metadata.reward
                    total_steps += metadata.num_steps
                    total_duration += metadata.duration_seconds
                
                # Calculate averages
                count = len(self.index)
                stats["average_reward"] = round(total_reward / count, 3) if count > 0 else 0
                stats["average_steps"] = round(total_steps / count, 1) if count > 0 else 0
                stats["average_duration"] = round(total_duration / count, 1) if count > 0 else 0
            
            # Get oldest and newest
            all_files = list(self.trajectories_dir.glob("*.json")) + list(self.compressed_dir.glob("*.json.gz"))
            if all_files:
                all_files.sort(key=lambda f: f.stat().st_mtime)
                stats["storage_info"]["oldest_trajectory"] = all_files[0].name
                stats["storage_info"]["newest_trajectory"] = all_files[-1].name
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {"error": str(e)}
    
    async def _perform_maintenance(self):
        """
        Perform maintenance tasks: compression, rotation, cleanup.
        """
        try:
            # Compress old trajectories
            await self._compress_old_trajectories()
            
            # Delete expired trajectories
            await self._delete_expired_trajectories()
            
            # Check total size and rotate if needed
            if self._calculate_total_size() > self.max_size_mb:
                await self._rotate_trajectories()
            
            # Save updated stats
            self._save_stats()
            
        except Exception as e:
            logger.error(f"Maintenance failed: {e}")
    
    async def _compress_old_trajectories(self):
        """Compress trajectories older than compress_after_days."""
        cutoff_date = datetime.now() - timedelta(days=self.compress_after_days)
        
        for filepath in self.trajectories_dir.glob("*.json"):
            try:
                mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
                if mtime < cutoff_date:
                    # Compress the file
                    compressed_path = self.compressed_dir / f"{filepath.name}.gz"
                    
                    with open(filepath, "rb") as f_in:
                        with gzip.open(compressed_path, "wb") as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    
                    # Update index
                    if self.index_enabled:
                        for exec_id, info in self.index.items():
                            if info["filepath"] == str(filepath):
                                info["filepath"] = str(compressed_path)
                                break
                    
                    # Delete original
                    filepath.unlink()
                    logger.debug(f"Compressed {filepath.name}")
                    
            except Exception as e:
                logger.error(f"Failed to compress {filepath}: {e}")
    
    async def _delete_expired_trajectories(self):
        """Delete trajectories older than max_age_days."""
        cutoff_date = datetime.now() - timedelta(days=self.max_age_days)
        
        for directory in [self.trajectories_dir, self.compressed_dir]:
            for filepath in directory.glob("*"):
                try:
                    mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
                    if mtime < cutoff_date:
                        # Remove from index
                        if self.index_enabled:
                            for exec_id, info in list(self.index.items()):
                                if info["filepath"] == str(filepath):
                                    del self.index[exec_id]
                                    break
                        
                        # Delete file
                        filepath.unlink()
                        logger.debug(f"Deleted expired trajectory: {filepath.name}")
                        
                except Exception as e:
                    logger.error(f"Failed to delete {filepath}: {e}")
    
    async def _rotate_trajectories(self):
        """Rotate oldest trajectories when size limit exceeded."""
        # Get all files sorted by modification time
        all_files = []
        for directory in [self.trajectories_dir, self.compressed_dir]:
            for filepath in directory.glob("*"):
                all_files.append((filepath, filepath.stat().st_mtime))
        
        all_files.sort(key=lambda x: x[1])  # Sort by mtime
        
        # Delete oldest files until under limit
        while self._calculate_total_size() > self.max_size_mb and all_files:
            filepath, _ = all_files.pop(0)
            
            # Remove from index
            if self.index_enabled:
                for exec_id, info in list(self.index.items()):
                    if info["filepath"] == str(filepath):
                        del self.index[exec_id]
                        break
            
            filepath.unlink()
            logger.debug(f"Rotated out: {filepath.name}")
    
    def _calculate_total_size(self) -> float:
        """Calculate total size of all trajectories in MB."""
        total_size = 0
        
        for directory in [self.trajectories_dir, self.compressed_dir]:
            for filepath in directory.glob("*"):
                total_size += filepath.stat().st_size
        
        return total_size / (1024 * 1024)
    
    def _extract_metadata(self, execution_id: str, data: Dict[str, Any]) -> TrajectoryMetadata:
        """Extract metadata from trajectory data."""
        metadata_dict = data.get("metadata", {})
        
        return TrajectoryMetadata(
            execution_id=execution_id,
            timestamp=metadata_dict.get("timestamp", datetime.now().isoformat()),
            project=metadata_dict.get("project", "atlas-v1-art"),
            phase=metadata_dict.get("phase"),
            success=metadata_dict.get("success", False),
            reward=metadata_dict.get("reward", 0.0),
            num_steps=metadata_dict.get("num_steps", 0),
            total_tokens=metadata_dict.get("total_tokens", 0),
            duration_seconds=metadata_dict.get("duration_seconds", 0.0),
            model_name=metadata_dict.get("model_name"),
            error=metadata_dict.get("error")
        )
    
    def _update_index(self, execution_id: str, filepath: Path, metadata: TrajectoryMetadata):
        """Update the index with new trajectory information."""
        self.index[execution_id] = {
            "filepath": str(filepath),
            "metadata": metadata,
            "indexed_at": datetime.now().isoformat()
        }
        self._save_index()
    
    def _load_index(self) -> Dict[str, Any]:
        """Load the index from disk."""
        index_file = self.index_dir / "index.json"
        if index_file.exists():
            try:
                with open(index_file, "r") as f:
                    raw_index = json.load(f)
                    # Reconstruct metadata objects
                    for exec_id, info in raw_index.items():
                        if "metadata" in info and isinstance(info["metadata"], dict):
                            info["metadata"] = TrajectoryMetadata(**info["metadata"])
                    return raw_index
            except Exception as e:
                logger.error(f"Failed to load index: {e}")
        return {}
    
    def _save_index(self):
        """Save the index to disk."""
        try:
            index_file = self.index_dir / "index.json"
            # Convert metadata objects to dicts
            serializable_index = {}
            for exec_id, info in self.index.items():
                serializable_index[exec_id] = {
                    "filepath": info["filepath"],
                    "metadata": asdict(info["metadata"]) if isinstance(info["metadata"], TrajectoryMetadata) else info["metadata"],
                    "indexed_at": info.get("indexed_at", datetime.now().isoformat())
                }
            
            with open(index_file, "w") as f:
                json.dump(serializable_index, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
    
    def _load_stats(self) -> Dict[str, Any]:
        """Load statistics from disk."""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, "r") as f:
                    return json.load(f)
            except:
                pass
        return {
            "total_saved": 0,
            "total_loaded": 0,
            "last_maintenance": None,
            "last_rotation": None
        }
    
    def _save_stats(self):
        """Save statistics to disk."""
        try:
            with open(self.stats_file, "w") as f:
                json.dump(self.stats, f, indent=2, default=str)
        except:
            pass
    
    def _update_stats(self, event: str, metadata: Optional[TrajectoryMetadata] = None):
        """Update statistics for an event."""
        if event == "trajectory_saved":
            self.stats["total_saved"] = self.stats.get("total_saved", 0) + 1
        elif event == "trajectory_loaded":
            self.stats["total_loaded"] = self.stats.get("total_loaded", 0) + 1
        
        self.stats["last_updated"] = datetime.now().isoformat()


# Global storage instance
_storage_instance: Optional[TrajectoryStorage] = None


def get_trajectory_storage(**kwargs) -> TrajectoryStorage:
    """
    Get or create the global trajectory storage instance.
    
    Returns:
        TrajectoryStorage instance
    """
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = TrajectoryStorage(**kwargs)
    return _storage_instance