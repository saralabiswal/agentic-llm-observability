"""
Prompt registry, version tracking, and comparison support for governance workflows.

Author: Sarala Biswal
"""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from prompts.version_store import PromptVersionStore


class ABResult(BaseModel):
    version_a_id: str
    version_b_id: str
    winner_version_id: str
    quality_delta: float
    cost_delta: Decimal
    latency_delta: int
    statistical_note: str

    model_config = ConfigDict(frozen=True)


class ABEvaluator:
    def __init__(self, version_store: PromptVersionStore) -> None:
        self.version_store = version_store

    async def compare(self, version_a_id: str, version_b_id: str) -> ABResult:
        a = await self.version_store.get_performance(version_a_id)
        b = await self.version_store.get_performance(version_b_id)
        quality_delta = float(b["avg_quality_score"]) - float(a["avg_quality_score"])
        cost_delta = Decimal(b["avg_cost_usd"]) - Decimal(a["avg_cost_usd"])
        latency_delta = int(b["avg_latency_ms"]) - int(a["avg_latency_ms"])
        winner = (
            version_b_id
            if _score_variant(quality_delta, cost_delta, latency_delta) >= 0
            else version_a_id
        )
        sample_count = min(int(a["call_count"]), int(b["call_count"]))
        note = (
            "directional only; collect more samples"
            if sample_count < 30
            else f"based on {sample_count} paired samples per version"
        )
        return ABResult(
            version_a_id=version_a_id,
            version_b_id=version_b_id,
            winner_version_id=winner,
            quality_delta=round(quality_delta, 4),
            cost_delta=cost_delta.quantize(Decimal("0.000001")),
            latency_delta=latency_delta,
            statistical_note=note,
        )


def _score_variant(quality_delta: float, cost_delta: Decimal, latency_delta: int) -> float:
    cost_penalty = float(cost_delta) * 10
    latency_penalty = latency_delta / 10_000
    return quality_delta - cost_penalty - latency_penalty
