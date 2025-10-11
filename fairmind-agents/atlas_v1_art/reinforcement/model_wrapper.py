"""
Model wrapper with ALWAYS-ON OpenPipe ART integration for Atlas V1.

This module provides model creation that is ALWAYS wrapped with ART
for automatic trajectory capture during every execution. There is no
option to disable ART - it's always active for continuous learning.

Supports multiple providers:
- OpenRouter (via ChatOpenAI with custom base_url)
- Anthropic (via ChatAnthropic)
- OpenAI (via ChatOpenAI)
"""

import os
import logging
import uuid
from typing import Optional, Any, Dict, Union
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# Import ART components - REQUIRED
from art.langgraph import init_chat_model
from art.langgraph.llm_wrapper import add_thread

# Import async-safe wrapper to prevent blocking I/O
from reinforcement.async_art_wrapper import make_async_safe

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Ensure ART is available - fail fast if not
try:
    import art
    logger.info("✅ OpenPipe ART is loaded and will be active for ALL executions")
except ImportError as e:
    logger.error("❌ OpenPipe ART is REQUIRED but not installed!")
    logger.error("   Install with: pip install 'openpipe-art[langgraph]'")
    raise ImportError("OpenPipe ART is required for this version of Atlas V1") from e


def get_art_enabled_model(
    model_name: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 8192,
    thread_id: Optional[str] = None,
    **kwargs
) -> Any:
    """
    Create a model instance that is ALWAYS wrapped with OpenPipe ART.
    
    This function initializes a language model and ALWAYS configures it
    for ART trajectory capture. There is no option to disable ART - 
    it's always active for continuous reinforcement learning.
    
    Priority order:
    1. OpenRouter (via OPENROUTER_API_KEY)
    2. Anthropic (via ANTHROPIC_API_KEY)
    3. OpenAI (via OPENAI_API_KEY)
    
    Args:
        model_name: Name of the model to use (defaults to env variable)
        temperature: Model temperature for generation
        max_tokens: Maximum tokens for generation
        thread_id: Thread ID for ART tracking (auto-generated if not provided)
        **kwargs: Additional model configuration
        
    Returns:
        ART-wrapped language model instance ready for trajectory capture
    """
    # Get parameters from environment if not provided
    if temperature is None:
        temperature = float(os.getenv("ATLAS_MODEL_TEMPERATURE", "0.7"))
    if max_tokens is None:
        max_tokens = int(os.getenv("ATLAS_MODEL_MAX_TOKENS", "8192"))
    
    # 1. Check for OpenRouter configuration
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key:
        if model_name is None:
            model_name = (
                os.getenv("OPENROUTER_MODEL") or 
                os.getenv("ATLAS_MODEL_NAME", "").replace("openrouter/", "") or
                "anthropic/claude-3.5-sonnet"
            )
        
        logger.info(f"Using OpenRouter with model: {model_name}")
        logger.info(f"  Temperature: {temperature}")
        logger.info(f"  Max tokens: {max_tokens}")
        
        base_model = ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key,
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            default_headers={
                "HTTP-Referer": "https://github.com/deepagents/atlas",
                "X-Title": "Atlas V1 Agent ART"
            },
            **kwargs
        )
    
    # 2. Check for Anthropic configuration
    elif os.getenv("ANTHROPIC_API_KEY"):
        if model_name is None:
            model_name = (
                os.getenv("ATLAS_MODEL_NAME", "").replace("anthropic/", "") or
                "claude-3-5-sonnet-20241022"
            )
        
        logger.info(f"Using Anthropic with model: {model_name}")
        logger.info(f"  Temperature: {temperature}")
        logger.info(f"  Max tokens: {max_tokens}")
        
        base_model = ChatAnthropic(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
    
    # 3. Check for OpenAI configuration
    elif os.getenv("OPENAI_API_KEY"):
        if model_name is None:
            model_name = (
                os.getenv("ATLAS_MODEL_NAME", "").replace("openai/", "") or
                "gpt-4"
            )
        
        logger.info(f"Using OpenAI with model: {model_name}")
        logger.info(f"  Temperature: {temperature}")
        logger.info(f"  Max tokens: {max_tokens}")
        
        base_model = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
    
    # 4. Default fallback - use Anthropic Claude
    else:
        if model_name is None:
            model_name = "claude-3-5-sonnet-20241022"
        
        logger.warning("No API keys found. Please set OPENROUTER_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY")
        logger.info(f"Attempting to use default model: {model_name}")
        
        # Try to use Anthropic as fallback (will fail if no key)
        base_model = ChatAnthropic(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
    
    # Store final configuration for ART
    final_model_name = model_name
    if openrouter_key:
        base_url = "https://openrouter.ai/api/v1"
        api_key = openrouter_key
    elif os.getenv("ANTHROPIC_API_KEY"):
        base_url = "https://api.anthropic.com/v1"
        api_key = os.getenv("ANTHROPIC_API_KEY")
    elif os.getenv("OPENAI_API_KEY"):
        base_url = "https://api.openai.com/v1"
        api_key = os.getenv("OPENAI_API_KEY")
    else:
        base_url = "https://api.anthropic.com/v1"
        api_key = "dummy-key"  # Will fail but allows configuration
    
    # ALWAYS configure ART context for trajectory capture
    # Generate thread ID if not provided
    if thread_id is None:
        thread_id = str(uuid.uuid4())
    
    logger.info(f"🎯 Configuring ART for thread: {thread_id[:8]}...")
    
    # Set up ART context - this is REQUIRED for init_chat_model to work
    # The add_thread function sets up the CURRENT_CONFIG context variable
    log_path = add_thread(
        thread_id=thread_id,
        base_url=base_url,  # Use the base_url we already determined correctly
        api_key=api_key,
        model=final_model_name
    )
    
    logger.info(f"✅ ART context configured - trajectory logging to: {log_path}")
    
    # Now create the ART-wrapped model using init_chat_model
    # This MUST be called AFTER add_thread sets up the context
    try:
        # Create ART-wrapped model
        art_model = init_chat_model(
            model=None,  # Model config comes from CURRENT_CONFIG set by add_thread
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        logger.info(f"✅ Model wrapped with ART for automatic trajectory capture")
        logger.info(f"   Model: {final_model_name}")
        logger.info(f"   Thread: {thread_id[:8]}")
        logger.info(f"   Temperature: {temperature}")
        
        # For now, return the ART model directly without async wrapper
        # The async wrapper needs more work to properly delegate all methods
        # Users should run with: langgraph dev --allow-blocking
        logger.info("⚠️ Note: Run with 'langgraph dev --allow-blocking' to prevent blocking I/O errors")
        
        return art_model
        
    except Exception as e:
        logger.error(f"❌ Failed to create ART-wrapped model: {e}")
        logger.warning("Falling back to base model without ART")
        return base_model


def create_phase_specific_model(
    phase_name: str,
    base_config: Optional[Dict[str, Any]] = None
) -> Any:
    """
    Create a model instance optimized for a specific Atlas phase.
    
    Different phases may benefit from different model configurations
    or even different models entirely.
    
    Args:
        phase_name: Name of the Atlas phase (investigation, discussion, planning, task_generation)
        base_config: Base configuration to override
        
    Returns:
        Configured model instance for the phase
    """
    config = base_config or {}
    
    # Phase-specific configurations
    phase_configs = {
        "investigation": {
            "temperature": 0.3,  # More focused for data gathering
            "max_tokens": 4096,  # Shorter responses for efficiency
        },
        "discussion": {
            "temperature": 0.7,  # More creative for question generation
            "max_tokens": 2048,  # Concise questions
        },
        "planning": {
            "temperature": 0.5,  # Balanced for technical planning
            "max_tokens": 8192,  # Detailed plans
        },
        "task_generation": {
            "temperature": 0.2,  # Consistent task formatting
            "max_tokens": 4096,  # Structured task lists
        }
    }
    
    # Merge phase-specific config with base config
    phase_config = phase_configs.get(phase_name, {})
    final_config = {**config, **phase_config}
    
    logger.info(f"Creating phase-specific model for '{phase_name}' phase")
    return get_art_enabled_model(**final_config)


def wrap_existing_model(model: Any, thread_id: Optional[str] = None) -> Any:
    """
    Wrap an existing model instance with OpenPipe ART.
    
    This ALWAYS wraps the model with ART - there is no option to disable it.
    ART is always active for continuous reinforcement learning.
    
    Args:
        model: Existing language model instance
        thread_id: Thread ID for ART tracking (auto-generated if not provided)
        
    Returns:
        Model wrapped with ART for automatic trajectory capture
    """
    # Generate thread ID if not provided
    if thread_id is None:
        thread_id = str(uuid.uuid4())
    
    logger.info(f"🎯 Wrapping existing model with ART (thread: {thread_id[:8]})")
    
    try:
        # Detect model provider and get configuration
        model_str = str(type(model)).lower()
        if 'chatanthropic' in model_str:
            base_url = "https://api.anthropic.com/v1"
            api_key = os.getenv("ANTHROPIC_API_KEY", "")
            model_name = getattr(model, "model_name", "claude-3-5-sonnet")
        elif 'chatopenai' in model_str:
            if hasattr(model, 'base_url') and 'openrouter' in str(model.base_url):
                base_url = "https://openrouter.ai/api/v1"
                api_key = os.getenv("OPENROUTER_API_KEY", "")
            else:
                base_url = "https://api.openai.com/v1"
                api_key = os.getenv("OPENAI_API_KEY", "")
            model_name = getattr(model, "model", "gpt-4")
        else:
            # Generic fallback
            base_url = "https://api.openai.com/v1"
            api_key = ""
            model_name = "unknown"
        
        # Configure ART context
        log_path = add_thread(thread_id, base_url, api_key, model_name)
        
        # Create wrapped model
        wrapped_model = init_chat_model(
            model=None,
            temperature=getattr(model, "temperature", 0.7),
            max_tokens=getattr(model, "max_tokens", 8192)
        )
        
        logger.info(f"✅ Model wrapped with ART - logging to: {log_path}")
        return wrapped_model
        
    except Exception as e:
        logger.error(f"❌ Failed to wrap existing model: {e}")
        logger.warning("Returning original model")
        return model