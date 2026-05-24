"""
Agent chain definitions for the Quote-to-Cash flow, including prompt construction per
step.

Author: Sarala Biswal
"""

from dataclasses import dataclass
from uuid import uuid4

from revenue_desk.llm import RevenueLLMClient, RevenueLLMResult
from revenue_desk.models import (
    RenewalOpportunity,
    RevenueAgentStep,
    RevenuePromptVersion,
)


@dataclass(frozen=True)
class RevenueAgent:
    agent_name: str
    prompt_name: str
    label: str
    system: str
    step_id: str
    latency_offset_ms: int

    async def run(
        self,
        *,
        client: RevenueLLMClient,
        opportunity: RenewalOpportunity,
        prompt_version: RevenuePromptVersion,
        prompt_context: str,
        mock_text: str,
        detail: str,
        evidence: list[str],
        quality_score: float,
    ) -> RevenueAgentStep:
        prompt_id = f"{prompt_version.value}.{self.prompt_name}"
        prompt = _build_agent_prompt(
            agent=self,
            opportunity=opportunity,
            prompt_version=prompt_version,
            prompt_context=prompt_context,
        )
        result = await client.generate_prompt(
            prompt=prompt,
            opportunity=opportunity,
            mock_text=mock_text,
            latency_offset_ms=self.latency_offset_ms,
        )
        return _to_step(
            agent=self,
            result=result,
            prompt_id=prompt_id,
            detail=detail,
            evidence=evidence,
            quality_score=quality_score,
        )


OPPORTUNITY_CONTEXT_AGENT = RevenueAgent(
    agent_name="Opportunity Context Agent",
    prompt_name="context",
    label="Load opportunity context",
    system="Revenue CRM",
    step_id="crm_context",
    latency_offset_ms=-150,
)

DISCOUNT_POLICY_AGENT = RevenueAgent(
    agent_name="Discount Policy Agent",
    prompt_name="discount_policy",
    label="Apply discount policy",
    system="Revenue Policy",
    step_id="policy_check",
    latency_offset_ms=-70,
)

MARGIN_RISK_AGENT = RevenueAgent(
    agent_name="Margin Risk Agent",
    prompt_name="margin_risk",
    label="Assess margin risk",
    system="CPQ Pricing",
    step_id="margin_assessment",
    latency_offset_ms=20,
)

APPROVAL_ROUTING_AGENT = RevenueAgent(
    agent_name="Approval Routing Agent",
    prompt_name="approval_route",
    label="Select approval route",
    system="Deal Desk",
    step_id="approval_route",
    latency_offset_ms=90,
)

NEGOTIATION_GUIDANCE_AGENT = RevenueAgent(
    agent_name="Negotiation Guidance Agent",
    prompt_name="negotiation_guidance",
    label="Draft negotiation guidance",
    system="Revenue Agent",
    step_id="negotiation_guidance",
    latency_offset_ms=180,
)

REVENUE_AGENTS: tuple[RevenueAgent, ...] = (
    OPPORTUNITY_CONTEXT_AGENT,
    DISCOUNT_POLICY_AGENT,
    MARGIN_RISK_AGENT,
    APPROVAL_ROUTING_AGENT,
    NEGOTIATION_GUIDANCE_AGENT,
)


def build_agent_prompt(
    *,
    agent: RevenueAgent,
    opportunity: RenewalOpportunity,
    prompt_version: RevenuePromptVersion,
    prompt_context: str,
) -> str:
    """Build the same prompt text used when an agent runs in the Quote-to-Cash flow."""
    return _build_agent_prompt(
        agent=agent,
        opportunity=opportunity,
        prompt_version=prompt_version,
        prompt_context=prompt_context,
    )


def _build_agent_prompt(
    *,
    agent: RevenueAgent,
    opportunity: RenewalOpportunity,
    prompt_version: RevenuePromptVersion,
    prompt_context: str,
) -> str:
    evidence = "\n".join(f"- {item}" for item in opportunity.grounded_evidence)
    flags = ", ".join(opportunity.approval_flags)
    return (
        f"Agent: {agent.agent_name}\n"
        f"Prompt: {prompt_version.value}.{agent.prompt_name}\n"
        f"Account: {opportunity.account.name}\n"
        f"Opportunity: {opportunity.name}\n"
        f"Scenario: {opportunity.scenario}\n"
        f"ARR: {opportunity.arr_usd}\n"
        f"Expansion ARR: {opportunity.expansion_arr_usd}\n"
        f"Requested discount: {opportunity.requested_discount_pct}%\n"
        f"Current discount: {opportunity.current_discount_pct}%\n"
        f"Target margin: {opportunity.target_margin_pct}%\n"
        f"Current margin: {opportunity.current_margin_pct}%\n"
        f"Renewal risk: {opportunity.renewal_risk.value}\n"
        f"Approval flags: {flags}\n"
        f"Evidence:\n{evidence}\n"
        f"Task context: {prompt_context}"
    )


def _to_step(
    *,
    agent: RevenueAgent,
    result: RevenueLLMResult,
    prompt_id: str,
    detail: str,
    evidence: list[str],
    quality_score: float,
) -> RevenueAgentStep:
    return RevenueAgentStep(
        step_id=agent.step_id,
        label=agent.label,
        system=agent.system,
        agent_name=agent.agent_name,
        prompt_name=agent.prompt_name,
        prompt_version=prompt_id,
        call_id=f"rcc-{agent.prompt_name}-{uuid4()}",
        model=result.model,
        provider=result.provider,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        latency_ms=result.latency_ms,
        quality_score=quality_score,
        status="completed",
        detail=detail,
        evidence=evidence,
    )
