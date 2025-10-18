"""
Schema mapping utilities for transforming Renshuu API payloads into internal models.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Sequence

from pydantic import ValidationError

from shaberookie.common import (
    GrammarTerm,
    KanjiTerm,
    LanguageCategory,
    UserLanguageProfile,
    VocabularyTerm,
)


class RenshuuSchemaMapper:
    """Convert Renshuu JSON payloads into shaberookie data models."""

    @staticmethod
    def map_profile(user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        profile_data = payload.get("profile", {})
        progress = profile_data.get("level_progress_percs", {})
        return {
            "user_id": user_id,
            "level_progress_percs": progress,
            "category_progress": {
                LanguageCategory.VOCABULARY: float(progress.get("vocab", 0.0)),
                LanguageCategory.KANJI: float(progress.get("kanji", 0.0)),
                LanguageCategory.GRAMMAR: float(progress.get("grammar", 0.0)),
            },
        }

    @staticmethod
    def map_vocabulary_terms(items: Sequence[Dict[str, Any]]) -> List[VocabularyTerm]:
        return _safe_parse(VocabularyTerm, items)

    @staticmethod
    def map_kanji_terms(items: Sequence[Dict[str, Any]]) -> List[KanjiTerm]:
        return _safe_parse(KanjiTerm, items)

    @staticmethod
    def map_grammar_terms(items: Sequence[Dict[str, Any]]) -> List[GrammarTerm]:
        return _safe_parse(GrammarTerm, items)

    @staticmethod
    def build_user_language_profile(
        base_profile: Dict[str, Any],
        vocab_terms: Iterable[VocabularyTerm],
        kanji_terms: Iterable[KanjiTerm],
        grammar_terms: Iterable[GrammarTerm],
        *,
        jlpt_level: str,
        profile_confidence: float,
    ) -> UserLanguageProfile:
        studied_terms = {
            LanguageCategory.VOCABULARY: list(vocab_terms),
            LanguageCategory.KANJI: list(kanji_terms),
            LanguageCategory.GRAMMAR: list(grammar_terms),
        }
        return UserLanguageProfile(
            user_id=base_profile["user_id"],
            jlpt_level=jlpt_level,
            category_progress=base_profile["category_progress"],
            studied_terms=studied_terms,
            level_progress_percs=base_profile["level_progress_percs"],
            profile_confidence=profile_confidence,
        )


def _safe_parse(model, items: Sequence[Dict[str, Any]]):
    parsed = []
    for item in items:
        try:
            parsed.append(model.model_validate(item))
        except ValidationError:
            continue
    return parsed