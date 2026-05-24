"""
Token and latency helpers that normalize per-call observability measurements.

Author: Sarala Biswal
"""

import math
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import LatencyPercentiles
from audit.models import LLMCall


class LatencyTracker:
    def __init__(self, session: AsyncSession, default_slo_ms: int = 2000) -> None:
        self.session = session
        self.default_slo_ms = default_slo_ms

    async def compute_percentiles(
        self,
        model: str,
        days: int = 30,
        slo_ms: int | None = None,
        use_case: str | None = None,
    ) -> LatencyPercentiles:
        target_slo = slo_ms if slo_ms is not None else self.default_slo_ms
        since = datetime.now(UTC) - timedelta(days=days)
        filters = [LLMCall.model == model, LLMCall.timestamp >= since]
        if use_case:
            filters.append(LLMCall.use_case == use_case)
        result = await self.session.execute(
            select(LLMCall.latency_ms)
            .where(*filters)
        )
        latencies = list(result.scalars().all())
        breach_count = sum(1 for latency in latencies if self.check_slo_breach(latency, target_slo))
        return LatencyPercentiles(
            model=model,
            p50_ms=compute_percentile(latencies, 50),
            p95_ms=compute_percentile(latencies, 95),
            p99_ms=compute_percentile(latencies, 99),
            slo_target_ms=target_slo,
            slo_compliance_pct=compute_slo_compliance(latencies, target_slo),
            breach_count_24h=breach_count,
        )

    @staticmethod
    def check_slo_breach(latency_ms: int, slo_ms: int = 2000) -> bool:
        return latency_ms > slo_ms


def compute_percentile(values: list[int], pct: float) -> int:
    if not values:
        return 0
    sorted_values = sorted(values)
    index = (len(sorted_values) - 1) * pct / 100
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return sorted_values[lower]
    weighted = sorted_values[lower] + (
        sorted_values[upper] - sorted_values[lower]
    ) * (index - lower)
    return int(weighted)


def compute_slo_compliance(latencies: list[int], slo_ms: int) -> float:
    if not latencies:
        return 100.0
    compliant = sum(1 for latency in latencies if latency <= slo_ms)
    return round(compliant / len(latencies) * 100, 2)
