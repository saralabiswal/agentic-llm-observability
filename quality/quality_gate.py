"""
Quality gates, hallucination checks, and judge-backed scoring for production LLM output.

Author: Sarala Biswal
"""

from api.dependencies import Settings, get_settings
from api.schemas import QualityScore


class QualityGate:
    def __init__(
        self,
        settings: Settings | None = None,
        thresholds_by_use_case: dict[str, float] | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.thresholds_by_use_case = thresholds_by_use_case or {}

    def evaluate(self, scores: QualityScore, use_case: str) -> bool:
        threshold = self.thresholds_by_use_case.get(use_case, self.settings.quality_gate_threshold)
        return scores.composite_score >= threshold
