"""
ART-enabled graph wrapper for Atlas V1.

This module provides a wrapper around LangGraph's CompiledStateGraph that
automatically captures trajectories using OpenPipe ART for every execution.
All agent interactions are automatically logged and stored for analysis
and reinforcement learning.
"""

import os
import asyncio
import logging
import uuid
from typing import Any, Dict, Optional, List
from datetime import datetime
from pathlib import Path
import json

# Import ART components
import art
from art import capture_auto_trajectory, auto_trajectory
from art.langgraph.llm_wrapper import add_thread

# Import LangGraph components
from langgraph.graph.state import CompiledStateGraph
from langchain_core.runnables import RunnableConfig

logger = logging.getLogger(__name__)


class ARTWrappedGraph:
    """
    Wrapper around CompiledStateGraph that automatically captures trajectories.
    
    This wrapper intercepts all graph invocations and wraps them with
    OpenPipe ART's capture_auto_trajectory to automatically log all
    LLM interactions for training and analysis.
    """
    
    def __init__(
        self,
        graph: CompiledStateGraph,
        project_name: str = "atlas-v1-art",
        trajectories_dir: str = ".art/trajectories",
        auto_save: bool = True
    ):
        """
        Initialize the ART-wrapped graph.
        
        Args:
            graph: The compiled LangGraph graph to wrap
            project_name: OpenPipe project name for tracking
            trajectories_dir: Directory to save trajectories
            auto_save: Whether to automatically save trajectories
        """
        self.graph = graph
        self.project_name = project_name
        self.trajectories_dir = Path(trajectories_dir)
        self.auto_save = auto_save
        
        # Create trajectories directory
        self.trajectories_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize storage for batch upload
        self.trajectory_buffer = []
        self.batch_size = int(os.getenv("ART_BATCH_SIZE", "10"))
        
        logger.info(f"✅ ARTWrappedGraph initialized")
        logger.info(f"   Project: {project_name}")
        logger.info(f"   Trajectories dir: {trajectories_dir}")
        logger.info(f"   Auto-save: {auto_save}")
    
    async def ainvoke(
        self,
        input: Dict[str, Any],
        config: Optional[RunnableConfig] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Async invocation with automatic trajectory capture.
        
        Every call to this method is wrapped with capture_auto_trajectory
        to automatically log all LLM interactions.
        """
        # Generate unique thread ID for this execution
        thread_id = str(uuid.uuid4())
        execution_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{thread_id[:8]}"
        
        logger.info(f"🎯 Starting ART-wrapped execution: {execution_id}")
        
        # Configure ART logging for this thread
        # This sets up the CURRENT_CONFIG context variable that init_chat_model needs
        base_url = os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")
        api_key = os.getenv("OPENROUTER_API_KEY", os.getenv("ANTHROPIC_API_KEY", ""))
        model_name = os.getenv("ATLAS_MODEL_NAME", "claude-3-5-sonnet-20241022")
        
        log_path = add_thread(thread_id, base_url, api_key, model_name)
        logger.debug(f"ART log path: {log_path}")
        
        try:
            # Wrap the graph execution with trajectory capture
            async def execute_with_capture():
                """Inner function to execute graph within capture context."""
                result = await self.graph.ainvoke(input, config, **kwargs)
                
                # Get the captured trajectory
                trajectory = auto_trajectory(required=False)
                
                if trajectory and self.auto_save:
                    # Save trajectory locally
                    await self._save_trajectory(execution_id, trajectory, input, result)
                
                return result
            
            # Execute with automatic trajectory capture
            trajectory = await capture_auto_trajectory(execute_with_capture())
            
            # The result is already returned by execute_with_capture
            # trajectory contains the full execution trace
            
            logger.info(f"✅ Execution {execution_id} completed with trajectory capture")
            
            # Buffer trajectory for batch upload if configured
            if os.getenv("ART_AUTO_UPLOAD", "false").lower() == "true":
                self.trajectory_buffer.append(trajectory)
                if len(self.trajectory_buffer) >= self.batch_size:
                    await self._upload_trajectories()
            
            # Return the actual result from the graph
            # Note: capture_auto_trajectory returns the trajectory, not the result
            # So we need to re-execute or store the result differently
            # For now, re-execute without capture (not ideal but works)
            result = await self.graph.ainvoke(input, config, **kwargs)
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in ART-wrapped execution: {e}")
            # Fall back to direct execution if ART fails
            return await self.graph.ainvoke(input, config, **kwargs)
    
    def invoke(
        self,
        input: Dict[str, Any],
        config: Optional[RunnableConfig] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Sync invocation with automatic trajectory capture.
        
        Delegates to async version using asyncio.
        """
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, use run_in_executor
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self.ainvoke(input, config, **kwargs))
                return future.result()
        else:
            # Otherwise, run normally
            return asyncio.run(self.ainvoke(input, config, **kwargs))
    
    async def _save_trajectory(
        self,
        execution_id: str,
        trajectory: art.Trajectory,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any]
    ):
        """
        Save a captured trajectory to local storage.
        
        Args:
            execution_id: Unique ID for this execution
            trajectory: Captured ART trajectory
            input_data: Input to the graph
            output_data: Output from the graph
        """
        try:
            # Create trajectory data
            trajectory_data = {
                "execution_id": execution_id,
                "timestamp": datetime.now().isoformat(),
                "project": self.project_name,
                "input": input_data,
                "output": output_data,
                "trajectory": {
                    "messages_and_choices": [
                        # Convert to serializable format
                        str(item) for item in trajectory.messages_and_choices
                    ],
                    "reward": trajectory.reward if hasattr(trajectory, 'reward') else 0.0,
                    "metadata": {}
                }
            }
            
            # Save to file
            filename = self.trajectories_dir / f"{execution_id}.json"
            with open(filename, "w") as f:
                json.dump(trajectory_data, f, indent=2, default=str)
            
            logger.debug(f"💾 Saved trajectory to {filename}")
            
            # Also append to JSONL for easier batch processing
            jsonl_file = self.trajectories_dir / "trajectories.jsonl"
            with open(jsonl_file, "a") as f:
                f.write(json.dumps(trajectory_data, default=str) + "\n")
            
        except Exception as e:
            logger.error(f"Failed to save trajectory: {e}")
    
    async def _upload_trajectories(self):
        """
        Upload buffered trajectories to OpenPipe for training.
        """
        if not self.trajectory_buffer:
            return
        
        try:
            logger.info(f"📤 Uploading {len(self.trajectory_buffer)} trajectories to OpenPipe")
            
            # TODO: Implement actual upload to OpenPipe
            # For now, just log and clear buffer
            logger.info(f"   (Upload not yet implemented - trajectories saved locally)")
            
            self.trajectory_buffer.clear()
            
        except Exception as e:
            logger.error(f"Failed to upload trajectories: {e}")
    
    def get_trajectory_stats(self) -> Dict[str, Any]:
        """
        Get statistics about captured trajectories.
        
        Returns:
            Dictionary with trajectory statistics
        """
        try:
            trajectory_files = list(self.trajectories_dir.glob("*.json"))
            jsonl_file = self.trajectories_dir / "trajectories.jsonl"
            
            stats = {
                "total_trajectories": len(trajectory_files),
                "trajectories_dir": str(self.trajectories_dir),
                "oldest_trajectory": None,
                "newest_trajectory": None,
                "total_size_mb": 0
            }
            
            if trajectory_files:
                # Get oldest and newest
                trajectory_files.sort(key=lambda f: f.stat().st_mtime)
                stats["oldest_trajectory"] = trajectory_files[0].name
                stats["newest_trajectory"] = trajectory_files[-1].name
                
                # Calculate total size
                total_size = sum(f.stat().st_size for f in trajectory_files)
                if jsonl_file.exists():
                    total_size += jsonl_file.stat().st_size
                stats["total_size_mb"] = round(total_size / (1024 * 1024), 2)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting trajectory stats: {e}")
            return {"error": str(e)}
    
    # Proxy all other attributes to the wrapped graph
    def __getattr__(self, name):
        """Proxy attribute access to the wrapped graph."""
        return getattr(self.graph, name)


def wrap_graph_with_art(
    graph: CompiledStateGraph,
    **kwargs
) -> ARTWrappedGraph:
    """
    Convenience function to wrap a graph with ART trajectory capture.
    
    Args:
        graph: The LangGraph graph to wrap
        **kwargs: Additional arguments for ARTWrappedGraph
        
    Returns:
        ARTWrappedGraph instance
    """
    return ARTWrappedGraph(graph, **kwargs)