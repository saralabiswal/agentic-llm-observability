"""
FastAPI route module exposing one LLMOps telemetry surface to the UI and SDK.

Author: Sarala Biswal
"""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import Settings, get_session, get_settings
from api.schemas import AlertRecord, AlertSeverity, AlertType
from audit.models import AlertHistory

router = APIRouter(prefix="/alerts", tags=["alerts"])


class AlertConfigUpdate(BaseModel):
    drift_alert_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    quality_gate_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    budget_limit_usd: float | None = Field(default=None, gt=0.0)


@router.get("/history", response_model=list[AlertRecord])
async def alert_history(
    session: Annotated[AsyncSession, Depends(get_session)],
    days: int = Query(default=30, ge=1),
    alert_type: AlertType | None = None,
    severity: AlertSeverity | None = None,
    use_case: str | None = None,
) -> list[AlertRecord]:
    statement = select(AlertHistory).where(AlertHistory.timestamp >= _since(days))
    if alert_type is not None:
        statement = statement.where(AlertHistory.alert_type == alert_type.value)
    if severity is not None:
        statement = statement.where(AlertHistory.severity == severity.value)
    if use_case is not None:
        statement = statement.where(AlertHistory.use_case == use_case)

    result = await session.execute(statement.order_by(AlertHistory.timestamp.desc()))
    return [_row_to_alert(row) for row in result.scalars().all()]


@router.post("/config")
async def update_alert_config(
    payload: AlertConfigUpdate,
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, float]:
    if payload.drift_alert_threshold is not None:
        settings.drift_alert_threshold = payload.drift_alert_threshold
    if payload.quality_gate_threshold is not None:
        settings.quality_gate_threshold = payload.quality_gate_threshold
    if payload.budget_limit_usd is not None:
        settings.budget_limit_usd = payload.budget_limit_usd
    return {
        "drift_alert_threshold": settings.drift_alert_threshold,
        "quality_gate_threshold": settings.quality_gate_threshold,
        "budget_limit_usd": settings.budget_limit_usd,
    }


def _row_to_alert(row: AlertHistory) -> AlertRecord:
    return AlertRecord(
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


def _since(days: int) -> datetime:
    return datetime.now(UTC) - timedelta(days=days)
