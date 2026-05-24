"""
Regression tests that keep the API, telemetry math, and Quote-to-Cash flow behavior
honest.

Author: Sarala Biswal
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from api.dependencies import AppMode, Settings
from api.schemas import AlertType, LLMCallRecord, PromptStatus, Provider
from audit.models import AlertHistory, Base
from drift.alert_engine import AlertEngine
from drift.semantic_drift import SemanticDriftDetector
from prompts.ab_evaluator import ABEvaluator
from prompts.version_store import PromptVersionStore
from tracking.token_tracker import TokenTracker


@pytest.fixture
async def session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


def _record(
    call_id: str,
    prompt_version: str,
    quality: float,
    cost: str,
    latency_ms: int,
) -> LLMCallRecord:
    return LLMCallRecord(
        call_id=call_id,
        timestamp=datetime.now(UTC),
        model="gpt-4o-mini",
        provider=Provider.OPENAI,
        use_case="banking_payment_risk",
        prompt_version=prompt_version,
        input_tokens=100,
        output_tokens=50,
        latency_ms=latency_ms,
        cost_usd=Decimal(cost),
        quality_score=quality,
        hallucination_flag=False,
        quality_gate_passed=quality >= 0.70,
        response_text="Grounded response.",
        context_text="Grounded response.",
    )


@pytest.mark.asyncio
async def test_prompt_version_registration_and_ab_comparison(session_factory) -> None:
    async with session_factory() as session:
        store = PromptVersionStore(session)
        version_a = await store.register_version(
            "banking_payment_risk",
            "v1.0",
            "Assess risk.",
            "gpt-4o-mini",
            PromptStatus.ACTIVE,
        )
        version_b = await store.register_version(
            "banking_payment_risk",
            "v2.1",
            "Assess risk with evidence.",
            "gpt-4o-mini",
            PromptStatus.TESTING,
        )
        versions = await store.get_versions("banking_payment_risk")
        assert [version.version for version in versions] == ["v1.0", "v2.1"]

        token_tracker = TokenTracker(session)
        await token_tracker.record_call(_record("call-a", "v1.0", 0.75, "0.010000", 900))
        await token_tracker.record_call(_record("call-b", "v2.1", 0.86, "0.009000", 800))

        result = await ABEvaluator(store).compare(version_a.version_id, version_b.version_id)

    assert result.winner_version_id == version_b.version_id
    assert result.quality_delta == 0.11
    assert result.cost_delta == Decimal("-0.001000")
    assert result.latency_delta == -100


@pytest.mark.asyncio
async def test_demo_drift_score_range() -> None:
    detector = SemanticDriftDetector(settings=Settings(app_mode=AppMode.DEMO))

    score = await detector.compute_drift("renewal_agent", "gpt-4o-mini")

    assert 0.0 <= score <= 1.0
    assert score == 0.38


@pytest.mark.asyncio
async def test_alert_engine_thresholds_persist_alerts(session_factory) -> None:
    async with session_factory() as session:
        engine = AlertEngine(
            session=session,
            settings=Settings(
                app_mode=AppMode.DEMO,
                drift_alert_threshold=0.35,
                quality_gate_threshold=0.70,
            ),
        )

        alerts = await engine.check_thresholds(
            drift_score=0.42,
            use_case="renewal_agent",
            monthly_spend_pct=0.82,
            quality_score=0.61,
        )
        count = await session.scalar(select(func.count(AlertHistory.alert_id)))

    assert len(alerts) == 3
    assert {alert.alert_type for alert in alerts} == {
        AlertType.DRIFT,
        AlertType.COST,
        AlertType.QUALITY,
    }
    assert count == 3
