"""
FastAPI route module exposing one LLMOps telemetry surface to the UI and SDK.

Author: Sarala Biswal
"""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_session
from api.schemas import QualityScore
from audit.models import LLMCall, QualityScoreRow

router = APIRouter(prefix="/quality", tags=["quality"])


@router.get("/scores", response_model=list[QualityScore])
async def quality_scores(
    session: Annotated[AsyncSession, Depends(get_session)],
    days: int = Query(default=30, ge=1),
    use_case: str | None = None,
) -> list[QualityScore]:
    filters = [QualityScoreRow.timestamp >= _since(days)]
    if use_case:
        filters.append(QualityScoreRow.use_case == use_case)
    result = await session.execute(
        select(QualityScoreRow)
        .where(*filters)
        .order_by(QualityScoreRow.timestamp)
    )
    return [
        QualityScore(
            use_case=row.use_case,
            model=row.model,
            timestamp=row.timestamp,
            faithfulness=float(row.faithfulness),
            relevance=float(row.relevance),
            coherence=float(row.coherence),
            gate_passed=row.gate_passed,
        )
        for row in result.scalars().all()
    ]


@router.get("/hallucinations")
async def hallucinations(
    session: Annotated[AsyncSession, Depends(get_session)],
    days: int = Query(default=30, ge=1),
    use_case: str | None = None,
) -> list[dict[str, str | int | float]]:
    filters = [LLMCall.timestamp >= _since(days)]
    if use_case:
        filters.append(LLMCall.use_case == use_case)
    result = await session.execute(
        select(
            LLMCall.model,
            LLMCall.use_case,
            func.count(LLMCall.call_id),
            func.sum(case((LLMCall.hallucination_flag.is_(True), 1), else_=0)),
        )
        .where(*filters)
        .group_by(LLMCall.model, LLMCall.use_case)
    )
    rows = []
    for model, use_case, total, flagged in result.all():
        total_int = int(total or 0)
        flagged_int = int(flagged or 0)
        rows.append(
            {
                "model": model,
                "use_case": use_case,
                "call_count": total_int,
                "flagged_count": flagged_int,
                "hallucination_rate": round(flagged_int / total_int * 100, 2) if total_int else 0.0,
            }
        )
    return rows


@router.get("/gate-results")
async def gate_results(
    session: Annotated[AsyncSession, Depends(get_session)],
    days: int = Query(default=30, ge=1),
    use_case: str | None = None,
) -> list[dict[str, str | int]]:
    filters = [LLMCall.timestamp >= _since(days)]
    if use_case:
        filters.append(LLMCall.use_case == use_case)
    result = await session.execute(
        select(
            LLMCall.use_case,
            func.sum(case((LLMCall.quality_gate_passed.is_(True), 1), else_=0)),
            func.sum(case((LLMCall.quality_gate_passed.is_(False), 1), else_=0)),
        )
        .where(*filters)
        .group_by(LLMCall.use_case)
    )
    return [
        {
            "use_case": use_case,
            "passed": int(passed or 0),
            "failed": int(failed or 0),
        }
        for use_case, passed, failed in result.all()
    ]


def _since(days: int) -> datetime:
    return datetime.now(UTC) - timedelta(days=days)
