"""
Regression tests that keep the API, telemetry math, and Quote-to-Cash flow behavior
honest.

Author: Sarala Biswal
"""

import pytest

from api.dependencies import AppMode, Settings
from api.schemas import QualityScore
from quality.hallucination_detector import HallucinationDetector
from quality.llm_judge import JudgeInput, LLMJudge
from quality.quality_gate import QualityGate


@pytest.mark.asyncio
async def test_demo_judge_scores_are_in_range() -> None:
    judge = LLMJudge(Settings(app_mode=AppMode.DEMO))

    score = await judge.score(
        JudgeInput(
            use_case="banking_payment_risk",
            model="gpt-4o-mini",
            prompt="Assess the payment.",
            response="The payment should be reviewed because the risk score is high.",
            context="The payment should be reviewed because the risk score is high.",
        )
    )

    assert score is not None
    assert 0.0 <= score.faithfulness <= 1.0
    assert 0.0 <= score.relevance <= 1.0
    assert 0.0 <= score.coherence <= 1.0
    assert 0.0 <= score.composite_score <= 1.0
    assert score.gate_passed


def test_quality_gate_pass_fail() -> None:
    gate = QualityGate(
        Settings(app_mode=AppMode.DEMO, quality_gate_threshold=0.70),
        thresholds_by_use_case={"strict_case": 0.90},
    )
    passing = QualityScore(
        use_case="default_case",
        model="gpt-4o-mini",
        faithfulness=0.8,
        relevance=0.8,
        coherence=0.8,
        gate_passed=False,
    )
    failing = QualityScore(
        use_case="strict_case",
        model="gpt-4o-mini",
        faithfulness=0.8,
        relevance=0.8,
        coherence=0.8,
        gate_passed=False,
    )

    assert gate.evaluate(passing, "default_case")
    assert not gate.evaluate(failing, "strict_case")


@pytest.mark.asyncio
async def test_hallucination_detector_demo_flags_unsupported_response() -> None:
    detector = HallucinationDetector(Settings(app_mode=AppMode.DEMO))

    flagged = await detector.detect("This is an unsupported claim.", "Only grounded facts.")

    assert flagged is True


@pytest.mark.asyncio
async def test_real_judge_failure_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    async def raise_error(*args, **kwargs):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr("quality.llm_judge.litellm.acompletion", raise_error)
    judge = LLMJudge(Settings(app_mode=AppMode.REAL))

    score = await judge.score(
        JudgeInput(
            use_case="banking_payment_risk",
            model="gpt-4o-mini",
            prompt="Prompt",
            response="Response",
            context="Context",
        )
    )

    assert score is None
