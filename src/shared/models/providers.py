"""
Model Provider Implementations

Provider-specific initialization logic for Anthropic, OpenRouter, and OpenAI.
"""

import os
import logging
from typing import Optional
from langchain_core.language_models import BaseChatModel

logger = logging.getLogger(__name__)


def initialize_anthropic_model(
    model_name: str,
    temperature: float,
    max_tokens: int
) -> Optional[BaseChatModel]:
    """Initialize Anthropic model with prompt caching."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    # Clean model name
    model_name = model_name.replace("anthropic/", "") or "claude-3-5-sonnet-20241022"

    logger.info(f"Using Anthropic with model: {model_name}")
    logger.info(f"  Prompt caching: Enabled with extended TTL and token-efficient tools")

    try:
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model_name=model_name,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            # Enable Anthropic beta features for optimal caching
            default_headers={
                "anthropic-beta": "extended-cache-ttl-2025-04-11,token-efficient-tools-2025-02-19"
            }
        )
    except ImportError:
        logger.error("langchain-anthropic not installed. Install with: pip install langchain-anthropic")
        return None


def initialize_openrouter_model(
    model_name: str,
    temperature: float,
    max_tokens: int
) -> Optional[BaseChatModel]:
    """Initialize OpenRouter model."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return None

    # Get model from OPENROUTER_MODEL or provided name
    model_name = (
        os.getenv("OPENROUTER_MODEL") or
        model_name.replace("openrouter/", "") or
        "anthropic/claude-3.5-sonnet"
    )

    logger.info(f"Using OpenRouter with model: {model_name}")

    try:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            default_headers={
                "HTTP-Referer": "https://github.com/deepagents/atlas",
                "X-Title": "DeepAgents FairMind"
            }
        )
    except ImportError:
        logger.error("langchain-openai not installed. Install with: pip install langchain-openai")
        return None


def initialize_openai_model(
    model_name: str,
    temperature: float,
    max_tokens: int
) -> Optional[BaseChatModel]:
    """Initialize OpenAI model."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    model_name = model_name.replace("openai/", "") or "gpt-4"

    logger.info(f"Using OpenAI with model: {model_name}")

    try:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model_name,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens
        )
    except ImportError:
        logger.error("langchain-openai not installed. Install with: pip install langchain-openai")
        return None


def get_default_model() -> BaseChatModel:
    """Get deepagents default model."""
    try:
        from deepagents.model import get_default_model as get_deepagents_default
        return get_deepagents_default()
    except ImportError:
        logger.error("deepagents not installed. Install with: pip install deepagents")
        raise
