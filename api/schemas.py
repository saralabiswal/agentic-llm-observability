"""
API bootstrap, settings, schemas, and shared dependency wiring for the observability
service.

Author: Sarala Biswal
"""

from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator


class Provider(StrEnum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE = "azure"
    OLLAMA = "ollama"


class AlertType(StrEnum):
    COST = "cost"
    QUALITY = "quality"
    DRIFT = "drift"
    LATENCY = "latency"


class AlertSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PromptStatus(StrEnum):
    ACTIVE = "active"
    TESTING = "testing"
    DEPRECATED = "deprecated"


class LLMCallRecord(BaseModel):
    call_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    model: str
    provider: Provider
    use_case: str
    prompt_version: str
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    latency_ms: int = Field(ge=0)
    cost_usd: Decimal = Field(default=Decimal("0.0"), ge=Decimal("0.0"))
    quality_score: float | None = Field(default=None, ge=0.0, le=1.0)
    hallucination_flag: bool = False
    quality_gate_passed: bool | None = None
    response_text: str | None = None
    context_text: str | None = None

    model_config = ConfigDict(frozen=True)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @field_validator("cost_usd")
    @classmethod
    def quantize_cost(cls, value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.000001"))


class CostSummary(BaseModel):
    total_cost_usd: Decimal
    total_calls: int = Field(ge=0)
    avg_cost_per_call: Decimal
    cost_by_model: dict[str, Decimal]
    cost_by_usecase: dict[str, Decimal]
    top_cost_driver: str
    projected_monthly_usd: Decimal
    budget_burn_rate_pct: float = Field(ge=0.0)

    model_config = ConfigDict(frozen=True)


class OptimizationRecommendation(BaseModel):
    use_case: str
    current_model: str
    current_cost_usd: Decimal
    recommended_model: str
    recommended_cost_usd: Decimal
    quality_delta_pct: float
    cost_savings_pct: float
    monthly_savings_usd: Decimal
    rationale: str

    model_config = ConfigDict(frozen=True)


class LatencyPercentiles(BaseModel):
    model: str
    p50_ms: int = Field(ge=0)
    p95_ms: int = Field(ge=0)
    p99_ms: int = Field(ge=0)
    slo_target_ms: int = Field(ge=0)
    slo_compliance_pct: float = Field(ge=0.0, le=100.0)
    breach_count_24h: int = Field(ge=0)

    model_config = ConfigDict(frozen=True)


class QualityScore(BaseModel):
    use_case: str
    model: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    faithfulness: float = Field(ge=0.0, le=1.0)
    relevance: float = Field(ge=0.0, le=1.0)
    coherence: float = Field(ge=0.0, le=1.0)
    gate_passed: bool

    model_config = ConfigDict(frozen=True)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def composite_score(self) -> float:
        return round(self.faithfulness * 0.45 + self.relevance * 0.35 + self.coherence * 0.20, 4)


class DriftScore(BaseModel):
    use_case: str
    model: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    drift_score: float = Field(ge=0.0, le=1.0)
    baseline_similarity: float = Field(ge=-1.0, le=1.0)
    alert_triggered: bool

    model_config = ConfigDict(frozen=True)


class PromptVersion(BaseModel):
    version_id: str
    use_case: str
    version: str
    prompt_text: str
    model: str
    status: PromptStatus = PromptStatus.TESTING
    deployed_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    avg_quality_score: float | None = Field(default=None, ge=0.0, le=1.0)
    avg_cost_usd: Decimal | None = None
    avg_latency_ms: int | None = Field(default=None, ge=0)

    model_config = ConfigDict(frozen=True)


class AlertRecord(BaseModel):
    alert_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    alert_type: AlertType
    severity: AlertSeverity
    use_case: str | None = None
    message: str
    metric_value: float | None = None
    threshold_value: float | None = None
    resolved: bool = False

    model_config = ConfigDict(frozen=True)
