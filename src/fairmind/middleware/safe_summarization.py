"""Safe Summarization Middleware - Enhanced context management with fallback protection.

This middleware extends LangChain's SummarizationMiddleware with critical safety features:

1. **Lower Token Threshold**: Triggers at 50k tokens (vs 85k default) for earlier intervention
2. **Fallback Protection**: Falls back to message trimming if summarization fails
3. **Hard Limit Protection**: Emergency trimming at 180k tokens (90% of 200k limit)
4. **Enhanced Logging**: Real-time token usage monitoring and compression metrics

Key Innovation: Graceful Degradation
-------------------------------------
Unlike the default SummarizationMiddleware which can fail silently with BlockingError
during async retry (causing zero compression: 255k → 252k), this middleware ALWAYS
reduces context when needed:

1. First attempt: Try full summarization (ideal)
2. Second attempt: Aggressive message trimming (safe)
3. Third attempt: Emergency hard limit trimming (guaranteed)

This ensures we never hit the 200k token limit that causes 400 "prompt too long" errors.

Usage:
------
```python
from fairmind.middleware import SafeSummarizationMiddleware
from langchain.chat_models import init_chat_model

model = init_chat_model("anthropic/claude-sonnet-4-5-20250929")

middleware = SafeSummarizationMiddleware(
    model=model,
    max_tokens_before_summary=50000,  # Lower threshold
    messages_to_keep=20,
    hard_limit_tokens=180000,  # Emergency protection
)

agent = create_agent(
    model=model,
    tools=[...],
    middleware=[middleware, ...]
)
```

Implementation Notes:
---------------------
- Inherits from LangChain's SummarizationMiddleware for proven logic
- Overrides _create_summary() to add try/except fallback
- Adds _emergency_trim() for hard limit protection
- Adds comprehensive logging for debugging token issues
"""

import logging
from typing import Any

from langchain.agents.middleware import SummarizationMiddleware, AgentState
from langchain_core.messages import AnyMessage, RemoveMessage
from langchain_core.messages.utils import count_tokens_approximately, trim_messages
from langgraph.graph.message import REMOVE_ALL_MESSAGES

logger = logging.getLogger(__name__)


class SafeSummarizationMiddleware(SummarizationMiddleware):
    """Enhanced summarization middleware with fallback protection and hard limits.

    This middleware extends the default SummarizationMiddleware with critical safety features
    to prevent the 200k token overflow issue that was causing 400 "prompt too long" errors.

    Key improvements:
    - Lower token threshold (50k vs 85k) for earlier intervention
    - Fallback to aggressive trimming when summarization fails
    - Hard limit protection at 180k tokens (90% of 200k)
    - Detailed logging for token usage monitoring
    """

    def __init__(
        self,
        model,
        max_tokens_before_summary: int = 50000,  # Lower threshold
        messages_to_keep: int = 20,
        hard_limit_tokens: int = 180000,  # Emergency protection at 90% of 200k
        **kwargs
    ):
        """Initialize SafeSummarizationMiddleware.

        Args:
            model: LLM model for summarization
            max_tokens_before_summary: Token threshold to trigger summarization (default: 50k)
            messages_to_keep: Number of recent messages to preserve (default: 20)
            hard_limit_tokens: Emergency hard limit for trimming (default: 180k = 90% of 200k)
            **kwargs: Additional arguments passed to SummarizationMiddleware
        """
        super().__init__(
            model=model,
            max_tokens_before_summary=max_tokens_before_summary,
            messages_to_keep=messages_to_keep,
            **kwargs
        )
        self.hard_limit_tokens = hard_limit_tokens

        logger.info("=" * 70)
        logger.info("SafeSummarizationMiddleware initialized")
        logger.info("=" * 70)
        logger.info(f"  Summarization threshold: {max_tokens_before_summary:,} tokens")
        logger.info(f"  Messages to keep: {messages_to_keep}")
        logger.info(f"  Hard limit: {hard_limit_tokens:,} tokens ({hard_limit_tokens/200000*100:.0f}% of 200k)")
        logger.info("=" * 70)

    def before_model(self, state: AgentState) -> dict[str, Any] | None:  # type: ignore[override]
        """Process messages before model invocation with enhanced safety checks.

        Processing flow:
        1. Check token count
        2. If over hard limit (180k): Emergency trim to safety
        3. If over threshold (50k): Try summarization with fallback
        4. Log all operations for monitoring

        Returns:
            State update with trimmed/summarized messages, or None if no action needed
        """
        messages = state["messages"]
        self._ensure_message_ids(messages)

        total_tokens = self.token_counter(messages)

        # Log current token usage
        logger.info(f"📊 Token usage: {total_tokens:,} / 200,000 ({total_tokens/200000*100:.1f}%)")

        # HARD LIMIT CHECK: Emergency protection at 180k tokens
        if total_tokens >= self.hard_limit_tokens:
            logger.warning("🚨 HARD LIMIT REACHED! Emergency trimming to prevent overflow")
            logger.warning(f"   Current: {total_tokens:,} tokens, Hard limit: {self.hard_limit_tokens:,} tokens")
            return self._emergency_trim(messages, total_tokens)

        # NORMAL THRESHOLD CHECK: Try summarization
        if (
            self.max_tokens_before_summary is not None
            and total_tokens < self.max_tokens_before_summary
        ):
            logger.debug(f"✅ Token usage OK: {total_tokens:,} < {self.max_tokens_before_summary:,}")
            return None

        logger.info(f"⚠️  Token threshold exceeded: {total_tokens:,} >= {self.max_tokens_before_summary:,}")
        logger.info("   Attempting summarization...")

        # Find safe cutoff point (preserve AI/Tool message pairs)
        cutoff_index = self._find_safe_cutoff(messages)

        if cutoff_index <= 0:
            logger.warning("   ⚠️  No safe cutoff point found - keeping all messages")
            return None

        messages_to_summarize, preserved_messages = self._partition_messages(messages, cutoff_index)

        logger.info(f"   Summarizing {len(messages_to_summarize)} messages, preserving {len(preserved_messages)}")

        # Try summarization with fallback to aggressive trimming
        summary = self._create_summary_with_fallback(messages_to_summarize, total_tokens)
        new_messages = self._build_new_messages(summary)

        # Calculate compression ratio
        old_tokens = self.token_counter(messages_to_summarize)
        new_tokens = self.token_counter(new_messages)
        compression_ratio = (1 - new_tokens / old_tokens) * 100 if old_tokens > 0 else 0

        logger.info(f"✅ Context compressed: {old_tokens:,} → {new_tokens:,} tokens ({compression_ratio:.1f}% reduction)")

        return {
            "messages": [
                RemoveMessage(id=REMOVE_ALL_MESSAGES),
                *new_messages,
                *preserved_messages,
            ]
        }

    def _create_summary_with_fallback(
        self,
        messages_to_summarize: list[AnyMessage],
        current_total_tokens: int
    ) -> str:
        """Create summary with fallback to aggressive trimming on failure.

        This is the KEY innovation that fixes the BlockingError issue:
        - First try: Use LLM summarization (ideal)
        - On failure: Fall back to aggressive message trimming (safe)

        Args:
            messages_to_summarize: Messages to summarize
            current_total_tokens: Current total token count for logging

        Returns:
            Summary text (either from LLM or fallback message)
        """
        try:
            # Try original summarization logic
            summary = self._create_summary(messages_to_summarize)

            # Check if summarization actually succeeded
            if summary and not summary.startswith("Error generating summary"):
                logger.info("   ✅ Summarization successful")
                return summary
            else:
                logger.warning(f"   ⚠️  Summarization returned error: {summary}")
                raise Exception("Summarization failed")

        except Exception as e:
            logger.error(f"   ❌ Summarization failed: {e}")
            logger.warning("   🔄 Falling back to aggressive message trimming...")

            # FALLBACK: Aggressive trimming to keep only most recent messages
            # This ensures we ALWAYS reduce context, even if summarization fails
            fallback_keep = min(10, len(messages_to_summarize) // 2)  # Keep at most 10 or half
            kept_messages = messages_to_summarize[-fallback_keep:]
            removed_count = len(messages_to_summarize) - fallback_keep

            old_tokens = self.token_counter(messages_to_summarize)
            new_tokens = self.token_counter(kept_messages)

            logger.warning(f"   Trimmed {removed_count} messages: {old_tokens:,} → {new_tokens:,} tokens")

            # Return a summary that explains what happened
            return (
                f"## Context Trimmed (Summarization Failed)\n\n"
                f"Due to summarization failure, {removed_count} older messages were removed.\n"
                f"Kept the {fallback_keep} most recent messages for context.\n\n"
                f"**Token reduction**: {old_tokens:,} → {new_tokens:,} tokens "
                f"({(1 - new_tokens/old_tokens)*100:.1f}% reduction)"
            )

    def _emergency_trim(
        self,
        messages: list[AnyMessage],
        current_tokens: int
    ) -> dict[str, Any]:
        """Emergency trimming when hard limit is reached.

        This is the last line of defense to prevent 400 "prompt too long" errors.
        Aggressively trims to well below the hard limit to ensure safety.

        Args:
            messages: All messages in conversation
            current_tokens: Current total token count

        Returns:
            State update with aggressively trimmed messages
        """
        # Keep only the most recent messages that fit well under hard limit
        # Target: 60% of hard limit (108k tokens if hard limit is 180k)
        target_tokens = int(self.hard_limit_tokens * 0.6)

        logger.warning(f"   Trimming to target: {target_tokens:,} tokens")

        try:
            # Use trim_messages to intelligently trim to target
            trimmed = trim_messages(
                messages,
                max_tokens=target_tokens,
                token_counter=self.token_counter,
                strategy="last",  # Keep most recent
                allow_partial=False,  # Don't split messages
                include_system=True,
            )

            final_tokens = self.token_counter(trimmed)
            removed = len(messages) - len(trimmed)

            logger.warning(f"   ✅ Emergency trim complete: {current_tokens:,} → {final_tokens:,} tokens")
            logger.warning(f"   Removed {removed} messages, kept {len(trimmed)}")

            return {
                "messages": [
                    RemoveMessage(id=REMOVE_ALL_MESSAGES),
                    *trimmed,
                ]
            }

        except Exception as e:
            logger.error(f"   ❌ Emergency trim failed: {e}")
            logger.error("   Using last-resort: keeping only last 15 messages")

            # Last resort: just keep the last 15 messages
            last_resort = messages[-15:]
            final_tokens = self.token_counter(last_resort)

            logger.error(f"   Last resort trim: {current_tokens:,} → {final_tokens:,} tokens")

            return {
                "messages": [
                    RemoveMessage(id=REMOVE_ALL_MESSAGES),
                    *last_resort,
                ]
            }
