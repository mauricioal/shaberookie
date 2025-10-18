"""
Profile builder that consolidates Renshuu data into a UserLanguageProfile.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Iterable, Optional

from shaberookie.common.types import (
    GrammarTerm,
    JLPTLevel,
    KanjiTerm,
    LanguageCategory,
    UserLanguageProfile,
    VocabularyTerm,
)
from shaberookie.profiling.classification_strategy import (
    BaseJLPTClassificationStrategy,
    ThresholdJLPTClassificationStrategy,
)
from shaberookie.renshuu_client.repository import RenshuuRepository


class ProfileBuilder:
    """Construct user language profiles from Renshuu data."""

    def __init__(
        self,
        repository: RenshuuRepository,
        classification_strategy: Optional[BaseJLPTClassificationStrategy] = None,
    ) -> None:
        self._repository = repository
        self._classification = classification_strategy or ThresholdJLPTClassificationStrategy()

    async def build_profile(self, user_id: str) -> UserLanguageProfile:
        """Fetch data from Renshuu and assemble a language profile."""
        base_profile = await self._repository.fetch_user_profile(user_id)
        studied_terms = await self._repository.fetch_studied_terms(user_id)

        level, confidence = self._classification.determine_level(
            base_profile.get("level_progress_percs", {})
        )
        profile = UserLanguageProfile(
            user_id=user_id,
            jlpt_level=level,
            category_progress=base_profile.get("category_progress", {}),
            studied_terms=self._normalize_terms(studied_terms),
            level_progress_percs=base_profile.get("level_progress_percs", {}),
            profile_confidence=confidence,
            last_synced=datetime.utcnow(),
        )
        return profile

    def _normalize_terms(
        self, terms: Dict[str, Iterable[object]]
    ) -> Dict[LanguageCategory, list]:
        return {
            LanguageCategory.VOCABULARY: list(
                self._sanitize_terms(terms.get("vocab", []), VocabularyTerm)
            ),
            LanguageCategory.KANJI: list(
                self._sanitize_terms(terms.get("kanji", []), KanjiTerm)
            ),
            LanguageCategory.GRAMMAR: list(
                self._sanitize_terms(terms.get("grammar", []), GrammarTerm)
            ),
        }

    @staticmethod
    def _sanitize_terms(items: Iterable[object], model) -> Iterable[object]:
        for item in items:
            if isinstance(item, model):
                yield item