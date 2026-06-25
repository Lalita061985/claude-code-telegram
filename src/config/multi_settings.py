"""Enhanced Configuration Management with Multi-API Support.

Features:
- Environment variable loading
- Type validation
- Default values
- Computed properties
- Environment-specific settings
- Multi-API provider support
- Dynamic switching configuration
"""

from pathlib import Path
from typing import Any, List, Literal, Optional, Union

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.utils.constants import (
    DEFAULT_CLAUDE_MAX_COST_PER_USER,
    DEFAULT_CLAUDE_MAX_TURNS,
    DEFAULT_CLAUDE_TIMEOUT_SECONDS,
    DEFAULT_DATABASE_URL,
    DEFAULT_MAX_SESSIONS_PER_USER,
    DEFAULT_RATE_LIMIT_BURST,
    DEFAULT_RATE_LIMIT_REQUESTS,
    DEFAULT_RATE_LIMIT_WINDOW,
    DEFAULT_SESSION_TIMEOUT_HOURS,
)


class MultiApiSettings(BaseSettings):
    """Multi-API configuration settings."""

    # Primary API provider
    primary_api_provider: Literal["claude", "openai", "ollama", "local"] = Field(
        default="claude",
        description="Primary API provider to use"
    )

    # Claude API settings
    anthropic_api_key: Optional[SecretStr] = Field(
        default=None,
        description="Anthropic API key"
    )
    anthropic_api_url: str = Field(
        default="https://api.anthropic.com",
        description="Anthropic API base URL"
    )
    anthropic_model: str = Field(
        default="claude-3-sonnet-20240229",
        description="Anthropic model to use"
    )
    anthropic_max_tokens: int = Field(
        default=4000,
        description="Maximum tokens for Claude API"
    )
    anthropic_temperature: float = Field(
        default=0.7,
        description="Temperature for Claude API"
    )

    # OpenAI API settings
    openai_api_key: Optional[SecretStr] = Field(
        default=None,
        description="OpenAI API key"
    )
    openai_api_url: str = Field(
        default="https://api.openai.com/v1",
        description="OpenAI API base URL"
    )
    openai_model: str = Field(
        default="gpt-4-turbo-preview",
        description="OpenAI model to use"
    )
    openai_max_tokens: int = Field(
        default=4000,
        description="Maximum tokens for OpenAI API"
    )
    openai_temperature: float = Field(
        default=0.7,
        description="Temperature for OpenAI API"
    )

    # Local LLM (Ollama) settings
    ollama_api_url: str = Field(
        default="http://localhost:11434",
        description="Ollama API base URL"
    )
    ollama_model: str = Field(
        default="llama3:8b",
        description="Ollama model to use"
    )
    ollama_max_tokens: int = Field(
        default=2000,
        description="Maximum tokens for Ollama API"
    )
    ollama_temperature: float = Field(
        default=0.7,
        description="Temperature for Ollama API"
    )

    # Dynamic switching settings
    enable_dynamic_switching: bool = Field(
        default=True,
        description="Enable automatic API switching based on conditions"
    )
    cost_switch_threshold: float = Field(
        default=5.0,
        description="Switch to local LLM when cost reaches this amount (USD)"
    )
    local_hours_start: Optional[int] = Field(
        default=None,
        description="Start of local LLM hours (24-hour format)"
    )
    local_hours_end: Optional[int] = Field(
        default=None,
        description="End of local LLM hours (24-hour format)"
    )
    enable_weekend_local: bool = Field(
        default=True,
        description="Switch to local LLM on weekends"
    )

    # Fallback settings
    fallback_api_provider: Literal["claude", "openai", "ollama", "local"] = Field(
        default="local",
        description="Fallback API if primary fails"
    )
    enable_auto_fallback: bool = Field(
        default=True,
        description="Enable automatic fallback to alternative provider"
    )

    # Cost tracking settings
    enable_cost_tracking: bool = Field(
        default=True,
        description="Enable cost tracking for dynamic switching"
    )
    cost_reset_interval: Literal["daily", "weekly", "monthly"] = Field(
        default="monthly",
        description="Interval for resetting cost tracking"
    )

    @model_validator(mode='after')
    def validate_local_hours(self):
        """Validate local hours configuration."""
        if self.local_hours_start is not None and self.local_hours_end is not None:
            if self.local_hours_start < 0 or self.local_hours_start > 23:
                raise ValueError("local_hours_start must be between 0 and 23")
            if self.local_hours_end < 0 or self.local_hours_end > 23:
                raise ValueError("local_hours_end must be between 0 and 23")
        return self

    @model_validator(mode='after')
    def validate_fallback_provider(self):
        """Ensure fallback provider is different from primary."""
        if self.primary_api_provider == self.fallback_api_provider:
            raise ValueError("fallback_api_provider must be different from primary_api_provider")
        return self


class Settings(BaseSettings):
    """Enhanced application settings with multi-API support."""

    # Use model config to allow env file override
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )

    # === BASIC BOT SETTINGS ===
    telegram_bot_token: SecretStr = Field(
        ..., description="Telegram bot token from BotFather"
    )
    telegram_bot_username: str = Field(..., description="Bot username without @")
    approved_directory: Path = Field(..., description="Base directory for projects")
    allowed_users: Optional[List[int]] = Field(
        default=None, description="Allowed Telegram user IDs"
    )

    # === AUTHENTICATION ===
    enable_token_auth: bool = Field(
        default=False, description="Enable token-based authentication"
    )
    auth_token_secret: Optional[SecretStr] = Field(
        default=None, description="Secret for auth tokens"
    )
    use_sdk: bool = Field(
        default=True, description="Use Claude Python SDK instead of CLI"
    )

    # === CLAUDE SETTINGS ===
    claude_max_turns: int = Field(
        DEFAULT_CLAUDE_MAX_TURNS, description="Maximum conversation turns"
    )
    claude_timeout_seconds: int = Field(
        DEFAULT_CLAUDE_TIMEOUT_SECONDS, description="Timeout for Claude operations"
    )
    claude_max_cost_per_user: float = Field(
        DEFAULT_CLAUDE_MAX_COST_PER_USER, description="Maximum cost per user in USD"
    )
    claude_allowed_tools: List[str] = Field(
        default_factory=lambda: [
            "Read", "Write", "Edit", "Bash", "Glob", "Grep", "LS", "Task",
            "MultiEdit", "NotebookRead", "NotebookEdit", "WebFetch",
            "TodoRead", "TodoWrite", "WebSearch"
        ],
        description="List of allowed Claude tools"
    )

    # === RATE LIMITING ===
    rate_limit_requests: int = Field(
        DEFAULT_RATE_LIMIT_REQUESTS, description="Number of requests per window"
    )
    rate_limit_window: int = Field(
        DEFAULT_RATE_LIMIT_WINDOW, description="Rate limit window in seconds"
    )
    rate_limit_burst: int = Field(
        DEFAULT_RATE_LIMIT_BURST, description="Burst capacity for rate limiting"
    )

    # === STORAGE ===
    database_url: str = Field(
        DEFAULT_DATABASE_URL, description="Database URL"
    )
    session_timeout_hours: int = Field(
        DEFAULT_SESSION_TIMEOUT_HOURS, description="Session timeout in hours"
    )
    max_sessions_per_user: int = Field(
        DEFAULT_MAX_SESSIONS_PER_USER, description="Maximum concurrent sessions"
    )

    # === FEATURES ===
    enable_mcp: bool = Field(
        default=False, description="Enable Model Context Protocol"
    )
    mcp_config_path: Optional[Path] = Field(
        default=None, description="Path to MCP configuration file"
    )
    enable_git_integration: bool = Field(
        default=True, description="Enable Git integration"
    )
    enable_file_uploads: bool = Field(
        default=True, description="Enable file upload handling"
    )
    enable_quick_actions: bool = Field(
        default=True, description="Enable quick action buttons"
    )
    enable_session_export: bool = Field(
        default=True, description="Enable session export functionality"
    )
    enable_image_uploads: bool = Field(
        default=True, description="Enable image/screenshot handling"
    )
    enable_conversation_mode: bool = Field(
        default=True, description="Enable conversation enhancements"
    )

    # === MONITORING ===
    log_level: str = Field(
        default="INFO", description="Log level (DEBUG, INFO, WARNING, ERROR)"
    )
    enable_telemetry: bool = Field(
        default=False, description="Enable anonymous telemetry"
    )
    sentry_dsn: Optional[str] = Field(
        default=None, description="Sentry DSN for error tracking"
    )

    # === DEVELOPMENT ===
    environment: Literal["development", "testing", "production"] = Field(
        default="development", description="Environment"
    )
    debug: bool = Field(default=False, description="Enable debug mode")
    development_mode: bool = Field(
        default=True, description="Enable development features"
    )

    # === MULTI-API SETTINGS ===
    multi_api: MultiApiSettings = Field(default_factory=MultiApiSettings)

    # === COST AND PERFORMANCE ===
    max_tokens_claude: int = Field(
        default=4000, description="Max tokens for Claude API"
    )
    max_tokens_openai: int = Field(
        default=4000, description="Max tokens for OpenAI API"
    )
    max_tokens_local: int = Field(
        default=2000, description="Max tokens for local LLM"
    )

    @property
    def anthropic_api_key_str(self) -> Optional[str]:
        """Get Anthropic API key as string."""
        return self.multi_api.anthropic_api_key.get_secret_value() if self.multi_api.anthropic_api_key else None

    @property
    def openai_api_key_str(self) -> Optional[str]:
        """Get OpenAI API key as string."""
        return self.multi_api.openai_api_key.get_secret_value() if self.multi_api.openai_api_key else None

    @property
    def auth_token_secret_str(self) -> Optional[str]:
        """Get auth token secret as string."""
        return self.auth_token_secret.get_secret_value() if self.auth_token_secret else None

    @field_validator('allowed_users', mode='before')
    @classmethod
    def parse_allowed_users(cls, v):
        """Parse allowed users from string or list."""
        if isinstance(v, str):
            if not v.strip():
                return None
            return [int(x.strip()) for x in v.split(',')]
        return v

    @model_validator(mode='after')
    def validate_api_configuration(self):
        """Validate that at least one API is configured."""
        if not self.multi_api.anthropic_api_key and not self.multi_api.openai_api_key:
            if not self.multi_api.ollama_api_url:
                raise ValueError("At least one API provider must be configured")
        return self


def create_settings() -> Settings:
    """Create settings instance."""
    return Settings()