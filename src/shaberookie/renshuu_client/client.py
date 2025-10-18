"""
HTTP client for interacting with the Renshuu API.

The client is designed to be resilient (retries, timeouts) and testable by accepting
an externally provided httpx.AsyncClient or httpx.Client instance. In production we
prefer the async client since Renshuu endpoints are network-bound.

Usage example
-------------
```python
from shaberookie.renshuu_client.client import RenshuuApiClient
from shaberookie.config.loader import get_settings

settings = get_settings()
client = RenshuuApiClient.from_settings(settings.renshuu)
profile = await client.get_user_profile(user_id="12345")
```
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Union

import httpx
from tenacity import AsyncRetrying, RetryError, retry, stop_after_attempt, wait_exponential

from shaberookie.common.exceptions import AuthenticationError, RateLimitError, RenshuuAPIError
from shaberookie.config.loader import RenshuuConfig


class RenshuuApiClient:
    """High-level API client that wraps HTTP calls to the Renshuu API."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        timeout_seconds: int = 10,
        client: Optional[Union[httpx.AsyncClient, httpx.Client]] = None,
        max_attempts: int = 3,
        backoff_factor: float = 0.5,
        max_backoff_seconds: int = 8,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout_seconds
        self._client = client
        self._max_attempts = max_attempts
        self._backoff_factor = backoff_factor
        self._max_backoff_seconds = max_backoff_seconds

    @classmethod
    def from_settings(cls, config: RenshuuConfig) -> "RenshuuApiClient":
        if not config.api_key:
            raise AuthenticationError("Renshuu API key is missing from configuration.")
        return cls(
            base_url=config.api_base,
            api_key=config.api_key,
            timeout_seconds=config.request_timeout_seconds,
            max_attempts=config.retry.max_attempts,
            backoff_factor=config.retry.backoff_factor,
            max_backoff_seconds=config.retry.max_backoff_seconds,
        )

    async def _ensure_async_client(self) -> httpx.AsyncClient:
        if isinstance(self._client, httpx.AsyncClient):
            return self._client
        return httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(self._timeout),
            headers=self._default_headers,
        )

    @property
    def _default_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Accept": "application/json",
            "User-Agent": "shaberookie/0.1",
        }

    async def _request(
        self, method: str, path: str, *, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        async_client = await self._ensure_async_client()
        try:
            async for attempt in AsyncRetrying(
                reraise=True,
                stop=stop_after_attempt(self._max_attempts),
                wait=wait_exponential(
                    multiplier=self._backoff_factor,
                    max=self._max_backoff_seconds,
                ),
            ):
                with attempt:
                    response = await async_client.request(
                        method, path, params=params, headers=self._default_headers
                    )
                    self._raise_for_status(response)
                    return response.json()
        except RetryError as exc:
            raise RenshuuAPIError(f"Exceeded retry attempts for {path}") from exc

    def _raise_for_status(self, response: httpx.Response) -> None:
        status = response.status_code
        if 200 <= status < 300:
            return
        if status == 401:
            raise AuthenticationError("Invalid or missing Renshuu API credentials.")
        if status == 429:
            raise RateLimitError("Renshuu API rate limit exceeded.")
        try:
            detail = response.json()
        except ValueError:
            detail = response.text
        raise RenshuuAPIError(f"Renshuu API error ({status}): {detail}")

    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Retrieve detailed profile information for the specified user."""
        path = f"/users/{user_id}/profile"
        return await self._request("GET", path)

    async def get_schedules(self, user_id: str) -> Dict[str, Any]:
        """Fetch active schedules for the user."""
        path = f"/users/{user_id}/schedules"
        return await self._request("GET", path)

    async def get_terms_for_schedule(
        self, schedule_id: str, *, category: str
    ) -> Dict[str, Any]:
        """Fetch terms for a given schedule and category (vocab, kanji, grammar)."""
        path = f"/schedules/{schedule_id}/terms"
        params = {"category": category}
        return await self._request("GET", path, params=params)

    async def list_terms(
        self, user_id: str, *, category: str, status_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """List all terms for a user filtered by category and optional status."""
        path = f"/users/{user_id}/terms"
        params = {"category": category}
        if status_filter:
            params["status"] = status_filter
        return await self._request("GET", path, params=params)

    async def close(self) -> None:
        """Close the underlying HTTP client if it was instantiated internally."""
        if isinstance(self._client, httpx.AsyncClient):
            await self._client.aclose()

    async def __aenter__(self) -> "RenshuuApiClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()