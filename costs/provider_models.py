"""
Cost attribution, provider rate cards, and optimization logic for token economics.

Author: Sarala Biswal
"""

from decimal import Decimal
from typing import Final, TypedDict


class ModelRates(TypedDict):
    input: Decimal
    output: Decimal


CostTable = dict[str, dict[str, ModelRates]]

PROVIDER_COSTS_VERSION: Final = "2026-05-23"

PROVIDER_COSTS: Final[CostTable] = {
    "openai": {
        "gpt-4o": {"input": Decimal("2.50"), "output": Decimal("10.00")},
        "gpt-4o-mini": {"input": Decimal("0.15"), "output": Decimal("0.60")},
        "gpt-4.1": {"input": Decimal("2.00"), "output": Decimal("8.00")},
        "gpt-4.1-mini": {"input": Decimal("0.40"), "output": Decimal("1.60")},
        "o1": {"input": Decimal("15.00"), "output": Decimal("60.00")},
        "o3": {"input": Decimal("10.00"), "output": Decimal("40.00")},
    },
    "anthropic": {
        "claude-3-5-sonnet-20241022": {
            "input": Decimal("3.00"),
            "output": Decimal("15.00"),
        },
        "claude-3-5-haiku-20241022": {
            "input": Decimal("0.80"),
            "output": Decimal("4.00"),
        },
        "claude-opus-4-20250514": {
            "input": Decimal("15.00"),
            "output": Decimal("75.00"),
        },
    },
    "azure": {
        "gpt-4o": {"input": Decimal("2.75"), "output": Decimal("11.00")},
        "gpt-4o-mini": {"input": Decimal("0.165"), "output": Decimal("0.66")},
    },
    "ollama": {
        "llama3.2": {"input": Decimal("0.20"), "output": Decimal("0.20")},
        "mistral": {"input": Decimal("0.18"), "output": Decimal("0.18")},
        "qwen2.5:7b": {"input": Decimal("0.24"), "output": Decimal("0.24")},
    },
}
