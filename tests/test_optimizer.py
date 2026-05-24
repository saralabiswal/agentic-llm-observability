"""
Regression tests that keep the API, telemetry math, and Quote-to-Cash flow behavior
honest.

Author: Sarala Biswal
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from api.schemas import LLMCallRecord, Provider
from audit.models import Base
from costs.optimizer import CostOptimizer
from tracking.token_tracker import TokenTracker


@pytest.fixture
async def session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


def _record(call_id: str) -> LLMCallRecord:
    return LLMCallRecord(
        call_id=call_id,
        timestamp=datetime.now(UTC),
        model="gpt-4o",
        provider=Provider.OPENAI,
        use_case="banking_payment_risk",
        prompt_version="v1.0",
        input_tokens=1_000_000,
        output_tokens=1_000_000,
        latency_ms=1200,
        cost_usd=Decimal("12.500000"),
        quality_score=0.90,
        hallucination_flag=False,
        quality_gate_passed=True,
    )


@pytest.mark.asyncio
async def test_optimizer_recommendations_sorted_by_savings(session_factory) -> None:
    async with session_factory() as session:
        tracker = TokenTracker(session)
        await tracker.record_call(_record("call-1"))

        recommendations = await CostOptimizer(session).generate_recommendations(
            "banking_payment_risk",
            days=30,
        )

    assert [item.monthly_savings_usd for item in recommendations] == sorted(
        [item.monthly_savings_usd for item in recommendations],
        reverse=True,
    )
    assert recommendations[0].recommended_model == "gpt-4o-mini"
    assert recommendations[0].quality_delta_pct == -3.2


@pytest.mark.asyncio
async def test_optimizer_quality_floor_enforced(session_factory) -> None:
    async with session_factory() as session:
        tracker = TokenTracker(session)
        await tracker.record_call(_record("call-1"))

        recommendations = await CostOptimizer(session).generate_recommendations(
            "banking_payment_risk",
            days=30,
        )

    recommended_models = {item.recommended_model for item in recommendations}
    assert "gpt-4.1-mini" not in recommended_models
    assert all(item.quality_delta_pct >= -5.0 for item in recommendations)


@pytest.mark.asyncio
async def test_optimizer_returns_selected_local_model_first_with_other_local_options(
    session_factory,
) -> None:
    async with session_factory() as session:
        tracker = TokenTracker(session)
        await tracker.record_call(_record("call-1"))

        recommendations = await CostOptimizer(session).generate_recommendations(
            "banking_payment_risk",
            days=30,
            target_model="qwen2.5:7b",
        )

    assert recommendations[0].recommended_model == "qwen2.5:7b"
    assert recommendations[0].current_model == "gpt-4o"
    assert recommendations[0].monthly_savings_usd > 0
    assert recommendations[0].recommended_cost_usd < recommendations[0].current_cost_usd
    assert {"llama3.2", "mistral"}.issubset({item.recommended_model for item in recommendations})
