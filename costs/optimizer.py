"""
Cost attribution, provider rate cards, and optimization logic for token economics.

Author: Sarala Biswal
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import OptimizationRecommendation, Provider
from audit.models import LLMCall
from costs.cost_calculator import CostCalculator
from costs.provider_models import PROVIDER_COSTS

QUALITY_BENCHMARKS: dict[tuple[str, str], float] = {
    ("gpt-4o", "gpt-4o-mini"): -0.032,
    ("gpt-4o", "llama3.2"): -0.048,
    ("gpt-4o", "mistral"): -0.049,
    ("gpt-4o", "qwen2.5:7b"): -0.043,
    ("gpt-4o-mini", "llama3.2"): -0.027,
    ("gpt-4o-mini", "mistral"): -0.041,
    ("gpt-4o-mini", "qwen2.5:7b"): -0.034,
    ("llama3.2", "mistral"): -0.016,
    ("llama3.2", "qwen2.5:7b"): 0.012,
    ("mistral", "llama3.2"): 0.016,
    ("mistral", "qwen2.5:7b"): 0.028,
    ("qwen2.5:7b", "llama3.2"): -0.012,
    ("qwen2.5:7b", "mistral"): -0.028,
    ("claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022"): -0.041,
    ("gpt-4o", "claude-3-5-haiku-20241022"): -0.028,
}

ALTERNATIVE_MODELS: tuple[tuple[str, Provider], ...] = tuple(
    (model, Provider(provider))
    for provider, models in PROVIDER_COSTS.items()
    for model in models
    if provider in {Provider.OPENAI.value, Provider.ANTHROPIC.value, Provider.OLLAMA.value}
)
LOCAL_MODELS: frozenset[str] = frozenset(PROVIDER_COSTS[Provider.OLLAMA.value])


@dataclass(frozen=True)
class CurrentModelStats:
    model: str
    provider: Provider
    avg_input_tokens: int
    avg_output_tokens: int
    total_calls: int
    monthly_cost: Decimal


class CostOptimizer:
    def __init__(self, session: AsyncSession, calculator: CostCalculator | None = None) -> None:
        self.session = session
        self.calculator = calculator or CostCalculator()

    async def generate_recommendations(
        self,
        use_case: str,
        days: int = 30,
        target_model: str | None = None,
    ) -> list[OptimizationRecommendation]:
        current = await self._get_current_model_stats(use_case, days)
        if current is None:
            return []

        recommendations: list[OptimizationRecommendation] = []
        target_recommendation: OptimizationRecommendation | None = None
        local_routing_requested = target_model in LOCAL_MODELS
        for alt_model, alt_provider in ALTERNATIVE_MODELS:
            if (
                alt_provider is Provider.OLLAMA
                and current.provider is not Provider.OLLAMA
                and not local_routing_requested
                and alt_model != target_model
            ):
                continue
            if alt_model == current.model and alt_provider == current.provider:
                if target_model == alt_model:
                    target_recommendation = _build_recommendation(
                        use_case,
                        current,
                        alt_model,
                        Decimal("0.000000"),
                        current.monthly_cost,
                        0.0,
                    )
                continue

            quality_delta = QUALITY_BENCHMARKS.get((current.model, alt_model), -0.10)
            if quality_delta < -0.05 and alt_model != target_model:
                continue

            alt_cost_per_call = self.calculator.calculate_call_cost(
                alt_model,
                alt_provider,
                current.avg_input_tokens,
                current.avg_output_tokens,
            )
            alt_monthly_cost = (
                alt_cost_per_call * Decimal(current.total_calls) * Decimal(30) / Decimal(days)
            )
            monthly_savings = current.monthly_cost - alt_monthly_cost
            if monthly_savings <= 0 and alt_model != target_model:
                continue

            recommendation = _build_recommendation(
                use_case,
                current,
                alt_model,
                monthly_savings,
                alt_monthly_cost,
                quality_delta,
            )
            if alt_model == target_model:
                target_recommendation = recommendation
                continue
            recommendations.append(recommendation)

        sorted_recommendations = sorted(
            recommendations,
            key=lambda item: item.monthly_savings_usd,
            reverse=True,
        )[:3]
        if target_recommendation is None:
            return sorted_recommendations
        return [
            target_recommendation,
            *[
                recommendation
                for recommendation in sorted_recommendations
                if recommendation.recommended_model != target_recommendation.recommended_model
            ],
        ]

    async def _get_current_model_stats(self, use_case: str, days: int) -> CurrentModelStats | None:
        since = datetime.now(UTC) - timedelta(days=days)
        result = await self.session.execute(
            select(
                LLMCall.model,
                LLMCall.provider,
                func.avg(LLMCall.input_tokens),
                func.avg(LLMCall.output_tokens),
                func.count(LLMCall.call_id),
                func.sum(LLMCall.cost_usd),
            )
            .where(LLMCall.use_case == use_case)
            .where(LLMCall.timestamp >= since)
            .group_by(LLMCall.model, LLMCall.provider)
            .order_by(func.sum(LLMCall.cost_usd).desc())
            .limit(1)
        )
        row = result.one_or_none()
        if row is None:
            return None
        model, provider, avg_input, avg_output, total_calls, total_cost = row
        monthly_cost = Decimal(total_cost or 0) * Decimal(30) / Decimal(days)
        return CurrentModelStats(
            model=str(model),
            provider=Provider(str(provider)),
            avg_input_tokens=int(avg_input or 0),
            avg_output_tokens=int(avg_output or 0),
            total_calls=int(total_calls or 0),
            monthly_cost=monthly_cost,
        )


def _build_recommendation(
    use_case: str,
    current: CurrentModelStats,
    alt_model: str,
    monthly_savings: Decimal,
    alt_monthly_cost: Decimal,
    quality_delta: float,
) -> OptimizationRecommendation:
    savings_pct = (
        round(float(monthly_savings / current.monthly_cost * Decimal("100")), 2)
        if current.monthly_cost > 0
        else 0.0
    )
    return OptimizationRecommendation(
        use_case=use_case,
        current_model=current.model,
        current_cost_usd=current.monthly_cost.quantize(Decimal("0.000001")),
        recommended_model=alt_model,
        recommended_cost_usd=alt_monthly_cost.quantize(Decimal("0.000001")),
        quality_delta_pct=round(quality_delta * 100, 2),
        cost_savings_pct=savings_pct,
        monthly_savings_usd=monthly_savings.quantize(Decimal("0.000001")),
        rationale=_build_rationale(current.model, alt_model, quality_delta, monthly_savings),
    )


def _build_rationale(
    current_model: str,
    alt_model: str,
    quality_delta: float,
    monthly_savings: Decimal,
) -> str:
    if monthly_savings == 0:
        return (
            "For Quote-to-Cash analysis, keep routing on "
            f"{alt_model}; this is the selected runtime model and shows no routed cost change."
        )
    change_word = "savings" if monthly_savings > 0 else "additional monthly cost"
    quality_word = "delta" if quality_delta < 0 else "lift"
    return (
        "For Quote-to-Cash analysis, route low-risk pricing drafts from "
        f"{current_model} to {alt_model} for "
        f"${abs(monthly_savings).quantize(Decimal('0.000001'))} observed {change_word} "
        f"with {quality_delta * 100:.1f}% expected quality {quality_word}."
    )
