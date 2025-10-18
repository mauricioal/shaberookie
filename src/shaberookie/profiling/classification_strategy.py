"""
Strategies for classifying users into JLPT levels based on Renshuu progress data.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Iterable, Tuple

from shaberookie.common.types import JLPTLevel


class BaseJLPTClassificationStrategy(ABC):
    """Interface for JLPT classification strategies."""

    @abstractmethod
    def determine_level(self, level_progress: Dict[str, float]) -> Tuple[JLPTLevel, float]:
        """
        Compute the JLPT level and an associated confidence score.

        Returns
        -------
        tuple
            A `(jlpt_level, confidence)` tuple where confidence is 0.0–1.0.
        """


class ThresholdJLPTClassificationStrategy(BaseJLPTClassificationStrategy):
    """
    Classify JLPT level based on configured progress thresholds.

    The strategy computes weighted averages across categories and selects the highest
    level whose threshold is satisfied. Confidence is derived from the ratio between the
    user's progress and the threshold for the chosen level.
    """

    def __init__(
        self,
        thresholds: Dict[JLPTLevel, float] | None = None,
        category_weights: Dict[str, float] | None = None,
    ) -> None:
        self._thresholds = thresholds or {
            JLPTLevel.N5: 0.2,
            JLPTLevel.N4: 0.45,
            JLPTLevel.N3: 0.6,
            JLPTLevel.N2: 0.75,
            JLPTLevel.N1: 0.9,
        }
        weights = category_weights or {"vocab": 0.4, "kanji": 0.3, "grammar": 0.3}
        normalization_factor = sum(weights.values()) or 1.0
        self._weights = {k: v / normalization_factor for k, v in weights.items()}

    def determine_level(self, level_progress: Dict[str, float]) -> Tuple[JLPTLevel, float]:
        weighted_score = self._compute_weighted_score(level_progress)
        selected_level = JLPTLevel.N5
        for level, threshold in sorted(
            self._thresholds.items(), key=lambda item: item[1]
        ):
            if weighted_score >= threshold:
                selected_level = level
        threshold_value = self._thresholds.get(selected_level, 1.0)
        confidence = min(weighted_score / threshold_value if threshold_value else 1.0, 1.0)
        return selected_level, max(confidence, 0.05)

    def _compute_weighted_score(self, level_progress: Dict[str, float]) -> float:
        score = 0.0
        for category, weight in self._weights.items():
            score += weight * (level_progress.get(category, 0.0) / 100.0)
        return score