"""
Model Configuration Utility for Atlas V1

This module provides intelligent model initialization based on environment variables,
supporting multiple providers including OpenRouter, Anthropic, and OpenAI.
"""

import os
import logging
from typing import Optional, Union
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def initialize_atlas_model() -> BaseChatModel:
    """
    Initialize the appropriate chat model based on environment variables.
    
    Priority order:
    1. OpenRouter (via OPENROUTER_API_KEY and OPENROUTER_MODEL)
    2. Anthropic (via ANTHROPIC_API_KEY)
    3. OpenAI (via OPENAI_API_KEY)
    4. Default fallback (Claude Sonnet)
    
    Returns:
        BaseChatModel: Configured chat model instance
    """
    # Get common parameters from environment
    temperature = float(os.getenv("ATLAS_MODEL_TEMPERATURE", "0.7"))
    max_tokens = int(os.getenv("ATLAS_MODEL_MAX_TOKENS", "8192"))
    
    # Log configuration source
    logger.info("Initializing Atlas model from environment variables...")
    
    # 1. Check for OpenRouter configuration
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key:
        model_name = (
            os.getenv("OPENROUTER_MODEL") or 
            os.getenv("LITELLM_MODEL", "").replace("openrouter/", "") or
            os.getenv("ATLAS_MODEL_NAME", "").replace("openrouter/", "") or
            "z-ai/glm-4.5"
        )
        
        logger.info(f"Using OpenRouter with model: {model_name}")
        logger.info(f"  Temperature: {temperature}")
        logger.info(f"  Max tokens: {max_tokens}")
        
        return ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key,
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            default_headers={
                "HTTP-Referer": "https://github.com/deepagents/atlas",
                "X-Title": "Atlas V1 Agent"
            }
        )
    
    # 2. Check for Anthropic configuration
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        model_name = (
            os.getenv("ATLAS_MODEL_NAME", "").replace("anthropic/", "") or
            os.getenv("LITELLM_MODEL", "").replace("anthropic/", "") or
            "claude-3-5-sonnet-20241022"
        )
        
        logger.info(f"Using Anthropic with model: {model_name}")
        logger.info(f"  Temperature: {temperature}")
        logger.info(f"  Max tokens: {max_tokens}")
        
        return ChatAnthropic(
            model_name=model_name,
            api_key=anthropic_key,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    # 3. Check for OpenAI configuration
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        model_name = (
            os.getenv("ATLAS_MODEL_NAME", "").replace("openai/", "") or
            os.getenv("LITELLM_MODEL", "").replace("openai/", "") or
            "gpt-4"
        )
        
        logger.info(f"Using OpenAI with model: {model_name}")
        logger.info(f"  Temperature: {temperature}")
        logger.info(f"  Max tokens: {max_tokens}")
        
        return ChatOpenAI(
            model=model_name,
            api_key=openai_key,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    # 4. Default fallback
    logger.warning("No API keys found in environment. Using default Claude Sonnet model.")
    logger.info("Set OPENROUTER_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY to use a specific provider.")
    
    # Import default model as fallback
    from deepagents.model import get_default_model
    return get_default_model()


def get_model_info() -> dict:
    """
    Get information about the configured model for debugging.
    
    Returns:
        dict: Model configuration details
    """
    info = {
        "provider": "unknown",
        "model": "unknown",
        "temperature": float(os.getenv("ATLAS_MODEL_TEMPERATURE", "0.7")),
        "max_tokens": int(os.getenv("ATLAS_MODEL_MAX_TOKENS", "8192"))
    }
    
    if os.getenv("OPENROUTER_API_KEY"):
        info["provider"] = "openrouter"
        info["model"] = (
            os.getenv("OPENROUTER_MODEL") or 
            os.getenv("LITELLM_MODEL", "").replace("openrouter/", "") or
            "z-ai/glm-4.5"
        )
    elif os.getenv("ANTHROPIC_API_KEY"):
        info["provider"] = "anthropic"
        info["model"] = (
            os.getenv("ATLAS_MODEL_NAME", "").replace("anthropic/", "") or
            "claude-3-5-sonnet-20241022"
        )
    elif os.getenv("OPENAI_API_KEY"):
        info["provider"] = "openai"
        info["model"] = (
            os.getenv("ATLAS_MODEL_NAME", "").replace("openai/", "") or
            "gpt-4"
        )
    else:
        info["provider"] = "default"
        info["model"] = "claude-sonnet-4-20250514"
    
    return info