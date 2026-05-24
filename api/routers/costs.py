"""
FastAPI route module exposing one LLMOps telemetry surface to the UI and SDK.

Author: Sarala Biswal
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import Settings, get_session, get_settings
from api.schemas import CostSummary, OptimizationRecommendation
from audit.models import LLMCall
from costs.optimizer import CostOptimizer

router = APIRouter(prefix="/costs", tags=["costs"])


@router.get("/summary", response_model=CostSummary)
async def cost_summary(
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    days: int = Query(default=30, ge=1),
    use_case: str | None = None,
) -> CostSummary:
    since = _since(days)
    filters = _filters(since, use_case)
    total_cost, total_calls = (
        await session.execute(
            select(func.coalesce(func.sum(LLMCall.cost_usd), 0), func.count(LLMCall.call_id))
            .where(*filters)
        )
    ).one()
    by_model = await _group_costs(session, LLMCall.model, since, use_case)
    by_usecase = await _group_costs(session, LLMCall.use_case, since, use_case)
    total_cost_decimal = Decimal(total_cost or 0)
    projected = total_cost_decimal * Decimal(30) / Decimal(days)
    return CostSummary(
        total_cost_usd=total_cost_decimal,
        total_calls=int(total_calls or 0),
        avg_cost_per_call=(
            total_cost_decimal / Decimal(total_calls) if total_calls else Decimal("0.000000")
        ).quantize(Decimal("0.000001")),
        cost_by_model=by_model,
        cost_by_usecase=by_usecase,
        top_cost_driver=max(by_usecase, key=lambda name: by_usecase[name]) if by_usecase else "",
        projected_monthly_usd=projected.quantize(Decimal("0.000001")),
        budget_burn_rate_pct=round(
            float(projected / Decimal(str(settings.budget_limit_usd)) * 100),
            2,
        ),
    )


@router.get("/by-model")
async def cost_by_model(
    session: Annotated[AsyncSession, Depends(get_session)],
    days: int = Query(default=30, ge=1),
    use_case: str | None = None,
) -> list[dict[str, str | int | Decimal]]:
    since = _since(days)
    filters = _filters(since, use_case)
    result = await session.execute(
        select(
            LLMCall.model,
            LLMCall.provider,
            func.sum(LLMCall.cost_usd),
            func.count(LLMCall.call_id),
            func.avg(LLMCall.cost_usd),
        )
        .where(*filters)
        .group_by(LLMCall.model, LLMCall.provider)
        .order_by(func.sum(LLMCall.cost_usd).desc())
    )
    return [
        {
            "model": model,
            "provider": provider,
            "total_cost": Decimal(total_cost or 0).quantize(Decimal("0.000001")),
            "call_count": int(call_count),
            "avg_cost": Decimal(avg_cost or 0).quantize(Decimal("0.000001")),
        }
        for model, provider, total_cost, call_count, avg_cost in result.all()
    ]


@router.get("/by-usecase")
async def cost_by_usecase(
    session: Annotated[AsyncSession, Depends(get_session)],
    days: int = Query(default=30, ge=1),
) -> list[dict[str, str | int | Decimal]]:
    since = _since(days)
    result = await session.execute(
        select(LLMCall.use_case, func.sum(LLMCall.cost_usd), func.count(LLMCall.call_id))
        .where(LLMCall.timestamp >= since)
        .group_by(LLMCall.use_case)
        .order_by(func.sum(LLMCall.cost_usd).desc())
    )
    return [
        {
            "use_case": use_case,
            "total_cost": Decimal(total_cost or 0).quantize(Decimal("0.000001")),
            "call_count": int(call_count),
        }
        for use_case, total_cost, call_count in result.all()
    ]


@router.get("/timeline")
async def cost_timeline(
    session: Annotated[AsyncSession, Depends(get_session)],
    days: int = Query(default=30, ge=1),
    use_case: str | None = None,
) -> list[dict[str, str | Decimal]]:
    since = _since(days)
    filters = _filters(since, use_case)
    result = await session.execute(
        select(func.date(LLMCall.timestamp), func.sum(LLMCall.cost_usd))
        .where(*filters)
        .group_by(func.date(LLMCall.timestamp))
        .order_by(func.date(LLMCall.timestamp))
    )
    return [
        {"date": str(day), "total_cost": Decimal(total_cost or 0).quantize(Decimal("0.000001"))}
        for day, total_cost in result.all()
    ]


@router.get("/optimize", response_model=list[OptimizationRecommendation])
async def optimize_costs(
    session: Annotated[AsyncSession, Depends(get_session)],
    use_case: str = "banking_payment_risk",
    days: int = Query(default=30, ge=1),
    target_model: str | None = Query(default=None),
) -> list[OptimizationRecommendation]:
    return await CostOptimizer(session).generate_recommendations(use_case, days, target_model)


def _since(days: int) -> datetime:
    return datetime.now(UTC) - timedelta(days=days)


async def _group_costs(
    session: AsyncSession,
    column: Any,
    since: datetime,
    use_case: str | None = None,
) -> dict[str, Decimal]:
    filters = _filters(since, use_case)
    result = await session.execute(
        select(column, func.sum(LLMCall.cost_usd))
        .where(*filters)
        .group_by(column)
        .order_by(func.sum(LLMCall.cost_usd).desc())
    )
    return {
        str(name): Decimal(total or 0).quantize(Decimal("0.000001"))
        for name, total in result.all()
    }


def _filters(since: datetime, use_case: str | None) -> list[Any]:
    filters: list[Any] = [LLMCall.timestamp >= since]
    if use_case:
        filters.append(LLMCall.use_case == use_case)
    return filters
