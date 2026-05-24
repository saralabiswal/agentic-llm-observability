"""
FastAPI routes for the Quote-to-Cash agentic workflow and prompt inspection APIs.

Author: Sarala Biswal
"""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import Settings, get_session, get_settings
from api.schemas import LLMCallRecord, PromptStatus, Provider
from audit.models import DriftScoreRow, PromptVersionRow, QualityScoreRow
from costs.cost_calculator import CostCalculator
from drift.alert_engine import AlertEngine
from revenue_desk.agents import REVENUE_AGENTS, RevenueAgent, build_agent_prompt
from revenue_desk.catalog import get_opportunity, list_opportunities
from revenue_desk.models import (
    QuoteInput,
    RenewalOpportunity,
    RevenueAgentStep,
    RevenueDeskResponse,
    RevenuePromptVersion,
)
from revenue_desk.policies import policy_for_prompt
from revenue_desk.service import (
    RevenueCommandCenterError,
    RevenueCommandCenterService,
    _prompt_context,
)
from tracking.token_tracker import TokenTracker

router = APIRouter(prefix="/revenue-desk", tags=["revenue-desk"])

_PROMPT_TASKS: dict[str, str] = {
    "context": "Summarize account health, renewal risk, and evidence.",
    "discount_policy": "Evaluate requested discount against policy and commercial pressure.",
    "margin_risk": "Assess expected margin, target margin gap, and financial risk.",
    "approval_route": "Select the approval path and explain governance controls.",
    "negotiation_guidance": "Draft seller guidance and customer-facing quote language.",
}


@router.get("/opportunities", response_model=list[RenewalOpportunity])
async def revenue_opportunities() -> list[RenewalOpportunity]:
    """Return deterministic Revenue Command Center opportunities."""
    return list_opportunities()


@router.get("/opportunities/{opportunity_id}", response_model=RenewalOpportunity)
async def revenue_opportunity(opportunity_id: str) -> RenewalOpportunity:
    """Return one Revenue Command Center opportunity."""
    opportunity = get_opportunity(opportunity_id)
    if opportunity is None:
        raise HTTPException(status_code=404, detail=f"Opportunity not found: {opportunity_id}")
    return opportunity


@router.get("/controls")
async def revenue_controls() -> dict[str, list[dict[str, str]]]:
    """Return prompt strategies supported by the Quote-to-Cash flow."""
    return {
        "prompt_versions": [
            {
                "value": RevenuePromptVersion.V1_GENERIC.value,
                "label": "Baseline prompt v1.0 - fastest draft",
            },
            {
                "value": RevenuePromptVersion.V21_MARGIN_AWARE.value,
                "label": "Margin-aware prompt v2.1 - preserve target margin",
            },
            {
                "value": RevenuePromptVersion.V22_APPROVAL_GUARDED.value,
                "label": "Approval-aware prompt v2.2 - policy-ready",
            },
        ]
    }


@router.get("/developer/prompts")
async def revenue_developer_prompts(
    opportunity_id: Annotated[str, Query()] = "RCC-OPP-002",
    prompt_version: Annotated[RevenuePromptVersion, Query()] = (
        RevenuePromptVersion.V22_APPROVAL_GUARDED
    ),
    approval_guardrails_enabled: Annotated[bool, Query()] = True,
    reviewer_notes: Annotated[str, Query()] = "",
) -> dict[str, object]:
    """Preview the exact prompt bodies used by each Quote-to-Cash agent."""
    opportunity = get_opportunity(opportunity_id)
    if opportunity is None:
        raise HTTPException(status_code=404, detail=f"Opportunity not found: {opportunity_id}")

    quote_input = QuoteInput(
        opportunity_id=opportunity_id,
        prompt_version=prompt_version,
        approval_guardrails_enabled=approval_guardrails_enabled,
        reviewer_notes=reviewer_notes,
    )
    prompts = [
        _developer_prompt(agent, opportunity, prompt_version, quote_input)
        for agent in REVENUE_AGENTS
    ]
    effective_guardrails_enabled = (
        approval_guardrails_enabled
        and prompt_version is RevenuePromptVersion.V22_APPROVAL_GUARDED
    )
    return {
        "use_case": "quote_to_cash_revenue_command_center",
        "opportunity_id": opportunity.opportunity_id,
        "opportunity_name": opportunity.name,
        "account_name": opportunity.account.name,
        "prompt_version": prompt_version.value,
        "approval_guardrails_enabled": effective_guardrails_enabled,
        "prompts": prompts,
    }


def _developer_prompt(
    agent: RevenueAgent,
    opportunity: RenewalOpportunity,
    prompt_version: RevenuePromptVersion,
    quote_input: QuoteInput,
) -> dict[str, object]:
    policy = policy_for_prompt(agent.prompt_name, opportunity)
    return {
        "step_id": agent.step_id,
        "agent_name": agent.agent_name,
        "prompt_name": agent.prompt_name,
        "prompt_contract": f"{prompt_version.value}.{agent.prompt_name}",
        "label": agent.label,
        "system": agent.system,
        "prompt": build_agent_prompt(
            agent=agent,
            opportunity=opportunity,
            prompt_version=prompt_version,
            prompt_context=_prompt_context(
                quote_input,
                _PROMPT_TASKS[agent.prompt_name],
            ),
        ),
        "policy_source": {
            "policy_id": policy.policy_id,
            "title": policy.title,
            "owner": policy.owner,
            "version": policy.version,
            "source": policy.source,
            "rules": policy.rules,
        },
        "observability_fields": [
            "model",
            "provider",
            "input_tokens",
            "output_tokens",
            "latency_ms",
            "cost_usd",
            "quality_score",
            "prompt_version",
        ],
    }


@router.post("/analyze", response_model=RevenueDeskResponse)
async def analyze_revenue_opportunity(
    quote_input: QuoteInput,
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> RevenueDeskResponse:
    """Run analysis and persist observability telemetry for each agent LLM call."""
    try:
        response = await RevenueCommandCenterService(settings).analyze(quote_input)
    except RevenueCommandCenterError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    trace = response.trace
    await _ensure_prompt_versions(
        session,
        trace.model,
        [step.prompt_version for step in trace.steps],
    )
    costed_steps: list[RevenueAgentStep] = []
    records: list[LLMCallRecord] = []
    calculator = CostCalculator()
    tracker = TokenTracker(session)
    for step in trace.steps:
        provider = Provider(step.provider)
        cost = calculator.calculate_call_cost(
            step.model,
            provider,
            step.input_tokens,
            step.output_tokens,
        )
        costed_step = step.model_copy(update={"cost_usd": cost})
        costed_steps.append(costed_step)
        record = _step_record(trace.use_case, costed_step)
        records.append(record)
        await tracker.record_call(record)
        session.add(_quality_score_row(record))

    aggregate_cost = sum((step.cost_usd for step in costed_steps), Decimal("0.0"))
    aggregate_quality = (
        round(sum(step.quality_score for step in costed_steps) / len(costed_steps), 4)
        if costed_steps
        else trace.quality_score
    )
    drift_score = _drift_score(response)
    session.add(
        DriftScoreRow(
            timestamp=records[-1].timestamp if records else datetime.now(UTC),
            use_case=trace.use_case,
            model=trace.model,
            drift_score=drift_score,
            baseline_similarity=max(-1.0, min(1.0, 1.0 - drift_score)),
            alert_triggered=drift_score > settings.drift_alert_threshold,
        )
    )
    await session.commit()
    alerts = await AlertEngine(session, settings).check_thresholds(
        use_case=trace.use_case,
        drift_score=drift_score,
        quality_score=aggregate_quality,
    )
    return response.model_copy(
        update={
            "trace": trace.model_copy(
                update={
                    "cost_usd": aggregate_cost,
                    "quality_score": aggregate_quality,
                    "steps": costed_steps,
                    "alerts_created": len(alerts),
                }
            )
        }
    )


def _response_text(response: RevenueDeskResponse) -> str:
    recommendation = response.recommendation
    return "\n".join(
        [
            recommendation.renewal_risk_summary,
            recommendation.margin_risk_assessment,
            " ".join(recommendation.negotiation_guidance),
            recommendation.customer_facing_quote_note,
        ]
    )


def _step_record(use_case: str, step: RevenueAgentStep) -> LLMCallRecord:
    return LLMCallRecord(
        call_id=step.call_id,
        model=step.model,
        provider=Provider(step.provider),
        use_case=use_case,
        prompt_version=step.prompt_version,
        input_tokens=step.input_tokens,
        output_tokens=step.output_tokens,
        latency_ms=step.latency_ms,
        cost_usd=step.cost_usd,
        quality_score=step.quality_score,
        hallucination_flag=step.quality_score < 0.70,
        quality_gate_passed=step.quality_score >= 0.70,
        response_text=step.detail,
        context_text="\n".join(step.evidence),
    )


def _quality_score_row(record: LLMCallRecord) -> QualityScoreRow:
    quality = record.quality_score or 0.0
    return QualityScoreRow(
        timestamp=record.timestamp,
        use_case=record.use_case,
        model=record.model,
        faithfulness=max(0.0, min(1.0, quality)),
        relevance=max(0.0, min(1.0, quality + 0.02)),
        coherence=max(0.0, min(1.0, quality - 0.01)),
        composite_score=quality,
        gate_passed=bool(record.quality_gate_passed),
    )


def _drift_score(response: RevenueDeskResponse) -> float:
    prompt_factor = {
        "v1.0": 0.22,
        "v2.1": 0.14,
        "v2.2": 0.10,
    }.get(response.trace.prompt_version.value, 0.14)
    risk_factor = response.trace.margin_risk_score * 0.55
    approval_factor = (
        0.08
        if response.recommendation.approval_recommendation.value != "auto_approve"
        else 0.0
    )
    return round(min(1.0, prompt_factor + risk_factor + approval_factor), 4)


async def _ensure_prompt_versions(
    session: AsyncSession,
    model: str,
    agent_versions: list[str],
) -> None:
    use_case = "quote_to_cash_revenue_command_center"
    existing = await session.execute(
        select(PromptVersionRow.version).where(PromptVersionRow.use_case == use_case)
    )
    versions = set(existing.scalars().all())
    rows = [
        ("v1.0", "Generic quote assistant", PromptStatus.DEPRECATED),
        ("v2.1", "Margin-aware revenue agent", PromptStatus.TESTING),
        ("v2.2", "Approval-policy guarded revenue agent", PromptStatus.ACTIVE),
    ]
    rows.extend(
        (
            version,
            f"Agent prompt for {version.rsplit('.', 1)[-1].replace('_', ' ')}",
            PromptStatus.ACTIVE if version.startswith("v2.2") else PromptStatus.TESTING,
        )
        for version in agent_versions
    )
    for version, prompt_text, status in rows:
        if version in versions:
            continue
        now = datetime.now(UTC)
        session.add(
            PromptVersionRow(
                version_id=str(uuid4()),
                use_case=use_case,
                version=version,
                prompt_text=prompt_text,
                model=model,
                status=status.value,
                deployed_at=now if status is PromptStatus.ACTIVE else None,
                created_at=now,
                avg_quality_score=None,
                avg_cost_usd=None,
                avg_latency_ms=None,
            )
        )
    await session.commit()
