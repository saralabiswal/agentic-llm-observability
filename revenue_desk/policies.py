"""
Quote-to-Cash domain catalog, policy, and model layer used by the agentic flow.

Author: Sarala Biswal
"""

from dataclasses import dataclass

from revenue_desk.models import RenewalOpportunity


@dataclass(frozen=True)
class RevenuePolicySource:
    policy_id: str
    title: str
    owner: str
    version: str
    source: str
    rules: list[str]


def policy_for_prompt(prompt_name: str, opportunity: RenewalOpportunity) -> RevenuePolicySource:
    policies = {
        "context": _context_policy(opportunity),
        "discount_policy": _discount_policy(opportunity),
        "margin_risk": _margin_policy(opportunity),
        "approval_route": _approval_policy(opportunity),
        "negotiation_guidance": _negotiation_policy(opportunity),
    }
    return policies[prompt_name]


def _context_policy(opportunity: RenewalOpportunity) -> RevenuePolicySource:
    return RevenuePolicySource(
        policy_id="REV-CTX-2026.05",
        title="Opportunity Evidence Context Policy",
        owner="Revenue Operations",
        version="2026.05",
        source="CRM account health, opportunity state, success plan, and grounded evidence",
        rules=[
            (
                f"Use account health score {opportunity.account.customer_health} as the "
                "primary renewal context signal."
            ),
            f"Treat renewal risk '{opportunity.renewal_risk.value}' as a required decision input.",
            "Ground every recommendation in account, opportunity, or success-plan evidence.",
            "Do not introduce customer claims that are not present in grounded evidence.",
        ],
    )


def _discount_policy(opportunity: RenewalOpportunity) -> RevenuePolicySource:
    policy_cap = _policy_discount_cap(opportunity)
    return RevenuePolicySource(
        policy_id="REV-DISC-2026.05",
        title="Commercial Discount Policy",
        owner="Deal Desk",
        version="2026.05",
        source="Discount policy engine and opportunity commercial terms",
        rules=[
            "Base discount authority starts at 12%.",
            "Add 6 points for terms of 36 months or longer.",
            "Add 4 points when expansion ARR is at least $250,000.",
            "Subtract 3 points when current margin is below target margin.",
            f"For this opportunity, the calculated policy cap is {policy_cap:.1f}%.",
            (
                f"Requested discount is {opportunity.requested_discount_pct:.1f}%; "
                f"current discount is {opportunity.current_discount_pct:.1f}%."
            ),
        ],
    )


def _margin_policy(opportunity: RenewalOpportunity) -> RevenuePolicySource:
    return RevenuePolicySource(
        policy_id="REV-MARGIN-2026.05",
        title="Gross Margin Protection Policy",
        owner="Finance",
        version="2026.05",
        source="CPQ margin model and revenue finance guardrails",
        rules=[
            f"Target margin for this quote is {opportunity.target_margin_pct:.1f}%.",
            f"Current margin before new concession is {opportunity.current_margin_pct:.1f}%.",
            "Expected margin is estimated as current margin minus 0.28 times recommended discount.",
            "Never project expected margin below 35%.",
            "Flag margin risk when expected margin is below target or close to approval floor.",
        ],
    )


def _approval_policy(opportunity: RenewalOpportunity) -> RevenuePolicySource:
    return RevenuePolicySource(
        policy_id="REV-APPROVAL-2026.05",
        title="Quote Approval Routing Policy",
        owner="Revenue Governance",
        version="2026.05",
        source="Deal Desk approval matrix",
        rules=[
            (
                "Executive review is required for critical renewal risk or expected "
                "margin below target minus 8 points."
            ),
            "Approval is required when discount is at least 20%.",
            "Approval is required when expected margin is below target margin.",
            "Approval is required when two or more approval flags are present.",
            (
                f"This opportunity has {len(opportunity.approval_flags)} approval "
                f"flag(s): {', '.join(opportunity.approval_flags) or 'none'}."
            ),
        ],
    )


def _negotiation_policy(opportunity: RenewalOpportunity) -> RevenuePolicySource:
    return RevenuePolicySource(
        policy_id="REV-NEGOTIATION-2026.05",
        title="Customer-Facing Negotiation Guidance Policy",
        owner="Sales Leadership",
        version="2026.05",
        source="Sales playbook and success-plan evidence",
        rules=[
            "Lead with the business scenario and documented customer value.",
            (
                "Tie concessions to term length, scope, expansion ARR, or support "
                "remediation milestones."
            ),
            "Do not commit customer-facing terms before required approval route is complete.",
            "Use success-plan and grounded-evidence language in the customer-facing quote note.",
            f"Scenario for this opportunity is '{opportunity.scenario.replace('_', ' ')}'.",
        ],
    )


def _policy_discount_cap(opportunity: RenewalOpportunity) -> float:
    base = 12.0
    if opportunity.contract_terms_months >= 36:
        base += 6.0
    if opportunity.expansion_arr_usd >= 250000:
        base += 4.0
    if opportunity.current_margin_pct < opportunity.target_margin_pct:
        base -= 3.0
    return max(8.0, base)
