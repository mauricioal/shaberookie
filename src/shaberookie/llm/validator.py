"""
Response validation utilities to enforce profile-based constraints on LLM outputs.
"""

from __future__ import annotations

import re
from typing import Iterable, Set

from shaberookie.common.exceptions import ValidationFailure
from shaberookie.common.types import LanguageCategory, UserLanguageProfile


class ResponseValidator:
    """Validate LLM responses against a user's known language profile."""

    def __init__(self, profile: UserLanguageProfile) -> None:
        self._profile = profile
        self._allowed_terms = self._build_allowed_term_set(profile)

    def ensure_compliance(self, response: str) -> str:
        """
        Verify that the response only uses known terms.

        Raises
        ------
        ValidationFailure
            If unknown terms are detected and cannot be automatically handled.
        """
        unknown_terms = self._detect_unknown_terms(response)
        if unknown_terms:
            raise ValidationFailure(
                "Response contains terms outside the user's studied list: "
                + ", ".join(sorted(unknown_terms))
            )
        return response

    def _detect_unknown_terms(self, response: str) -> Set[str]:
        tokens = _tokenize(response)
        return {token for token in tokens if token not in self._allowed_terms}

    @staticmethod
    def _build_allowed_term_set(profile: UserLanguageProfile) -> Set[str]:
        allowed: Set[str] = set()
        for category in LanguageCategory:
            terms = profile.studied_terms.get(category, [])
            allowed.update(_extract_values(terms))
        return {term.lower() for term in allowed if term}

    def update_profile(self, profile: UserLanguageProfile) -> None:
        """Refresh the validator with a new profile snapshot."""
        self._profile = profile
        self._allowed_terms = self._build_allowed_term_set(profile)


def _extract_values(terms: Iterable[object]) -> Iterable[str]:
    fields = ("term", "character", "pattern")
    for term in terms:
        for field in fields:
            value = getattr(term, field, None)
            if value:
                yield value


_TOKEN_PATTERN = re.compile(r"[一-龯ぁ-ゔァ-ヴー々〆〤\w]+")


def _tokenize(text: str) -> Set[str]:
    return {match.group(0).lower() for match in _TOKEN_PATTERN.finditer(text)}