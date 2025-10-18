"""
Profile storage backends for shaberookie.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

import orjson

from shaberookie.common.types import UserLanguageProfile


class ProfileStore(ABC):
    """Abstraction for persisting and retrieving user language profiles."""

    @abstractmethod
    def save(self, profile: UserLanguageProfile) -> None:
        """Persist the given profile."""

    @abstractmethod
    def load(self, user_id: str) -> Optional[UserLanguageProfile]:
        """Load the profile for the specified user."""

    @abstractmethod
    def delete(self, user_id: str) -> None:
        """Remove the stored profile for the user."""


class FileProfileStore(ProfileStore):
    """File-based profile store using ORJSON serialization."""

    def __init__(self, base_path: str | Path) -> None:
        self._base_path = Path(base_path)
        self._base_path.mkdir(parents=True, exist_ok=True)

    def _profile_path(self, user_id: str) -> Path:
        safe_user_id = user_id.replace("/", "_")
        return self._base_path / f"{safe_user_id}.json"

    def save(self, profile: UserLanguageProfile) -> None:
        path = self._profile_path(profile.user_id)
        data = profile.model_dump(mode="json")
        path.write_bytes(orjson.dumps(data, option=orjson.OPT_INDENT_2))

    def load(self, user_id: str) -> Optional[UserLanguageProfile]:
        path = self._profile_path(user_id)
        if not path.exists():
            return None
        data = orjson.loads(path.read_bytes())
        return UserLanguageProfile.model_validate(data)

    def delete(self, user_id: str) -> None:
        path = self._profile_path(user_id)
        if path.exists():
            path.unlink()