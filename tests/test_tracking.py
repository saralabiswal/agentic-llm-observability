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
from tracking.latency_tracker import LatencyTracker, compute_percentile, compute_slo_compliance
from tracking.token_tracker import TokenTracker


@pytest.fixture
async def session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


def _record(call_id: str, latency_ms: int, model: str = "gpt-4o-mini") -> LLMCallRecord:
    return LLMCallRecord(
        call_id=call_id,
        timestamp=datetime.now(UTC),
        model=model,
        provider=Provider.OPENAI,
        use_case="banking_payment_risk",
        prompt_version="v1.0",
        input_tokens=100,
        output_tokens=50,
        latency_ms=latency_ms,
        cost_usd=Decimal("0.000045"),
        quality_score=0.82,
        hallucination_flag=False,
        quality_gate_passed=True,
    )


@pytest.mark.asyncio
async def test_token_tracker_record_and_retrieve_round_trip(session_factory) -> None:
    async with session_factory() as session:
        tracker = TokenTracker(session)
        await tracker.record_call(_record("call-1", 420))

        records = await tracker.get_calls(use_case="banking_payment_risk")

    assert len(records) == 1
    assert records[0].call_id == "call-1"
    assert records[0].total_tokens == 150
    assert records[0].quality_score == 0.82


@pytest.mark.asyncio
async def test_latency_tracker_computes_percentiles_and_slo(session_factory) -> None:
    async with session_factory() as session:
        token_tracker = TokenTracker(session)
        for index, latency_ms in enumerate([100, 200, 300, 400, 2500], start=1):
            await token_tracker.record_call(_record(f"call-{index}", latency_ms))

        latency_tracker = LatencyTracker(session, default_slo_ms=1000)
        percentiles = await latency_tracker.compute_percentiles("gpt-4o-mini")

    assert percentiles.p50_ms == 300
    assert percentiles.p95_ms == 2079
    assert percentiles.p99_ms == 2416
    assert percentiles.slo_compliance_pct == 80.0
    assert percentiles.breach_count_24h == 1


def test_percentile_and_slo_helpers() -> None:
    assert compute_percentile([], 95) == 0
    assert compute_percentile([10, 20, 30, 40], 50) == 25
    assert compute_slo_compliance([], 1000) == 100.0
    assert compute_slo_compliance([500, 1500], 1000) == 50.0
    assert LatencyTracker.check_slo_breach(2001, 2000)
