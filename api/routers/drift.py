"""
FastAPI route module exposing one LLMOps telemetry surface to the UI and SDK.

Author: Sarala Biswal
"""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_session
from api.schemas import AlertRecord, AlertSeverity, AlertType, DriftScore
from audit.models import AlertHistory, DriftScoreRow

router = APIRouter(prefix="/drift", tags=["drift"])


@router.get("/scores", response_model=list[DriftScore])
async def drift_scores(
    session: Annotated[AsyncSession, Depends(get_session)],
    days: int = Query(default=30, ge=1),
    use_case: str | None = None,
) -> list[DriftScore]:
    filters = [DriftScoreRow.timestamp >= _since(days)]
    if use_case:
        filters.append(DriftScoreRow.use_case == use_case)
    result = await session.execute(
        select(DriftScoreRow)
        .where(*filters)
        .order_by(DriftScoreRow.timestamp)
    )
    return [
        DriftScore(
            use_case=row.use_case,
            model=row.model,
            timestamp=row.timestamp,
            drift_score=float(row.drift_score),
            baseline_similarity=float(row.baseline_similarity),
            alert_triggered=row.alert_triggered,
        )
        for row in result.scalars().all()
    ]


@router.get("/alerts", response_model=list[AlertRecord])
async def drift_alerts(
    session: Annotated[AsyncSession, Depends(get_session)],
    days: int = Query(default=30, ge=1),
    use_case: str | None = None,
) -> list[AlertRecord]:
    filters = [
        AlertHistory.timestamp >= _since(days),
        AlertHistory.alert_type == AlertType.DRIFT.value,
    ]
    if use_case:
        filters.append(AlertHistory.use_case == use_case)
    result = await session.execute(
        select(AlertHistory)
        .where(*filters)
        .order_by(AlertHistory.timestamp.desc())
    )
    return [
        AlertRecord(
            alert_id=row.alert_id,
            timestamp=row.timestamp,
            alert_type=AlertType(row.alert_type),
            severity=AlertSeverity(row.severity),
            use_case=row.use_case,
            message=row.message,
            metric_value=float(row.metric_value) if row.metric_value is not None else None,
            threshold_value=float(row.threshold_value) if row.threshold_value is not None else None,
            resolved=row.resolved,
        )
        for row in result.scalars().all()
    ]


def _since(days: int) -> datetime:
    return datetime.now(UTC) - timedelta(days=days)
