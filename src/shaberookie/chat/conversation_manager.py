"""
Conversation coordination logic shared by CLI and Gradio interfaces.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, List, Optional

from shaberookie.common import ConversationMessage, ConversationRole, UserLanguageProfile
from shaberookie.llm import LLMAdapter, PromptTemplateManager, ResponseValidator


@dataclass
class ConversationSession:
    """In-memory session state for a single chat."""

    user_id: str
    profile: UserLanguageProfile
    messages: List[ConversationMessage] = field(default_factory=list)

    def append(self, role: ConversationRole, content: str) -> None:
        self.messages.append(
            ConversationMessage(role=role, content=content, timestamp=datetime.utcnow())
        )


class ConversationManager:
    """
    Facade orchestrating prompt generation, LLM calls, and response validation.
    """

    def __init__(
        self,
        adapter: LLMAdapter,
        prompt_manager: PromptTemplateManager,
        *,
        on_message: Optional[Callable[[ConversationMessage], None]] = None,
    ) -> None:
        self._adapter = adapter
        self._prompt_manager = prompt_manager
        self._on_message = on_message

    async def send_user_message(
        self,
        session: ConversationSession,
        content: str,
    ) -> ConversationMessage:
        """Process a user message and return the assistant response."""
        session.append(ConversationRole.USER, content)

        validator = ResponseValidator(session.profile)
        system_prompt = self._prompt_manager.build_system_prompt(session.profile)
        response_text = await self._adapter.generate_response(
            system_prompt=system_prompt,
            messages=[message.dict() for message in session.messages],
        )
        validator.ensure_compliance(response_text)

        assistant_message = ConversationMessage(
            role=ConversationRole.ASSISTANT,
            content=response_text,
            timestamp=datetime.utcnow(),
        )
        session.messages.append(assistant_message)
        if self._on_message:
            self._on_message(assistant_message)
        return assistant_message

    def start_session(self, profile: UserLanguageProfile) -> ConversationSession:
        """Create a new conversation session pre-populated with the system prompt."""
        session = ConversationSession(user_id=profile.user_id, profile=profile)
        system_prompt = self._prompt_manager.build_system_prompt(profile)
        session.append(ConversationRole.SYSTEM, system_prompt)
        if self._on_message:
            self._on_message(session.messages[-1])
        return session