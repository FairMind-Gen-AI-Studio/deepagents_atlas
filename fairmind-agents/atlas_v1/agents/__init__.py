# Atlas V1 Modular Agents
# Following DeepAgents hierarchical agent patterns

from .investigation_agent import investigation_agent
from .discussion_agent import discussion_agent
from .planning_agent import planning_agent, create_repository_analyzer
from .task_generation_agent import task_generation_agent

__all__ = [
    'investigation_agent',
    'discussion_agent', 
    'planning_agent',
    'task_generation_agent',
    'create_repository_analyzer'
]