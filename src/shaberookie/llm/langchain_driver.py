"""
LangChain driver responsible for interacting with configured language models.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from langchain.chat_models.base import BaseChatModel
from langchain.schema import AIMessage, HumanMessage, SystemMessage

from shaberookie.common.exceptions import LLMProviderError
from shaberookie.config.loader import LLMConfig


class LangChainDriver:
    """Manage LangChain chat model invocation with standardized prompts."""

    def __init__(
        self,
        chat_model: BaseChatModel,
        *,
        default_temperature: float,
        default_max_tokens: int,
    ) -> None:
        self._chat_model = chat_model
        self._default_temperature = default_temperature
        self._default_max_tokens = default_max_tokens

    @classmethod
    def from_config(
        cls,
        config: LLMConfig,
        *,
        provider: str,
        **kwargs: Any,
    ) -> "LangChainDriver":
        model = _create_chat_model(provider=provider, config=config, **kwargs)
        return cls(
            chat_model=model,
            default_temperature=config.temperature,
            default_max_tokens=config.max_tokens,
        )

    async def generate(
        self,
        *,
        system_prompt: str,
        messages: Iterable[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        prompt_sequence = _convert_messages(system_prompt, messages)
        result = await self._chat_model.apredict_messages(
            prompt_sequence,
            temperature=temperature or self._default_temperature,
            max_tokens=max_tokens or self._default_max_tokens,
        )
        return result.content


def _create_chat_model(
    *,
    provider: str,
    config: LLMConfig,
    **kwargs: Any,
) -> BaseChatModel:
    provider = provider.lower()
    try:
        if provider == "openai":
            from langchain_openai import ChatOpenAI

            return ChatOpenAI(
                model=config.model,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                **kwargs,
            )
        if provider == "anthropic":
            from langchain_anthropic import ChatAnthropic

            return ChatAnthropic(
                model=config.model,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                **kwargs,
            )
        if provider == "ollama":
            from langchain_community.chat_models import ChatOllama

            return ChatOllama(
                model=config.model,
                temperature=config.temperature,
                **kwargs,
            )
    except ImportError as exc:  # pragma: no cover - runtime guard
        raise LLMProviderError(
            f"Missing provider-specific dependency for {provider}: {exc}"
        ) from exc
    raise LLMProviderError(f"Unsupported LangChain provider: {provider}")


def _convert_messages(
    system_prompt: str, messages: Iterable[Dict[str, str]]
) -> list[Any]:
    prompt_sequence: list[Any] = [SystemMessage(content=system_prompt)]
    role_map = {"user": HumanMessage, "assistant": AIMessage}
    for message in messages:
        role = message.get("role")
        content = message.get("content", "")
        message_cls = role_map.get(role)
        if message_cls is None:
            continue
        prompt_sequence.append(message_cls(content=content))
    return prompt_sequence