"""
Quote-to-Cash domain catalog, policy, and model layer used by the agentic flow.

Author: Sarala Biswal
"""

from decimal import Decimal

from revenue_desk.models import Account, ProductTier, RenewalOpportunity, RenewalRisk

_ACCOUNTS = {
    "ACC-001": Account(
        account_id="ACC-001",
        name="Northstar Telecom",
        segment="Strategic Enterprise",
        industry="Telecommunications",
        region="North America",
        customer_health=84,
        executive_sponsor="VP Network Operations",
    ),
    "ACC-002": Account(
        account_id="ACC-002",
        name="MetroWave Communications",
        segment="Enterprise",
        industry="Telecommunications",
        region="EMEA",
        customer_health=52,
        executive_sponsor="Chief Revenue Officer",
    ),
    "ACC-003": Account(
        account_id="ACC-003",
        name="Apex Mobile Networks",
        segment="Strategic Enterprise",
        industry="Telecommunications",
        region="APAC",
        customer_health=69,
        executive_sponsor="CTO",
    ),
    "ACC-004": Account(
        account_id="ACC-004",
        name="BluePeak Fiber",
        segment="Mid-Market",
        industry="Broadband",
        region="North America",
        customer_health=77,
        executive_sponsor="Director of Infrastructure",
    ),
    "ACC-005": Account(
        account_id="ACC-005",
        name="HelioLink Wireless",
        segment="Enterprise",
        industry="Wireless",
        region="LATAM",
        customer_health=61,
        executive_sponsor="Head of Procurement",
    ),
}


_OPPORTUNITIES = (
    RenewalOpportunity(
        opportunity_id="RCC-OPP-001",
        account=_ACCOUNTS["ACC-001"],
        scenario="enterprise_expansion",
        name="5G Edge Platform Expansion",
        stage="Solution Validation",
        arr_usd=Decimal("1250000"),
        expansion_arr_usd=Decimal("420000"),
        current_discount_pct=14.0,
        requested_discount_pct=18.0,
        target_margin_pct=68.0,
        current_margin_pct=71.0,
        renewal_risk=RenewalRisk.LOW,
        product_tier=ProductTier.STRATEGIC,
        contract_terms_months=36,
        close_date="2026-06-30",
        approval_flags=["expansion_arr", "multi_year_commit"],
        pain_points=[
            "Edge capacity is constrained in 12 metro zones.",
            "Operations team wants one management plane for core and edge storage.",
        ],
        success_plan=[
            "Bundle expansion with renewal to preserve account momentum.",
            "Use 36-month term incentive instead of a deeper discount.",
        ],
        grounded_evidence=[
            "Health score 84 with two successful production go-lives in the last 90 days.",
            "Customer approved a 12-site edge rollout business case for Q3.",
            "Procurement accepted a 36-month framework if discount stays below 20%.",
        ],
    ),
    RenewalOpportunity(
        opportunity_id="RCC-OPP-002",
        account=_ACCOUNTS["ACC-002"],
        scenario="renewal_at_risk",
        name="Core Billing Platform Renewal",
        stage="Commercial Review",
        arr_usd=Decimal("890000"),
        expansion_arr_usd=Decimal("0"),
        current_discount_pct=11.0,
        requested_discount_pct=26.0,
        target_margin_pct=64.0,
        current_margin_pct=58.0,
        renewal_risk=RenewalRisk.HIGH,
        product_tier=ProductTier.ENTERPRISE,
        contract_terms_months=24,
        close_date="2026-05-28",
        approval_flags=["high_discount", "margin_below_target", "renewal_risk"],
        pain_points=[
            "Open severity-two support escalation from the billing migration.",
            "Competitor quote is positioned as 19% lower on first-year cost.",
        ],
        success_plan=[
            "Tie discount concession to support remediation milestones.",
            "Add executive sponsor checkpoint before procurement final round.",
        ],
        grounded_evidence=[
            "Support case CS-4481 has been open for 21 days.",
            "Customer health dropped from 71 to 52 over the last quarter.",
            "Requested 26% discount would keep expected margin below target.",
        ],
    ),
    RenewalOpportunity(
        opportunity_id="RCC-OPP-003",
        account=_ACCOUNTS["ACC-005"],
        scenario="discount_pressure",
        name="Wireless Analytics Contract Reset",
        stage="Negotiation",
        arr_usd=Decimal("640000"),
        expansion_arr_usd=Decimal("75000"),
        current_discount_pct=18.0,
        requested_discount_pct=32.0,
        target_margin_pct=62.0,
        current_margin_pct=65.0,
        renewal_risk=RenewalRisk.MEDIUM,
        product_tier=ProductTier.PROFESSIONAL,
        contract_terms_months=24,
        close_date="2026-06-18",
        approval_flags=["procurement_pressure", "requested_discount_above_policy"],
        pain_points=[
            "Procurement is benchmarking against a cloud-only analytics bundle.",
            "Regional budget owner wants flat year-one spend despite added scope.",
        ],
        success_plan=[
            "Offer ramped pricing instead of approving the full discount request.",
            "Package analytics onboarding credits with a smaller discount.",
        ],
        grounded_evidence=[
            "Procurement asked for 32% discount in the latest redline.",
            "Expansion scope adds two analytics workloads and one managed service.",
            "Policy allows 22% discount before revenue leadership approval.",
        ],
    ),
    RenewalOpportunity(
        opportunity_id="RCC-OPP-004",
        account=_ACCOUNTS["ACC-004"],
        scenario="margin_protection",
        name="Fiber OSS Data Platform Renewal",
        stage="Proposal",
        arr_usd=Decimal("520000"),
        expansion_arr_usd=Decimal("0"),
        current_discount_pct=9.0,
        requested_discount_pct=20.0,
        target_margin_pct=66.0,
        current_margin_pct=60.0,
        renewal_risk=RenewalRisk.LOW,
        product_tier=ProductTier.STANDARD,
        contract_terms_months=12,
        close_date="2026-07-10",
        approval_flags=["margin_protection"],
        pain_points=[
            "Customer wants a short renewal while they evaluate OSS modernization.",
            "Services attachment is low, leaving limited margin cushion.",
        ],
        success_plan=[
            "Protect margin with a smaller discount and attach support uplift.",
            "Position a 24-month option as the path to unlock deeper pricing.",
        ],
        grounded_evidence=[
            "Current margin is six points below target before any new concession.",
            "No competitive displacement risk has been documented by the account team.",
            "Customer health is 77 with stable platform usage.",
        ],
    ),
    RenewalOpportunity(
        opportunity_id="RCC-OPP-005",
        account=_ACCOUNTS["ACC-003"],
        scenario="multi_product_upsell",
        name="National CDR Retention and AI Ops Upsell",
        stage="Business Case",
        arr_usd=Decimal("1480000"),
        expansion_arr_usd=Decimal("680000"),
        current_discount_pct=16.0,
        requested_discount_pct=23.0,
        target_margin_pct=67.0,
        current_margin_pct=69.0,
        renewal_risk=RenewalRisk.MEDIUM,
        product_tier=ProductTier.STRATEGIC,
        contract_terms_months=48,
        close_date="2026-09-30",
        approval_flags=["multi_product", "strategic_expansion", "long_term_commit"],
        pain_points=[
            "Regulated CDR retention must scale across national network regions.",
            "AI operations team needs searchable telemetry history for incident response.",
        ],
        success_plan=[
            "Anchor discount to a four-year multi-product commitment.",
            "Use governance evidence to justify premium support attachment.",
        ],
        grounded_evidence=[
            "Customer requires regulated retention for 16 regional network domains.",
            "Architecture review approved object storage plus AI Ops management bundle.",
            "Four-year commitment supports a moderate discount while preserving margin.",
        ],
    ),
)


def list_opportunities() -> list[RenewalOpportunity]:
    """Return all deterministic Revenue Command Center opportunities."""
    return list(_OPPORTUNITIES)


def get_opportunity(opportunity_id: str) -> RenewalOpportunity | None:
    """Return one deterministic opportunity by id."""
    return next(
        (
            opportunity
            for opportunity in _OPPORTUNITIES
            if opportunity.opportunity_id == opportunity_id
        ),
        None,
    )
