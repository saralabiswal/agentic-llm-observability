"""
Quote-to-Cash domain catalog, policy, and model layer used by the agentic flow.

Author: Sarala Biswal
"""

from revenue_desk.catalog import get_opportunity, list_opportunities
from revenue_desk.service import RevenueCommandCenterService

__all__ = ["RevenueCommandCenterService", "get_opportunity", "list_opportunities"]
