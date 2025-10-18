"""
Caching helpers for shaberookie.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from shaberookie.common.exceptions import ConfigurationError


class CacheBackend(ABC):
    """Abstract cache interface."""

    @abstractmethod
    def get(self, key: str) -> Any:
        """Retrieve a cached value."""

    @abstractmethod
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Store a value with optional TTL."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete a cached value."""


class InMemoryCache(CacheBackend):
    """Simple in-memory cache for development use."""

    def __init__(self) -> None:
        self._store: Dict[str, Any] = {}
        self._expirations: Dict[str, datetime] = {}

    def get(self, key: str) -> Any:
        expires_at = self._expirations.get(key)
        if expires_at and datetime.utcnow() > expires_at:
            self.delete(key)
            return None
        return self._store.get(key)

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        self._store[key] = value
        if ttl_seconds:
            self._expirations[key] = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        elif key in self._expirations:
            del self._expirations[key]

    def delete(self, key: str) -> None:
        self._store.pop(key, None)
        self._expirations.pop(key, None)


class RedisCache(CacheBackend):
    """Redis-backed cache adapter."""

    def __init__(self, redis_client) -> None:
        self._client = redis_client

    def get(self, key: str) -> Any:
        value = self._client.get(key)
        if value is None:
            return None
        return value

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        if ttl_seconds:
            self._client.setex(key, ttl_seconds, value)
        else:
            self._client.set(key, value)

    def delete(self, key: str) -> None:
        self._client.delete(key)


def get_cache_backend(
    backend_name: str,
    *,
    redis_url: Optional[str] = None,
) -> CacheBackend:
    normalized = backend_name.lower()
    if normalized == "memory":
        return InMemoryCache()
    if normalized == "redis":
        if not redis_url:
            raise ConfigurationError("Redis cache selected but REDIS_URL is not configured.")
        try:
            import redis  # type: ignore
        except ImportError as exc:  # pragma: no cover - runtime guard
            raise ConfigurationError("Redis support requires the 'redis' extra.") from exc
        client = redis.from_url(redis_url)
        return RedisCache(client)
    raise ConfigurationError(f"Unsupported cache backend: {backend_name}")