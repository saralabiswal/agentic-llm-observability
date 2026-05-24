"""
Regression tests that keep the API, telemetry math, and Quote-to-Cash flow behavior
honest.

Author: Sarala Biswal
"""

from decimal import Decimal

import pytest

from api.schemas import Provider
from costs.cost_calculator import CostCalculator
from costs.provider_models import PROVIDER_COSTS


@pytest.mark.parametrize(
    ("provider", "model"),
    [
        (Provider(provider_name), model_name)
        for provider_name, models in PROVIDER_COSTS.items()
        for model_name in models
    ],
)
def test_all_provider_model_combinations_return_expected_cost(
    provider: Provider,
    model: str,
) -> None:
    calculator = CostCalculator()
    rates = PROVIDER_COSTS[provider.value][model]

    cost = calculator.calculate_call_cost(
        model=model,
        provider=provider,
        input_tokens=1_000_000,
        output_tokens=1_000_000,
    )

    assert cost == (rates["input"] + rates["output"]).quantize(Decimal("0.000001"))


def test_unknown_model_raises_value_error() -> None:
    calculator = CostCalculator()

    with pytest.raises(ValueError, match="Unknown provider/model combination"):
        calculator.calculate_call_cost(
            model="unknown-model",
            provider=Provider.OPENAI,
            input_tokens=100,
            output_tokens=100,
        )


def test_negative_token_count_raises_value_error() -> None:
    calculator = CostCalculator()

    with pytest.raises(ValueError, match="Token counts must be non-negative"):
        calculator.calculate_call_cost(
            model="gpt-4o-mini",
            provider=Provider.OPENAI,
            input_tokens=-1,
            output_tokens=100,
        )
