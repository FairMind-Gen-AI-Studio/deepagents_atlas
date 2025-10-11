"""
Unified Model Configuration

Single source of truth for model initialization across all agents.
Supports Anthropic, OpenRouter, and OpenAI providers.
"""

import os
import logging
from typing import Optional
from langchain_core.language_models import BaseChatModel
from dotenv import load_dotenv

from .providers import (
    initialize_anthropic_model,
    initialize_openrouter_model,
    initialize_openai_model,
    get_default_model
)

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def initialize_model(
    agent_prefix: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    model_name: Optional[str] = None
) -> BaseChatModel:
    """
    Initialize the appropriate chat model based on environment variables.

    Priority order:
    1. Anthropic (via ANTHROPIC_API_KEY)
    2. OpenRouter (via OPENROUTER_API_KEY)
    3. OpenAI (via OPENAI_API_KEY)
    4. Default fallback (deepagents default model)

    Args:
        agent_prefix: Agent-specific env var prefix (e.g., "ATLAS", "DOCGEN", "ARCHQA")
                     If provided, looks for {prefix}_MODEL_NAME, {prefix}_MODEL_TEMPERATURE, etc.
        temperature: Override temperature (defaults to env var or 0.7)
        max_tokens: Override max_tokens (defaults to env var or 8192)
        model_name: Override model name (defaults to env var)

    Returns:
        BaseChatModel: Configured chat model instance

    Example:
        # Atlas V1 agent
        model = initialize_model(agent_prefix="ATLAS")
        # Looks for: ATLAS_MODEL_NAME, ATLAS_MODEL_TEMPERATURE, etc.

        # Generic agent
        model = initialize_model(temperature=0.5)
        # Uses global MODEL_NAME, MODEL_TEMPERATURE, etc.
    """
    # Build environment variable names
    if agent_prefix:
        temp_var = f"{agent_prefix}_MODEL_TEMPERATURE"
        tokens_var = f"{agent_prefix}_MODEL_MAX_TOKENS"
        name_var = f"{agent_prefix}_MODEL_NAME"
    else:
        temp_var = "MODEL_TEMPERATURE"
        tokens_var = "MODEL_MAX_TOKENS"
        name_var = "MODEL_NAME"

    # Get configuration from environment with fallbacks
    temperature = temperature or float(os.getenv(temp_var, os.getenv("MODEL_TEMPERATURE", "0.7")))
    max_tokens = max_tokens or int(os.getenv(tokens_var, os.getenv("MODEL_MAX_TOKENS", "8192")))
    model_name = model_name or os.getenv(name_var, os.getenv("MODEL_NAME", ""))

    logger.info(f"Initializing model for {agent_prefix or 'generic'} agent...")
    logger.info(f"  Temperature: {temperature}")
    logger.info(f"  Max tokens: {max_tokens}")

    # Try each provider in order
    model = None

    # 1. Anthropic
    if os.getenv("ANTHROPIC_API_KEY"):
        model = initialize_anthropic_model(model_name, temperature, max_tokens)
        if model:
            return model

    # 2. OpenRouter
    if os.getenv("OPENROUTER_API_KEY"):
        model = initialize_openrouter_model(model_name, temperature, max_tokens)
        if model:
            return model

    # 3. OpenAI
    if os.getenv("OPENAI_API_KEY"):
        model = initialize_openai_model(model_name, temperature, max_tokens)
        if model:
            return model

    # 4. Default fallback
    logger.warning("No API keys found. Using deepagents default model.")
    logger.info("Set ANTHROPIC_API_KEY, OPENROUTER_API_KEY, or OPENAI_API_KEY")
    return get_default_model()


def get_model_info(agent_prefix: Optional[str] = None) -> dict:
    """
    Get information about the configured model for debugging.

    Args:
        agent_prefix: Agent-specific env var prefix (e.g., "ATLAS")

    Returns:
        dict: Model configuration details
    """
    if agent_prefix:
        temp_var = f"{agent_prefix}_MODEL_TEMPERATURE"
        tokens_var = f"{agent_prefix}_MODEL_MAX_TOKENS"
        name_var = f"{agent_prefix}_MODEL_NAME"
    else:
        temp_var = "MODEL_TEMPERATURE"
        tokens_var = "MODEL_MAX_TOKENS"
        name_var = "MODEL_NAME"

    info = {
        "provider": "unknown",
        "model": "unknown",
        "temperature": float(os.getenv(temp_var, os.getenv("MODEL_TEMPERATURE", "0.7"))),
        "max_tokens": int(os.getenv(tokens_var, os.getenv("MODEL_MAX_TOKENS", "8192")))
    }

    model_name = os.getenv(name_var, os.getenv("MODEL_NAME", ""))

    if os.getenv("ANTHROPIC_API_KEY"):
        info["provider"] = "anthropic"
        info["model"] = model_name.replace("anthropic/", "") or "claude-3-5-sonnet-20241022"
    elif os.getenv("OPENROUTER_API_KEY"):
        info["provider"] = "openrouter"
        info["model"] = os.getenv("OPENROUTER_MODEL") or model_name or "anthropic/claude-3.5-sonnet"
    elif os.getenv("OPENAI_API_KEY"):
        info["provider"] = "openai"
        info["model"] = model_name.replace("openai/", "") or "gpt-4"
    else:
        info["provider"] = "default"
        info["model"] = "claude-sonnet-4-20250514"

    return info
