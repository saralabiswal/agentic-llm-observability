"""
FastAPI route module exposing one LLMOps telemetry surface to the UI and SDK.

Author: Sarala Biswal
"""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import Settings, get_session, get_settings
from api.schemas import LatencyPercentiles
from audit.models import LLMCall
from tracking.latency_tracker import LatencyTracker, compute_percentile

router = APIRouter(prefix="/latency", tags=["latency"])


@router.get("/percentiles", response_model=list[LatencyPercentiles])
async def latency_percentiles(
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    days: int = Query(default=30, ge=1),
    use_case: str | None = None,
) -> list[LatencyPercentiles]:
    models = await _models(session, days, use_case)
    tracker = LatencyTracker(session, settings.slo_target_ms)
    return [
        await tracker.compute_percentiles(model, days, use_case=use_case)
        for model in models
    ]


@router.get("/slos")
async def latency_slos(
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    days: int = Query(default=30, ge=1),
    use_case: str | None = None,
) -> list[dict[str, str | int | float]]:
    percentiles = await latency_percentiles(session, settings, days, use_case)
    return [
        {
            "model": item.model,
            "slo_target_ms": item.slo_target_ms,
            "slo_compliance_pct": item.slo_compliance_pct,
            "breach_count_24h": item.breach_count_24h,
            "status": _slo_status(item.slo_compliance_pct),
        }
        for item in percentiles
    ]


@router.get("/timeline")
async def latency_timeline(
    session: Annotated[AsyncSession, Depends(get_session)],
    days: int = Query(default=30, ge=1),
    use_case: str | None = None,
) -> list[dict[str, str | int]]:
    filters = [LLMCall.timestamp >= _since(days)]
    if use_case:
        filters.append(LLMCall.use_case == use_case)
    result = await session.execute(
        select(func.date(LLMCall.timestamp), LLMCall.model, LLMCall.latency_ms)
        .where(*filters)
        .order_by(func.date(LLMCall.timestamp), LLMCall.model)
    )
    grouped: dict[tuple[str, str], list[int]] = {}
    for day, model, latency_ms in result.all():
        grouped.setdefault((str(day), str(model)), []).append(int(latency_ms))
    return [
        {"date": day, "model": model, "p95_ms": compute_percentile(latencies, 95)}
        for (day, model), latencies in sorted(grouped.items())
    ]


async def _models(session: AsyncSession, days: int, use_case: str | None = None) -> list[str]:
    filters = [LLMCall.timestamp >= _since(days)]
    if use_case:
        filters.append(LLMCall.use_case == use_case)
    result = await session.execute(
        select(LLMCall.model)
        .where(*filters)
        .distinct()
        .order_by(LLMCall.model)
    )
    return [str(model) for model in result.scalars().all()]


def _since(days: int) -> datetime:
    return datetime.now(UTC) - timedelta(days=days)


def _slo_status(compliance_pct: float) -> str:
    if compliance_pct < 95:
        return "critical"
    if compliance_pct < 98:
        return "warning"
    return "healthy"
