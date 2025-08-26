"""
Atlas V1 with OpenPipe ART Integration

Experimental implementation of Atlas V1 with reinforcement learning
capabilities through OpenPipe ART.
"""

from .atlas_agent_art import (
    AtlasAgentART,
    create_atlas_agent_art
)

__version__ = "0.1.0"
__all__ = [
    'AtlasAgentART',
    'create_atlas_agent_art'
]