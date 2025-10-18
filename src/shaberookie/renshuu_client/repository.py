"""
Repository layer that orchestrates data retrieval from the Renshuu API.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from shaberookie.common.exceptions import ProfileNotFoundError
from shaberookie.common.types import GrammarTerm, KanjiTerm, VocabularyTerm
from shaberookie.renshuu_client.client import RenshuuApiClient
from shaberookie.renshuu_client.mapper import RenshuuSchemaMapper


class RenshuuRepository:
    """Facade combining API access and schema mapping."""

    def __init__(
        self,
        client: RenshuuApiClient,
        mapper: Optional[RenshuuSchemaMapper] = None,
    ) -> None:
        self._client = client
        self._mapper = mapper or RenshuuSchemaMapper()

    async def fetch_user_profile(self, user_id: str) -> Dict[str, object]:
        payload = await self._client.get_user_profile(user_id)
        if not payload:
            raise ProfileNotFoundError(f"User profile not found for user_id={user_id}")
        return self._mapper.map_profile(user_id, payload)

    async def fetch_user_terms(
        self,
        user_id: str,
        *,
        category: str,
        status_filter: Optional[str] = "studied",
    ) -> List[dict]:
        response = await self._client.list_terms(
            user_id, category=category, status_filter=status_filter
        )
        return response.get("terms", [])

    async def fetch_studied_terms(
        self, user_id: str
    ) -> Dict[str, List[object]]:
        vocab_raw = await self.fetch_user_terms(user_id, category="vocab")
        kanji_raw = await self.fetch_user_terms(user_id, category="kanji")
        grammar_raw = await self.fetch_user_terms(user_id, category="grammar")

        vocab_terms: List[VocabularyTerm] = self._mapper.map_vocabulary_terms(vocab_raw)
        kanji_terms: List[KanjiTerm] = self._mapper.map_kanji_terms(kanji_raw)
        grammar_terms: List[GrammarTerm] = self._mapper.map_grammar_terms(grammar_raw)

        return {
            "vocab": vocab_terms,
            "kanji": kanji_terms,
            "grammar": grammar_terms,
        }

    async def close(self) -> None:
        await self._client.close()