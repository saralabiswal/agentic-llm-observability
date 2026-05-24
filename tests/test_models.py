"""
Regression tests that keep the API, telemetry math, and Quote-to-Cash flow behavior
honest.

Author: Sarala Biswal
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine

from api.schemas import (
    AlertRecord,
    AlertSeverity,
    AlertType,
    CostSummary,
    DriftScore,
    LatencyPercentiles,
    LLMCallRecord,
    OptimizationRecommendation,
    PromptStatus,
    PromptVersion,
    Provider,
    QualityScore,
)
from audit.models import Base


def test_pydantic_models_instantiate() -> None:
    call = LLMCallRecord(
        call_id="call-1",
        timestamp=datetime.now(UTC),
        model="gpt-4o-mini",
        provider=Provider.OPENAI,
        use_case="banking_payment_risk",
        prompt_version="v1.0",
        input_tokens=100,
        output_tokens=50,
        latency_ms=420,
        cost_usd=Decimal("0.000045"),
    )
    assert call.total_tokens == 150

    summary = CostSummary(
        total_cost_usd=Decimal("12.50"),
        total_calls=100,
        avg_cost_per_call=Decimal("0.125000"),
        cost_by_model={"gpt-4o-mini": Decimal("9.00")},
        cost_by_usecase={"banking_payment_risk": Decimal("9.00")},
        top_cost_driver="banking_payment_risk",
        projected_monthly_usd=Decimal("25.00"),
        budget_burn_rate_pct=5.0,
    )
    assert summary.total_calls == 100

    recommendation = OptimizationRecommendation(
        use_case="banking_payment_risk",
        current_model="gpt-4o",
        current_cost_usd=Decimal("20.00"),
        recommended_model="gpt-4o-mini",
        recommended_cost_usd=Decimal("3.00"),
        quality_delta_pct=-3.2,
        cost_savings_pct=85.0,
        monthly_savings_usd=Decimal("17.00"),
        rationale="Lower cost with acceptable quality delta.",
    )
    assert recommendation.monthly_savings_usd == Decimal("17.00")

    latency = LatencyPercentiles(
        model="gpt-4o-mini",
        p50_ms=300,
        p95_ms=900,
        p99_ms=1200,
        slo_target_ms=2000,
        slo_compliance_pct=99.0,
        breach_count_24h=1,
    )
    assert latency.p95_ms == 900

    quality = QualityScore(
        use_case="banking_payment_risk",
        model="gpt-4o-mini",
        faithfulness=0.9,
        relevance=0.8,
        coherence=0.7,
        gate_passed=True,
    )
    assert quality.composite_score == 0.825

    drift = DriftScore(
        use_case="banking_payment_risk",
        model="gpt-4o-mini",
        drift_score=0.12,
        baseline_similarity=0.88,
        alert_triggered=False,
    )
    assert not drift.alert_triggered

    prompt = PromptVersion(
        version_id="prompt-1",
        use_case="banking_payment_risk",
        version="v1.0",
        prompt_text="Assess payment risk.",
        model="gpt-4o-mini",
        status=PromptStatus.ACTIVE,
    )
    assert prompt.status == PromptStatus.ACTIVE

    alert = AlertRecord(
        alert_id="alert-1",
        alert_type=AlertType.QUALITY,
        severity=AlertSeverity.HIGH,
        use_case="banking_payment_risk",
        message="Quality below threshold.",
    )
    assert alert.severity == AlertSeverity.HIGH


@pytest.mark.asyncio
async def test_db_tables_created() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        table_names = await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())

    assert set(table_names) == {
        "alert_history",
        "cost_snapshots",
        "drift_scores",
        "llm_calls",
        "prompt_versions",
        "quality_scores",
    }
    await engine.dispose()
