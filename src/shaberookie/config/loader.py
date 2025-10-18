"""
Configuration loader for shaberookie.

This module centralizes configuration management by merging YAML defaults,
environment variable overrides, and `.env` values into a validated settings object.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

import orjson
import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError, root_validator

CONFIG_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CONFIG_DIR.parent.parent
DEFAULT_CONFIG_PATH = CONFIG_DIR / "config.yaml"
ENV_FILE = PROJECT_ROOT.parent / ".env"


class RetryConfig(BaseModel):
    max_attempts: int = Field(default=3, ge=1)
    backoff_factor: float = Field(default=0.5, ge=0.0)
    max_backoff_seconds: int = Field(default=8, ge=1)


class RenshuuConfig(BaseModel):
    api_base: str = Field(default="https://api.renshuu.org/v1")
    api_key: Optional[str] = None
    request_timeout_seconds: int = Field(default=10, ge=1)
    retry: RetryConfig = Field(default_factory=RetryConfig)


class LLMConfig(BaseModel):
    provider: str = Field(default="openai")
    model: str = Field(default="gpt-4o-mini")
    api_key: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=512, ge=1)
    system_prompt_path: Optional[str] = None
    response_conformity_checks: bool = True


class GradioConfig(BaseModel):
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=7860, ge=1, le=65535)
    share: bool = False


class ConsoleConfig(BaseModel):
    history_path: str = Field(default="data/console_history")


class ChatConfig(BaseModel):
    gradio: GradioConfig = Field(default_factory=GradioConfig)
    console: ConsoleConfig = Field(default_factory=ConsoleConfig)


class AppConfig(BaseModel):
    name: str = Field(default="shaberookie")
    log_level: str = Field(default="INFO")
    log_dir: str = Field(default="logs")
    conversation_log_path: str = Field(default="data/conversations")
    profile_store_path: str = Field(default="data/profiles")
    cache_ttl_seconds: int = Field(default=900, ge=0)
    cache_backend: str = Field(default="memory")


class StorageConfig(BaseModel):
    redis_url: Optional[str] = None
    sqlite_path: str = Field(default="data/shaberookie.sqlite")


class MetricsConfig(BaseModel):
    enabled: bool = False
    endpoint: Optional[str] = None


class Settings(BaseModel):
    app: AppConfig = Field(default_factory=AppConfig)
    renshuu: RenshuuConfig = Field(default_factory=RenshuuConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    chat: ChatConfig = Field(default_factory=ChatConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)

    class Config:
        frozen = True

    @root_validator(pre=True)
    def validate_structures(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure nested dicts exist even if missing from the raw configuration."""
        defaults = cls.model_construct().model_dump()
        merged: Dict[str, Any] = orjson.loads(orjson.dumps(defaults))
        merged.update(values or {})
        return merged


def _load_yaml_config(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _load_environment_overrides(prefix: str = "SHABEROOOKIE_") -> Dict[str, Any]:
    overrides: Dict[str, Any] = {}
    prefix_len = len(prefix)
    for key, value in os.environ.items():
        if not key.startswith(prefix):
            continue
        normalized_key = key[prefix_len:].lower().split("__")
        _assign_nested_key(overrides, normalized_key, value)
    return overrides


def _assign_nested_key(container: Dict[str, Any], key_parts: Any, value: Any) -> None:
    current = container
    *parents, last = key_parts
    for part in parents:
        current = current.setdefault(part, {})
    current[last] = _parse_env_value(value)


def _parse_env_value(value: str) -> Any:
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


@lru_cache(maxsize=1)
def get_settings(config_path: Optional[Path] = None, *, refresh: bool = False) -> Settings:
    """
    Load and cache application settings.

    Parameters
    ----------
    config_path:
        Optional override for the YAML configuration file.
    refresh:
        If True, forces cache invalidation and reload.
    """
    if refresh:
        get_settings.cache_clear()  # type: ignore[attr-defined]
    load_dotenv(dotenv_path=ENV_FILE, override=False)

    base_config = _load_yaml_config(config_path or DEFAULT_CONFIG_PATH)
    env_overrides = _load_environment_overrides()
    merged_config = _deep_merge_dicts(base_config, env_overrides)
    try:
        return Settings(**merged_config)
    except ValidationError as exc:
        raise RuntimeError(f"Configuration validation failed: {exc}") from exc


def _deep_merge_dicts(base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    result = orjson.loads(orjson.dumps(base))
    for key, value in overrides.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = _deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


__all__ = ["Settings", "get_settings"]