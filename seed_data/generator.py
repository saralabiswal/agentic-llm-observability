"""
Deterministic seed data generator that makes dashboards useful on a fresh local
database.

Author: Sarala Biswal
"""

import asyncio
import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import delete

from api.dependencies import get_engine, get_sessionmaker
from api.schemas import Provider
from audit.models import (
    AlertHistory,
    Base,
    DriftScoreRow,
    LLMCall,
    PromptVersionRow,
    QualityScoreRow,
)
from costs.cost_calculator import CostCalculator

USE_CASES = [
    "banking_payment_risk",
    "renewal_agent",
    "quote_generation",
    "cdp_churn_prediction",
    "hr_onboarding",
]

MODEL_MIX = [
    ("gpt-4o-mini", Provider.OPENAI, 0.60),
    ("claude-3-5-haiku-20241022", Provider.ANTHROPIC, 0.30),
    ("gpt-4o", Provider.OPENAI, 0.10),
]


async def main() -> None:
    random.seed(42)
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        for table in [AlertHistory, DriftScoreRow, QualityScoreRow, LLMCall, PromptVersionRow]:
            await session.execute(delete(table))

        for use_case in USE_CASES:
            session.add_all(_prompt_versions(use_case))

        calculator = CostCalculator()
        today = datetime.now(UTC).replace(hour=12, minute=0, second=0, microsecond=0)
        for day_index in range(30):
            timestamp = today - timedelta(days=29 - day_index)
            for use_case in USE_CASES:
                model, provider = _pick_model(day_index, use_case)
                prompt_version = "v1.0" if day_index < 14 else "v2.1"
                for call_number in range(20):
                    input_tokens = random.randint(700, 2200)
                    output_tokens = random.randint(120, 900)
                    latency_ms = _latency_for_model(model)
                    cost_usd = calculator.calculate_call_cost(
                        model,
                        provider,
                        input_tokens,
                        output_tokens,
                    )
                    quality_score = _quality_for_day(day_index, prompt_version)
                    hallucination_flag = quality_score < 0.70 and call_number % 7 == 0
                    session.add(
                        LLMCall(
                            call_id=str(uuid4()),
                            timestamp=timestamp + timedelta(minutes=call_number),
                            model=model,
                            provider=provider.value,
                            use_case=use_case,
                            prompt_version=prompt_version,
                            input_tokens=input_tokens,
                            output_tokens=output_tokens,
                            total_tokens=input_tokens + output_tokens,
                            latency_ms=latency_ms,
                            cost_usd=cost_usd,
                            quality_score=quality_score,
                            hallucination_flag=hallucination_flag,
                            quality_gate_passed=quality_score >= 0.70,
                            response_text=f"{use_case} grounded response day {day_index}",
                            context_text=f"{use_case} grounded response day {day_index}",
                        )
                    )

                composite = _quality_for_day(day_index, prompt_version)
                session.add(
                    QualityScoreRow(
                        timestamp=timestamp,
                        use_case=use_case,
                        model=model,
                        faithfulness=max(composite - 0.02, 0),
                        relevance=composite,
                        coherence=min(composite + 0.02, 1),
                        composite_score=composite,
                        gate_passed=composite >= 0.70,
                    )
                )

                drift_score = _drift_for_day(day_index, use_case)
                session.add(
                    DriftScoreRow(
                        timestamp=timestamp,
                        use_case=use_case,
                        model=model,
                        drift_score=drift_score,
                        baseline_similarity=1 - drift_score,
                        alert_triggered=drift_score > 0.35,
                    )
                )

        await session.commit()

    print("Seeded 30 days of LLM observability data for 5 use cases.")


def _prompt_versions(use_case: str) -> list[PromptVersionRow]:
    now = datetime.now(UTC)
    return [
        PromptVersionRow(
            version_id=str(uuid4()),
            use_case=use_case,
            version="v1.0",
            prompt_text=f"Baseline prompt for {use_case}.",
            model="gpt-4o-mini",
            status="deprecated",
            deployed_at=now - timedelta(days=30),
            created_at=now - timedelta(days=30),
            avg_quality_score=Decimal("0.78"),
            avg_cost_usd=Decimal("0.002000"),
            avg_latency_ms=1100,
        ),
        PromptVersionRow(
            version_id=str(uuid4()),
            use_case=use_case,
            version="v2.1",
            prompt_text=f"Evidence-grounded prompt for {use_case}.",
            model="gpt-4o-mini",
            status="active",
            deployed_at=now - timedelta(days=15),
            created_at=now - timedelta(days=15),
            avg_quality_score=Decimal("0.84"),
            avg_cost_usd=Decimal("0.001700"),
            avg_latency_ms=980,
        ),
    ]


def _pick_model(day_index: int, use_case: str) -> tuple[str, Provider]:
    if day_index == 25 and use_case == "quote_generation":
        return "gpt-4o", Provider.OPENAI
    roll = random.random()
    cumulative = 0.0
    for model, provider, weight in MODEL_MIX:
        cumulative += weight
        if roll <= cumulative:
            return model, provider
    model, provider, _ = MODEL_MIX[-1]
    return model, provider


def _quality_for_day(day_index: int, prompt_version: str) -> float:
    if day_index == 18:
        return 0.61
    base = 0.78 if prompt_version == "v1.0" else 0.84
    return round(base + random.uniform(-0.04, 0.04), 4)


def _drift_for_day(day_index: int, use_case: str) -> float:
    if day_index == 22 and use_case == "renewal_agent":
        return 0.42
    return round(random.uniform(0.05, 0.22), 4)


def _latency_for_model(model: str) -> int:
    base = {
        "gpt-4o-mini": 820,
        "claude-3-5-haiku-20241022": 1050,
        "gpt-4o": 1800,
    }[model]
    return max(100, int(random.gauss(base, 180)))


if __name__ == "__main__":
    asyncio.run(main())
