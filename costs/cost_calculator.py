"""
Cost attribution, provider rate cards, and optimization logic for token economics.

Author: Sarala Biswal
"""

from decimal import Decimal

from api.schemas import Provider
from costs.provider_models import PROVIDER_COSTS

TOKENS_PER_MILLION = Decimal("1000000")


class CostCalculator:
    def calculate_call_cost(
        self,
        model: str,
        provider: Provider,
        input_tokens: int,
        output_tokens: int,
    ) -> Decimal:
        if input_tokens < 0 or output_tokens < 0:
            raise ValueError("Token counts must be non-negative")

        try:
            rates = PROVIDER_COSTS[provider.value][model]
        except KeyError as exc:
            message = f"Unknown provider/model combination: {provider.value}/{model}"
            raise ValueError(message) from exc

        input_cost = rates["input"] * Decimal(input_tokens) / TOKENS_PER_MILLION
        output_cost = rates["output"] * Decimal(output_tokens) / TOKENS_PER_MILLION
        return (input_cost + output_cost).quantize(Decimal("0.000001"))


def calculate_call_cost(
    model: str,
    provider: Provider,
    input_tokens: int,
    output_tokens: int,
) -> Decimal:
    return CostCalculator().calculate_call_cost(model, provider, input_tokens, output_tokens)
