"""
Prompt template management for the shaberookie LLM layer.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, Optional

from shaberookie.common.types import (
    LanguageCategory,
    UserLanguageProfile,
)
from shaberookie.config.loader import LLMConfig


DEFAULT_SYSTEM_PROMPT = """\
You are Shaberookie, a supportive Japanese conversation partner.

User JLPT level: {jlpt_level}
Confidence in classification: {confidence:.2f}

You must only use vocabulary, kanji, and grammar that the user has already studied.
The known terms are provided below. If you need to express something using vocabulary
outside of the allowed set, rephrase or ask a clarifying question. Encourage the user,
offer gentle corrections, and keep responses concise (2-3 sentences max). Include furigana
for kanji where appropriate and provide an English gloss in parentheses when clarification
is helpful.

Known vocabulary terms:
{vocab_terms}

Known kanji characters:
{kanji_terms}

Known grammar patterns:
{grammar_terms}

Conversation policy:
- If the user asks about content above their level, suggest simpler phrasing.
- Highlight at least one studied term per response.
- If you cannot comply without new vocabulary, explain the limitation and offer a simpler alternative.
"""


class PromptTemplateManager:
    """Assemble system prompts and reusable templates for the LLM."""

    def __init__(self, config: LLMConfig, prompt_path: Optional[str] = None) -> None:
        self._config = config
        self._prompt_path = prompt_path or config.system_prompt_path
        self._cached_prompt: Optional[str] = None

    def build_system_prompt(self, profile: UserLanguageProfile) -> str:
        """Generate the system prompt customized to the user's profile."""
        template = self._load_template()
        vocab_terms = self._format_terms(profile.studied_terms[LanguageCategory.VOCABULARY], "term")
        kanji_terms = self._format_terms(profile.studied_terms[LanguageCategory.KANJI], "character")
        grammar_terms = self._format_terms(profile.studied_terms[LanguageCategory.GRAMMAR], "pattern")

        return template.format(
            jlpt_level=profile.jlpt_level.value if hasattr(profile.jlpt_level, "value") else profile.jlpt_level,
            confidence=profile.profile_confidence,
            vocab_terms=vocab_terms,
            kanji_terms=kanji_terms,
            grammar_terms=grammar_terms,
        )

    def _load_template(self) -> str:
        if self._cached_prompt:
            return self._cached_prompt
        if self._prompt_path:
            path = Path(self._prompt_path)
            if path.exists():
                self._cached_prompt = path.read_text(encoding="utf-8")
                return self._cached_prompt
        self._cached_prompt = DEFAULT_SYSTEM_PROMPT
        return self._cached_prompt

    @staticmethod
    def _format_terms(terms: Iterable[object], attr: str) -> str:
        formatted = []
        for term in terms:
            value = getattr(term, attr, None)
            if value:
                formatted.append(str(value))
        if not formatted:
            return "None listed"
        return ", ".join(formatted[:100])  # limit size to avoid prompt explosion