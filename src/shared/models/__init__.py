"""
Model Configuration Module

Provides unified model initialization with multi-provider support (Anthropic, OpenRouter, OpenAI).
"""

from .config import initialize_model, get_model_info
from .providers import (
    initialize_anthropic_model,
    initialize_openrouter_model,
    initialize_openai_model,
    get_default_model,
)

__all__ = [
    "initialize_model",
    "get_model_info",
    "initialize_anthropic_model",
    "initialize_openrouter_model",
    "initialize_openai_model",
    "get_default_model",
]
