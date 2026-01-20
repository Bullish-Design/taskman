"""Configuration management for TaskMan."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TaskManConfig(BaseSettings):
    """TaskMan configuration settings.

    Can be configured via:
    - Environment variables (TASKMAN_*)
    - Config file (~/.config/taskman/config.toml or TASKMAN_CONFIG_PATH)
    """

    model_config = SettingsConfigDict(
        env_prefix="TASKMAN_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Taskwarrior settings
    task_bin: str = Field(default="task", description="Path to taskwarrior binary")
    taskrc_path: Path | None = Field(default=None, description="Path to taskrc file")

    # Taskdantic settings
    uda_models_modules: list[str] = Field(
        default_factory=list,
        description="Python module paths for UDA model discovery",
    )
    uda_config_path: Path | None = Field(
        default=None,
        description="Path to write UDA config (defaults to ~/.taskrc-udas)",
    )

    # LLM settings
    llm_model: str = Field(default="gpt-4", description="LLM model to use")
    llm_temperature: float = Field(default=0.1, description="LLM temperature")
    llm_max_retries: int = Field(default=3, description="Max retries for LLM validation")

    # Safety settings
    default_mode: str = Field(default="safe", description="Default mode: 'safe' or 'power'")

    # Editor settings
    editor: str = Field(
        default_factory=lambda: os.environ.get("EDITOR", "vim"),
        description="Editor command for reviewing revise scripts",
    )

    # Output settings
    verbose: bool = Field(default=False, description="Enable verbose output")
    show_prompt: bool = Field(default=False, description="Show prompts sent to LLM")

    @property
    def uda_config_file(self) -> Path:
        """Get the UDA config file path, with sensible default."""
        if self.uda_config_path:
            return self.uda_config_path
        return Path.home() / ".taskrc-udas"

    @classmethod
    def load(cls, config_path: Path | None = None) -> TaskManConfig:
        """Load configuration from file and environment.

        Args:
            config_path: Optional path to config file. If not provided,
                        looks for TASKMAN_CONFIG_PATH env var or default location.

        Returns:
            Loaded configuration
        """
        # TODO: Add support for TOML config file loading
        # For now, just use environment variables
        return cls()


class ReviseScriptConfig(BaseModel):
    """Configuration for a revise script execution."""

    stop_on_error: bool = Field(
        default=True,
        description="Stop execution on first error",
    )
    dry_run: bool = Field(
        default=False,
        description="Parse and validate without executing",
    )
    show_diff: bool = Field(
        default=True,
        description="Show diff summary before execution",
    )
    require_confirmation: bool = Field(
        default=True,
        description="Require user confirmation before execution",
    )


# Global config instance (lazy-loaded)
_config: TaskManConfig | None = None


def get_config() -> TaskManConfig:
    """Get the global TaskMan configuration."""
    global _config
    if _config is None:
        _config = TaskManConfig.load()
    return _config


def set_config(config: TaskManConfig) -> None:
    """Set the global TaskMan configuration."""
    global _config
    _config = config
