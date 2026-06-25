"""Multi-API Manager for Claude Code Telegram Bot.

Supports multiple API providers with dynamic switching:
- Claude API
- OpenAI API
- Local LLM (Ollama)
- Custom HTTP APIs
"""

import asyncio
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import httpx
import structlog
# Try to import Claude SDK components
try:
    from claude_code_sdk import (
        ClaudeCodeOptions,
        ClaudeSDKError,
        CLIConnectionError,
        CLINotFoundError,
        Message,
        ProcessError,
        query,
    )
    CLAUDE_SDK_AVAILABLE = True
except ImportError:
    # Create dummy classes for testing without Claude SDK
    CLAUDE_SDK_AVAILABLE = False
    class ClaudeCodeOptions:
        def __init__(self, max_tokens=None, temperature=None):
            self.max_tokens = max_tokens
            self.temperature = temperature

    class ClaudeSDKError(Exception):
        pass

    class Message:
        pass

    class UserMessage(Message):
        def __init__(self, content):
            self.content = content

    class AssistantMessage(Message):
        def __init__(self, content):
            self.content = content

from ..config.settings import Settings
from .exceptions import ClaudeParsingError, ClaudeTimeoutError

logger = structlog.get_logger()


class APIProvider(Enum):
    """Supported API providers."""
    CLAUDE = "claude"
    OPENAI = "openai"
    OLLAMA = "ollama"
    LOCAL = "local"


@dataclass
class APIConfig:
    """Configuration for an API provider."""
    provider: APIProvider
    api_key: Optional[str] = None
    api_url: Optional[str] = None
    model: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    timeout: Optional[int] = None
    enabled: bool = True
    cost_per_token: float = 0.0


@dataclass
class APICost:
    """Cost tracking for API usage."""
    provider: APIProvider
    tokens_used: int = 0
    cost_usd: float = 0.0
    last_reset: datetime = field(default_factory=datetime.now)

    def add_usage(self, tokens: int, cost_per_token: float):
        """Add token usage and update cost."""
        self.tokens_used += tokens
        self.cost_usd += tokens * cost_per_token


class CostTracker:
    """Tracks API usage costs and enables dynamic switching."""

    def __init__(self, config: Settings):
        self.config = config
        self.user_costs: Dict[int, Dict[APIProvider, APICost]] = {}
        self.reset_intervals = {
            "daily": timedelta(days=1),
            "weekly": timedelta(weeks=1),
            "monthly": timedelta(days=30),
        }

    def get_user_cost(self, user_id: int, provider: APIProvider) -> APICost:
        """Get or create cost tracker for user-provider."""
        if user_id not in self.user_costs:
            self.user_costs[user_id] = {}

        if provider not in self.user_costs[user_id]:
            self.user_costs[user_id][provider] = APICost(provider=provider)

        # Check if we need to reset
        cost_data = self.user_costs[user_id][provider]
        if self.config.cost_reset_interval:
            if datetime.now() - cost_data.last_reset > self.reset_intervals[self.config.cost_reset_interval]:
                cost_data.tokens_used = 0
                cost_data.cost_usd = 0.0
                cost_data.last_reset = datetime.now()

        return cost_data

    def add_usage(self, user_id: int, provider: APIProvider, tokens: int, cost_per_token: float):
        """Add token usage for user."""
        cost_data = self.get_user_cost(user_id, provider)
        cost_data.add_usage(tokens, cost_per_token)

    def get_user_total_cost(self, user_id: int) -> float:
        """Get total cost for all providers for user."""
        total = 0.0
        if user_id in self.user_costs:
            for cost_data in self.user_costs[user_id].values():
                total += cost_data.cost_usd
        return total


class BaseAPIProvider(ABC):
    """Base class for API providers."""

    def __init__(self, config: APIConfig):
        self.config = config

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        **kwargs
    ) -> Dict[str, Any]:
        """Generate chat completion."""
        pass

    @abstractmethod
    def get_cost_per_token(self) -> float:
        """Get cost per token for this provider."""
        pass


class ClaudeProvider(BaseAPIProvider):
    """Claude API provider."""

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        **kwargs
    ) -> Dict[str, Any]:
        """Generate chat completion using Claude API."""
        if not CLAUDE_SDK_AVAILABLE:
            raise Exception("Claude SDK not available. Install with: pip install claude-code-sdk")

        try:
            # Convert messages to Claude format
            claude_messages = []
            for msg in messages:
                if msg["role"] == "user":
                    claude_messages.append(UserMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    claude_messages.append(AssistantMessage(content=msg["content"]))
                elif msg["role"] == "system":
                    claude_messages.append(UserMessage(content=msg["content"]))

            # Create options
            options = ClaudeCodeOptions(
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
            )

            # Execute query
            response = await query(
                prompt=messages[-1]["content"],  # Use last message as prompt
                options=options,
            )

            return {
                "content": response.content,
                "tokens_used": len(response.content.split()),
                "model": self.config.model,
                "provider": APIProvider.CLAUDE.value,
            }

        except Exception as e:
            logger.error("Claude API error", error=str(e))
            raise

    def get_cost_per_token(self) -> float:
        """Get cost per token for Claude."""
        # Simplified cost calculation
        return 0.000015  # ~$15 per 1M tokens for Claude 3 Sonnet


class OpenAIProvider(BaseAPIProvider):
    """OpenAI API provider."""

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        **kwargs
    ) -> Dict[str, Any]:
        """Generate chat completion using OpenAI API."""
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    f"{self.config.api_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.config.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.config.model,
                        "messages": messages,
                        "max_tokens": self.config.max_tokens,
                        "temperature": self.config.temperature,
                    },
                )
                response.raise_for_status()

                data = response.json()
                content = data["choices"][0]["message"]["content"]
                tokens_used = data.get("usage", {}).get("total_tokens", 0)

                return {
                    "content": content,
                    "tokens_used": tokens_used,
                    "model": self.config.model,
                    "provider": APIProvider.OPENAI.value,
                }

        except Exception as e:
            logger.error("OpenAI API error", error=str(e))
            raise

    def get_cost_per_token(self) -> float:
        """Get cost per token for OpenAI."""
        # Simplified cost calculation
        if "gpt-4" in self.config.model:
            return 0.00003  # ~$30 per 1M tokens for GPT-4
        else:
            return 0.000002  # ~$2 per 1M tokens for GPT-3.5


class OllamaProvider(BaseAPIProvider):
    """Ollama (local LLM) provider."""

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        **kwargs
    ) -> Dict[str, Any]:
        """Generate chat completion using Ollama API."""
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    f"{self.config.api_url}/api/chat",
                    json={
                        "model": self.config.model,
                        "messages": messages,
                        "options": {
                            "temperature": self.config.temperature,
                            "num_predict": self.config.max_tokens,
                        },
                    },
                )
                response.raise_for_status()

                data = response.json()
                content = data["response"]
                # Estimate tokens (Ollama doesn't return token count)
                tokens_used = len(content.split()) * 1.3  # Rough estimate

                return {
                    "content": content,
                    "tokens_used": tokens_used,
                    "model": self.config.model,
                    "provider": APIProvider.OLLAMA.value,
                }

        except Exception as e:
            logger.error("Ollama API error", error=str(e))
            raise

    def get_cost_per_token(self) -> float:
        """Get cost per token for Ollama (free)."""
        return 0.0


class MultiAPIManager:
    """Manages multiple API providers with dynamic switching."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.providers: Dict[APIProvider, BaseAPIProvider] = {}
        self.cost_tracker = CostTracker(settings)
        self.primary_provider = APIProvider.CLAUDE
        self.fallback_provider = APIProvider.OLLAMA

        self._setup_providers()

    def _setup_providers(self):
        """Setup all configured providers."""
        # Claude provider
        if self.settings.anthropic_api_key:
            claude_config = APIConfig(
                provider=APIProvider.CLAUDE,
                api_key=self.settings.anthropic_api_key,
                api_url=self.settings.anthropic_api_url,
                model=self.settings.anthropic_model,
                max_tokens=self.settings.anthropic_max_tokens,
                temperature=self.settings.anthropic_temperature,
            )
            self.providers[APIProvider.CLAUDE] = ClaudeProvider(claude_config)

        # OpenAI provider
        if self.settings.openai_api_key:
            openai_config = APIConfig(
                provider=APIProvider.OPENAI,
                api_key=self.settings.openai_api_key,
                api_url=self.settings.openai_api_url,
                model=self.settings.openai_model,
                max_tokens=self.settings.openai_max_tokens,
                temperature=self.settings.openai_temperature,
            )
            self.providers[APIProvider.OPENAI] = OpenAIProvider(openai_config)

        # Ollama provider
        ollama_config = APIConfig(
            provider=APIProvider.OLLAMA,
            api_url=self.settings.ollama_api_url,
            model=self.settings.ollama_model,
            max_tokens=self.settings.ollama_max_tokens,
            temperature=self.settings.ollama_temperature,
        )
        self.providers[APIProvider.OLLAMA] = OllamaProvider(ollama_config)

    def get_current_provider(self, user_id: int) -> APIProvider:
        """Get the current API provider for a user."""
        if not self.settings.enable_dynamic_switching:
            return self.primary_provider

        # Check cost threshold
        if self.settings.cost_switch_threshold:
            user_cost = self.cost_tracker.get_user_total_cost(user_id)
            if user_cost >= self.settings.cost_switch_threshold:
                logger.info(
                    "Switching to local LLM due to cost threshold",
                    user_cost=user_cost,
                    threshold=self.settings.cost_switch_threshold,
                )
                return APIProvider.OLLAMA

        # Check time-based switching
        if self.settings.local_hours_start and self.settings.local_hours_end:
            current_hour = datetime.now().hour
            local_hours_start = self.settings.local_hours_start
            local_hours_end = self.settings.local_hours_end

            # Handle overnight hours
            if local_hours_start > local_hours_end:
                # Current time is overnight
                if current_hour >= local_hours_start or current_hour < local_hours_end:
                    return APIProvider.OLLAMA
            else:
                # Current time is during local hours
                if local_hours_start <= current_hour < local_hours_end:
                    return APIProvider.OLLAMA

        # Check weekend switching
        if self.settings.enable_weekend_local:
            current_day = datetime.now().weekday()  # 0=Monday, 6=Sunday
            if current_day >= 5:  # Saturday or Sunday
                return APIProvider.OLLAMA

        # Use primary provider
        return self.primary_provider

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        user_id: int,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate chat completion with dynamic provider selection."""
        provider = self.get_current_provider(user_id)

        # Try primary provider first
        try:
            result = await self.providers[provider].chat_completion(messages, **kwargs)

            # Track usage
            if self.settings.enable_cost_tracking:
                cost_per_token = self.providers[provider].get_cost_per_token()
                self.cost_tracker.add_usage(user_id, provider, result["tokens_used"], cost_per_token)

            return result

        except Exception as e:
            logger.error(f"Primary provider {provider} failed", error=str(e))

            # Try fallback provider
            if self.settings.enable_auto_fallback and provider != self.fallback_provider:
                logger.info(f"Falling back to {self.fallback_provider}")
                try:
                    result = await self.providers[self.fallback_provider].chat_completion(
                        messages, **kwargs
                    )

                    # Track fallback usage
                    if self.settings.enable_cost_tracking:
                        cost_per_token = self.providers[self.fallback_provider].get_cost_per_token()
                        self.cost_tracker.add_usage(
                            user_id, self.fallback_provider, result["tokens_used"], cost_per_token
                        )

                    return result

                except Exception as fallback_error:
                    logger.error("Fallback provider also failed", error=str(fallback_error))
                    raise

            raise

    def get_provider_info(self, user_id: int) -> Dict[str, Any]:
        """Get current provider and cost information."""
        provider = self.get_current_provider(user_id)
        user_cost = self.cost_tracker.get_user_total_cost(user_id)

        return {
            "current_provider": provider.value,
            "available_providers": list(p.value for p in self.providers.keys()),
            "user_cost": user_cost,
            "cost_threshold": self.settings.cost_switch_threshold,
            "dynamic_switching_enabled": self.settings.enable_dynamic_switching,
        }

    async def switch_provider(self, user_id: int, provider: APIProvider):
        """Manually switch provider for a user."""
        if provider not in self.providers:
            raise ValueError(f"Provider {provider} not available")

        logger.info(f"Manual provider switch for user {user_id}", provider=provider.value)
        # Update user-specific preference (implementation would extend this)

    async def get_user_cost_summary(self, user_id: int) -> Dict[str, Any]:
        """Get detailed cost summary for a user."""
        summary = {}
        user_cost_data = self.user_costs.get(user_id, {})

        for provider, cost_data in user_cost_data.items():
            summary[provider.value] = {
                "tokens_used": cost_data.tokens_used,
                "cost_usd": cost_data.cost_usd,
                "last_reset": cost_data.last_reset.isoformat(),
            }

        summary["total"] = {
            "cost_usd": self.cost_tracker.get_user_total_cost(user_id),
        }

        return summary