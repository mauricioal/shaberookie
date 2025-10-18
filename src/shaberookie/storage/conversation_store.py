"""
Conversation log storage backends for shaberookie.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

import orjson

from shaberookie.common.types import ConversationMessage, ConversationRole


class ConversationLogStore(ABC):
    """Abstract interface for storing conversation transcripts."""

    @abstractmethod
    def append(self, user_id: str, message: ConversationMessage) -> None:
        """Append a conversation message for the user."""

    @abstractmethod
    def load(self, user_id: str) -> Iterable[ConversationMessage]:
        """Load the conversation history for the user."""

    @abstractmethod
    def clear(self, user_id: str) -> None:
        """Remove conversation history for the user."""


class FileConversationLogStore(ConversationLogStore):
    """File-based conversation log store with ORJSON serialization."""

    def __init__(self, base_path: str | Path) -> None:
        self._base_path = Path(base_path)
        self._base_path.mkdir(parents=True, exist_ok=True)

    def _log_path(self, user_id: str) -> Path:
        safe_user_id = user_id.replace("/", "_")
        return self._base_path / f"{safe_user_id}.jsonl"

    def append(self, user_id: str, message: ConversationMessage) -> None:
        path = self._log_path(user_id)
        record = {
            "role": message.role.value if isinstance(message.role, ConversationRole) else message.role,
            "content": message.content,
            "timestamp": message.timestamp.isoformat(),
        }
        with path.open("a", encoding="utf-8") as handle:
            handle.write(orjson.dumps(record).decode("utf-8"))
            handle.write("\n")

    def load(self, user_id: str) -> Iterable[ConversationMessage]:
        path = self._log_path(user_id)
        if not path.exists():
            return []
        messages = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                data = orjson.loads(line)
                messages.append(
                    ConversationMessage(
                        role=ConversationRole(data["role"]),
                        content=data["content"],
                        timestamp=datetime.fromisoformat(data["timestamp"]),
                    )
                )
        return messages

    def clear(self, user_id: str) -> None:
        path = self._log_path(user_id)
        if path.exists():
            path.unlink()