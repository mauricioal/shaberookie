"""
Adapter interfaces and factory for LLM provider integration.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type

from shaberookie.common.exceptions import LLMProviderError
from shaberookie.config.loader import LLMConfig
from shaberookie.llm.langchain_driver import LangChainDriver


class LLMAdapter(ABC):
    """Common interface for invoking a language model."""

    @abstractmethod
    async def generate_response(
        self,
        *,
        system_prompt: str,
        messages: list[dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Produce a response given the conversation context."""


class LangChainAdapter(LLMAdapter):
    """Adapter that delegates to LangChainDriver."""

    def __init__(self, driver: LangChainDriver) -> None:
        self._driver = driver

    async def generate_response(
        self,
        *,
        system_prompt: str,
        messages: list[dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        return await self._driver.generate(
            system_prompt=system_prompt,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )


class LLMFactory:
    """Factory for constructing LLMAdapter instances based on configuration."""

    _registry: Dict[str, Type[LLMAdapter]] = {
        "openai": LangChainAdapter,
        "anthropic": LangChainAdapter,
        "ollama": LangChainAdapter,
    }

    @classmethod
    def create(
        cls,
        provider: str,
        config: LLMConfig,
        driver: Optional[LangChainDriver] = None,
        **kwargs: Any,
    ) -> LLMAdapter:
        provider_key = provider.lower()
        adapter_cls = cls._registry.get(provider_key)
        if not adapter_cls:
            raise LLMProviderError(f"Unsupported LLM provider: {provider}")
        if adapter_cls is LangChainAdapter:
            if driver is None:
                driver = LangChainDriver.from_config(
                    config,
                    provider=provider_key,
                    api_key=config.api_key,
                    **kwargs,
                )
            return LangChainAdapter(driver)
        raise LLMProviderError(f"No adapter available for provider: {provider}")

    @classmethod
    def register(cls, provider: str, adapter_cls: Type[LLMAdapter]) -> None:
        cls._registry[provider.lower()] = adapter_cls