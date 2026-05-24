"""
Semantic drift scoring and alert generation for prompt and output behavior changes.

Author: Sarala Biswal
"""

from datetime import UTC, datetime, timedelta
from importlib import import_module

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import AppMode, Settings, get_settings
from audit.models import LLMCall


class SemanticDriftDetector:
    def __init__(
        self,
        session: AsyncSession | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.session = session
        self.settings = settings or get_settings()

    async def compute_drift(
        self,
        use_case: str,
        model: str,
        current_window_days: int = 7,
        baseline_window_days: int = 7,
        baseline_offset_days: int = 30,
    ) -> float:
        if self.settings.app_mode == AppMode.DEMO or self.session is None:
            return _demo_drift_score(use_case, model)

        current = await self._get_responses(use_case, model, current_window_days)
        baseline = await self._get_responses(
            use_case,
            model,
            baseline_window_days,
            offset_days=baseline_offset_days,
        )
        if not current or not baseline:
            return 0.0

        sentence_transformers = import_module("sentence_transformers")
        encoder = sentence_transformers.SentenceTransformer("all-MiniLM-L6-v2")
        current_embeddings = encoder.encode(current)
        baseline_embeddings = encoder.encode(baseline)
        current_mean = np.mean(current_embeddings, axis=0)
        baseline_mean = np.mean(baseline_embeddings, axis=0)
        similarity = _cosine_similarity(current_mean, baseline_mean)
        return round(float(1 - similarity), 4)

    async def _get_responses(
        self,
        use_case: str,
        model: str,
        window_days: int,
        offset_days: int = 0,
    ) -> list[str]:
        if self.session is None:
            return []
        end = datetime.now(UTC) - timedelta(days=offset_days)
        start = end - timedelta(days=window_days)
        result = await self.session.execute(
            select(LLMCall.response_text)
            .where(LLMCall.use_case == use_case)
            .where(LLMCall.model == model)
            .where(LLMCall.timestamp >= start)
            .where(LLMCall.timestamp <= end)
            .where(LLMCall.response_text.is_not(None))
        )
        return [response for response in result.scalars().all() if response]


def _demo_drift_score(use_case: str, model: str) -> float:
    if use_case == "renewal_agent":
        return 0.38
    if model == "gpt-4o":
        return 0.22
    return 0.12


def _cosine_similarity(left: np.ndarray, right: np.ndarray) -> float:
    denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
    if denominator == 0.0:
        return 1.0
    return float(np.dot(left, right) / denominator)
