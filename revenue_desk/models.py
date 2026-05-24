"""
Quote-to-Cash domain catalog, policy, and model layer used by the agentic flow.

Author: Sarala Biswal
"""

from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, computed_field


class RenewalRisk(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ProductTier(StrEnum):
    STANDARD = "standard"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    STRATEGIC = "strategic"


class ApprovalDecision(StrEnum):
    AUTO_APPROVE = "auto_approve"
    APPROVAL_REQUIRED = "approval_required"
    EXECUTIVE_REVIEW = "executive_review"


class LLMMode(StrEnum):
    MOCK = "mock"
    OLLAMA = "ollama"
    OPENAI = "openai"


class LocalLLMModel(StrEnum):
    LLAMA32 = "llama3.2"
    MISTRAL = "mistral"
    QWEN25_7B = "qwen2.5:7b"


class RevenuePromptVersion(StrEnum):
    V1_GENERIC = "v1.0"
    V21_MARGIN_AWARE = "v2.1"
    V22_APPROVAL_GUARDED = "v2.2"


class Account(BaseModel):
    account_id: str
    name: str
    segment: str
    industry: str
    region: str
    customer_health: int = Field(ge=0, le=100)
    executive_sponsor: str

    model_config = ConfigDict(frozen=True)


class RenewalOpportunity(BaseModel):
    opportunity_id: str
    account: Account
    scenario: str
    name: str
    stage: str
    arr_usd: Decimal = Field(ge=Decimal("0"))
    expansion_arr_usd: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    current_discount_pct: float = Field(ge=0.0, le=80.0)
    requested_discount_pct: float = Field(ge=0.0, le=80.0)
    target_margin_pct: float = Field(ge=0.0, le=100.0)
    current_margin_pct: float = Field(ge=0.0, le=100.0)
    renewal_risk: RenewalRisk
    product_tier: ProductTier
    contract_terms_months: int = Field(ge=1)
    close_date: str
    approval_flags: list[str]
    pain_points: list[str]
    success_plan: list[str]
    grounded_evidence: list[str]

    model_config = ConfigDict(frozen=True)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_contract_value_usd(self) -> Decimal:
        annual_value = self.arr_usd + self.expansion_arr_usd
        return annual_value * Decimal(self.contract_terms_months) / Decimal(12)


class QuoteInput(BaseModel):
    opportunity_id: str
    prompt_version: RevenuePromptVersion = RevenuePromptVersion.V21_MARGIN_AWARE
    model_mode: LLMMode = LLMMode.OLLAMA
    local_model: LocalLLMModel | None = None
    approval_guardrails_enabled: bool = True
    reviewer_notes: str = ""

    model_config = ConfigDict(frozen=True)


class QuoteRecommendation(BaseModel):
    renewal_risk_summary: str
    recommended_discount_pct: float = Field(ge=0.0, le=80.0)
    margin_risk_assessment: str
    approval_recommendation: ApprovalDecision
    negotiation_guidance: list[str]
    customer_facing_quote_note: str
    evidence_citations: list[str]
    forecast_arr_usd: Decimal = Field(ge=Decimal("0"))
    forecast_tcv_usd: Decimal = Field(ge=Decimal("0"))
    expected_margin_pct: float = Field(ge=0.0, le=100.0)

    model_config = ConfigDict(frozen=True)


class RevenueAgentStep(BaseModel):
    step_id: str
    label: str
    system: str
    agent_name: str
    prompt_name: str
    prompt_version: str
    call_id: str
    model: str
    provider: str
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    latency_ms: int = Field(ge=0)
    cost_usd: Decimal = Field(default=Decimal("0.0"), ge=Decimal("0.0"))
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    status: str
    detail: str
    evidence: list[str] = Field(default_factory=list)

    model_config = ConfigDict(frozen=True)


class RevenueAgentTrace(BaseModel):
    trace_id: str
    call_id: str
    use_case: str = "quote_to_cash_revenue_command_center"
    prompt_version: RevenuePromptVersion
    model_mode: LLMMode
    model: str
    provider: str
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    latency_ms: int = Field(ge=0)
    cost_usd: Decimal = Field(default=Decimal("0.0"), ge=Decimal("0.0"))
    quality_score: float = Field(ge=0.0, le=1.0)
    margin_risk_score: float = Field(ge=0.0, le=1.0)
    alerts_created: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    steps: list[RevenueAgentStep]

    model_config = ConfigDict(frozen=True)


class RevenueDeskResponse(BaseModel):
    status: str
    opportunity: RenewalOpportunity
    recommendation: QuoteRecommendation
    trace: RevenueAgentTrace

    model_config = ConfigDict(frozen=True)
