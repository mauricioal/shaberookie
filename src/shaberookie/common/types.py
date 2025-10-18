"""Shared type definitions and data models for shaberookie."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class JLPTLevel(str, Enum):
    """Enumeration of JLPT proficiency levels."""

    N5 = "N5"
    N4 = "N4"
    N3 = "N3"
    N2 = "N2"
    N1 = "N1"


class LanguageCategory(str, Enum):
    """Supported study categories."""

    VOCABULARY = "vocab"
    KANJI = "kanji"
    GRAMMAR = "grammar"


class VocabularyTerm(BaseModel):
    term_id: str = Field(..., alias="id")
    term: str
    meaning: str
    reading: Optional[str] = None
    source_schedule_id: Optional[str] = Field(default=None)
    tags: List[str] = Field(default_factory=list)

    class Config:
        allow_population_by_field_name = True


class KanjiTerm(BaseModel):
    character: str = Field(..., alias="kanji")
    meanings: List[str]
    onyomi: Optional[List[str]] = None
    kunyomi: Optional[List[str]] = None
    grade: Optional[int] = None
    source_schedule_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    class Config:
        allow_population_by_field_name = True


class GrammarTerm(BaseModel):
    term_id: str = Field(..., alias="id")
    pattern: str
    explanation: str
    example_sentences: List[str] = Field(default_factory=list)
    source_schedule_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    class Config:
        allow_population_by_field_name = True


class ConversationRole(str, Enum):
    """Conversation participant roles."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ConversationMessage(BaseModel):
    role: ConversationRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class UserLanguageProfile(BaseModel):
    user_id: str
    jlpt_level: JLPTLevel
    category_progress: Dict[LanguageCategory, float] = Field(
        default_factory=lambda: {
            LanguageCategory.GRAMMAR: 0.0,
            LanguageCategory.KANJI: 0.0,
            LanguageCategory.VOCABULARY: 0.0,
        }
    )
    studied_terms: Dict[LanguageCategory, List[BaseModel]] = Field(
        default_factory=lambda: {
            LanguageCategory.GRAMMAR: [],
            LanguageCategory.KANJI: [],
            LanguageCategory.VOCABULARY: [],
        }
    )
    level_progress_percs: Dict[str, float] = Field(default_factory=dict)
    profile_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    last_synced: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True