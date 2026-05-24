"""
Quote-to-Cash orchestration service that turns one opportunity into a governed
recommendation and trace.

Author: Sarala Biswal
"""

from decimal import Decimal
from uuid import uuid4

from api.dependencies import Settings
from revenue_desk.agents import (
    APPROVAL_ROUTING_AGENT,
    DISCOUNT_POLICY_AGENT,
    MARGIN_RISK_AGENT,
    NEGOTIATION_GUIDANCE_AGENT,
    OPPORTUNITY_CONTEXT_AGENT,
)
from revenue_desk.catalog import get_opportunity
from revenue_desk.llm import RevenueLLMClient
from revenue_desk.models import (
    ApprovalDecision,
    QuoteInput,
    QuoteRecommendation,
    RenewalOpportunity,
    RenewalRisk,
    RevenueAgentTrace,
    RevenueDeskResponse,
    RevenuePromptVersion,
)


class RevenueCommandCenterError(ValueError):
    """Raised when the Revenue Command Center workflow cannot complete."""


class RevenueCommandCenterService:
    """Run a standalone Quote-to-Cash analysis and build observable trace output."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def analyze(self, quote_input: QuoteInput) -> RevenueDeskResponse:
        """Generate a structured revenue recommendation for one opportunity."""
        opportunity = get_opportunity(quote_input.opportunity_id)
        if opportunity is None:
            raise RevenueCommandCenterError(
                f"Revenue opportunity not found: {quote_input.opportunity_id}"
            )

        client = RevenueLLMClient(
            self.settings,
            quote_input.model_mode,
            quote_input.local_model,
        )
        context_text = _context_summary(opportunity)
        context_step = await OPPORTUNITY_CONTEXT_AGENT.run(
            client=client,
            opportunity=opportunity,
            prompt_version=quote_input.prompt_version,
            prompt_context=_prompt_context(
                quote_input,
                "Summarize account health, renewal risk, and evidence.",
            ),
            mock_text=context_text,
            detail=context_text,
            evidence=[
                f"Health score {opportunity.account.customer_health}",
                f"Renewal risk {opportunity.renewal_risk.value}",
            ],
            quality_score=_agent_quality_score(opportunity, "context"),
        )
        recommendation = _build_recommendation(
            opportunity=opportunity,
            prompt_version=quote_input.prompt_version,
            approval_guardrails_enabled=quote_input.approval_guardrails_enabled,
            llm_guidance=context_step.detail,
        )
        downstream_steps = [
            await DISCOUNT_POLICY_AGENT.run(
                client=client,
                opportunity=opportunity,
                prompt_version=quote_input.prompt_version,
                prompt_context=_prompt_context(
                    quote_input,
                    "Evaluate requested discount against policy and commercial pressure.",
                ),
                mock_text=_discount_policy_text(opportunity, recommendation),
                detail=_discount_policy_text(opportunity, recommendation),
                evidence=opportunity.approval_flags
                or [f"Policy cap {_policy_discount_cap(opportunity):.1f}%"],
                quality_score=_agent_quality_score(opportunity, "discount"),
            ),
            await MARGIN_RISK_AGENT.run(
                client=client,
                opportunity=opportunity,
                prompt_version=quote_input.prompt_version,
                prompt_context=_prompt_context(
                    quote_input,
                    "Assess expected margin, target margin gap, and financial risk.",
                ),
                mock_text=recommendation.margin_risk_assessment,
                detail=recommendation.margin_risk_assessment,
                evidence=[
                    f"Target margin {opportunity.target_margin_pct:.1f}%",
                    f"Expected margin {recommendation.expected_margin_pct:.1f}%",
                ],
                quality_score=_agent_quality_score(opportunity, "margin", recommendation),
            ),
            await APPROVAL_ROUTING_AGENT.run(
                client=client,
                opportunity=opportunity,
                prompt_version=quote_input.prompt_version,
                prompt_context=_prompt_context(
                    quote_input,
                    "Select the approval path and explain governance controls.",
                ),
                mock_text=_approval_route_text(recommendation),
                detail=_approval_route_text(recommendation),
                evidence=recommendation.evidence_citations,
                quality_score=_agent_quality_score(opportunity, "approval", recommendation),
            ),
            await NEGOTIATION_GUIDANCE_AGENT.run(
                client=client,
                opportunity=opportunity,
                prompt_version=quote_input.prompt_version,
                prompt_context=_prompt_context(
                    quote_input,
                    "Draft seller guidance and customer-facing quote language.",
                ),
                mock_text=_negotiation_guidance_text(recommendation),
                detail=_negotiation_guidance_text(recommendation),
                evidence=recommendation.evidence_citations,
                quality_score=_agent_quality_score(opportunity, "negotiation", recommendation),
            ),
        ]
        steps = [context_step, *downstream_steps]
        trace = RevenueAgentTrace(
            trace_id=f"trace-{uuid4()}",
            call_id=f"rcc-flow-{uuid4()}",
            prompt_version=quote_input.prompt_version,
            model_mode=quote_input.model_mode,
            model=steps[0].model,
            provider=steps[0].provider,
            input_tokens=sum(step.input_tokens for step in steps),
            output_tokens=sum(step.output_tokens for step in steps),
            latency_ms=sum(step.latency_ms for step in steps),
            quality_score=round(sum(step.quality_score for step in steps) / len(steps), 4),
            margin_risk_score=_margin_risk_score(opportunity, recommendation),
            steps=steps,
        )
        return RevenueDeskResponse(
            status="completed",
            opportunity=opportunity,
            recommendation=recommendation,
            trace=trace,
        )


def _build_recommendation(
    *,
    opportunity: RenewalOpportunity,
    prompt_version: RevenuePromptVersion,
    approval_guardrails_enabled: bool,
    llm_guidance: str,
) -> QuoteRecommendation:
    policy_cap = _policy_discount_cap(opportunity)
    risk_adjustment = {
        RenewalRisk.LOW: 0.0,
        RenewalRisk.MEDIUM: 1.5,
        RenewalRisk.HIGH: 3.0,
        RenewalRisk.CRITICAL: 4.0,
    }[opportunity.renewal_risk]
    version_adjustment = {
        RevenuePromptVersion.V1_GENERIC: 2.5,
        RevenuePromptVersion.V21_MARGIN_AWARE: 0.0,
        RevenuePromptVersion.V22_APPROVAL_GUARDED: -1.0,
    }[prompt_version]
    recommended_discount = min(
        opportunity.requested_discount_pct,
        max(opportunity.current_discount_pct, policy_cap + risk_adjustment + version_adjustment),
    )
    # Only the approval-aware prompt family converts advisory policy into a hard cap.
    if approval_guardrails_enabled and prompt_version is RevenuePromptVersion.V22_APPROVAL_GUARDED:
        recommended_discount = min(recommended_discount, policy_cap)

    expected_margin = max(35.0, opportunity.current_margin_pct - (recommended_discount * 0.28))
    forecast_arr = opportunity.arr_usd + opportunity.expansion_arr_usd
    forecast_tcv = forecast_arr * Decimal(opportunity.contract_terms_months) / Decimal(12)
    decision = _approval_decision(opportunity, recommended_discount, expected_margin)
    citations = opportunity.grounded_evidence[:3]
    summary = (
        f"{opportunity.renewal_risk.value.title()} renewal risk: "
        f"{opportunity.account.name} has health {opportunity.account.customer_health}, "
        f"{len(opportunity.approval_flags)} approval signal(s), and "
        f"{opportunity.requested_discount_pct:.1f}% requested discount."
    )
    margin = (
        f"Expected margin is {expected_margin:.1f}% against a "
        f"{opportunity.target_margin_pct:.1f}% target after a "
        f"{recommended_discount:.1f}% recommended discount."
    )
    guidance = [
        f"Lead with the {opportunity.scenario.replace('_', ' ')} business case.",
        f"Hold discount at {recommended_discount:.1f}% unless term or scope expands.",
        llm_guidance,
    ]
    if opportunity.expansion_arr_usd > 0:
        guidance.insert(1, "Tie concession language to documented expansion ARR.")
    if decision is not ApprovalDecision.AUTO_APPROVE:
        guidance.append("Route to revenue leadership before customer-facing commitment.")

    note = (
        f"Thank you for partnering with us on {opportunity.name}. The proposed renewal "
        f"keeps the program aligned to the documented success plan while applying a "
        f"{recommended_discount:.1f}% commercial adjustment tied to the current scope."
    )
    return QuoteRecommendation(
        renewal_risk_summary=summary,
        recommended_discount_pct=round(recommended_discount, 2),
        margin_risk_assessment=margin,
        approval_recommendation=decision,
        negotiation_guidance=guidance,
        customer_facing_quote_note=note,
        evidence_citations=citations,
        forecast_arr_usd=forecast_arr,
        forecast_tcv_usd=forecast_tcv,
        expected_margin_pct=round(expected_margin, 2),
    )


def _policy_discount_cap(opportunity: RenewalOpportunity) -> float:
    base = 12.0
    if opportunity.contract_terms_months >= 36:
        base += 6.0
    if opportunity.expansion_arr_usd >= Decimal("250000"):
        base += 4.0
    if opportunity.current_margin_pct < opportunity.target_margin_pct:
        base -= 3.0
    return max(8.0, base)


def _approval_decision(
    opportunity: RenewalOpportunity,
    recommended_discount: float,
    expected_margin: float,
) -> ApprovalDecision:
    margin_floor = opportunity.target_margin_pct - 8
    if opportunity.renewal_risk is RenewalRisk.CRITICAL or expected_margin < margin_floor:
        return ApprovalDecision.EXECUTIVE_REVIEW
    if (
        recommended_discount >= 20
        or expected_margin < opportunity.target_margin_pct
        or len(opportunity.approval_flags) >= 2
    ):
        return ApprovalDecision.APPROVAL_REQUIRED
    return ApprovalDecision.AUTO_APPROVE


def _quality_score(
    opportunity: RenewalOpportunity,
    recommendation: QuoteRecommendation,
) -> float:
    evidence_bonus = min(0.08, len(recommendation.evidence_citations) * 0.025)
    margin_penalty = (
        0.08 if recommendation.expected_margin_pct < opportunity.target_margin_pct else 0.0
    )
    return round(max(0.55, min(0.96, 0.86 + evidence_bonus - margin_penalty)), 4)


def _agent_quality_score(
    opportunity: RenewalOpportunity,
    agent: str,
    recommendation: QuoteRecommendation | None = None,
) -> float:
    base = _quality_score(opportunity, recommendation) if recommendation else 0.86
    evidence_bonus = min(0.04, len(opportunity.grounded_evidence) * 0.01)
    if agent == "context":
        return round(min(0.97, base + evidence_bonus), 4)
    if agent == "discount":
        policy_pressure = max(
            0.0,
            opportunity.requested_discount_pct - _policy_discount_cap(opportunity),
        )
        return round(max(0.62, min(0.96, base - (policy_pressure / 220))), 4)
    if agent == "margin" and recommendation is not None:
        margin_gap = max(0.0, opportunity.target_margin_pct - recommendation.expected_margin_pct)
        return round(max(0.60, min(0.96, base - (margin_gap / 120))), 4)
    if agent == "approval" and recommendation is not None:
        routed = recommendation.approval_recommendation is not ApprovalDecision.AUTO_APPROVE
        flag_bonus = 0.025 if routed and opportunity.approval_flags else 0.0
        return round(max(0.64, min(0.97, base + flag_bonus)), 4)
    if agent == "negotiation":
        return round(max(0.62, min(0.95, base + evidence_bonus - 0.015)), 4)
    return base


def _margin_risk_score(
    opportunity: RenewalOpportunity,
    recommendation: QuoteRecommendation,
) -> float:
    margin_gap = max(0.0, opportunity.target_margin_pct - recommendation.expected_margin_pct)
    discount_pressure = max(
        0.0,
        opportunity.requested_discount_pct - recommendation.recommended_discount_pct,
    )
    return round(min(1.0, (margin_gap / 20) + (discount_pressure / 100)), 4)


def _prompt_context(quote_input: QuoteInput, task: str) -> str:
    notes = quote_input.reviewer_notes.strip()
    # Keep prompt text truthful: v1.0/v2.1 can mention policy, but only v2.2 enforces it.
    guardrails_enforced = (
        quote_input.approval_guardrails_enabled
        and quote_input.prompt_version is RevenuePromptVersion.V22_APPROVAL_GUARDED
    )
    guardrail_mode = (
        "approval guardrails enforced"
        if guardrails_enforced
        else "approval guardrails advisory"
    )
    if notes:
        return f"{task} Reviewer notes: {notes}. Mode: {guardrail_mode}."
    return f"{task} Mode: {guardrail_mode}."


def _context_summary(opportunity: RenewalOpportunity) -> str:
    return (
        f"{opportunity.account.name} is a {opportunity.account.segment} "
        f"{opportunity.account.industry} account with health "
        f"{opportunity.account.customer_health}, {opportunity.renewal_risk.value} renewal risk, "
        f"and {len(opportunity.grounded_evidence)} grounded evidence item(s)."
    )


def _discount_policy_text(
    opportunity: RenewalOpportunity,
    recommendation: QuoteRecommendation,
) -> str:
    return (
        f"Requested discount is {opportunity.requested_discount_pct:.1f}% against a "
        f"{_policy_discount_cap(opportunity):.1f}% policy cap; recommend "
        f"{recommendation.recommended_discount_pct:.1f}% with concessions tied to term, "
        "scope, or expansion commitment."
    )


def _approval_route_text(recommendation: QuoteRecommendation) -> str:
    return (
        "Decision: "
        f"{recommendation.approval_recommendation.value.replace('_', ' ')} based on "
        "discount, margin, renewal risk, and policy flags."
    )


def _negotiation_guidance_text(recommendation: QuoteRecommendation) -> str:
    return " ".join(
        [
            *recommendation.negotiation_guidance,
            recommendation.customer_facing_quote_note,
        ]
    )
