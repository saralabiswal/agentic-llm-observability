"""
Quality gates, hallucination checks, and judge-backed scoring for production LLM output.

Author: Sarala Biswal
"""

import json
import logging
from dataclasses import dataclass

import litellm

from api.dependencies import AppMode, Settings, get_settings
from api.schemas import QualityScore

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class JudgeInput:
    use_case: str
    model: str
    prompt: str
    response: str
    context: str


class LLMJudge:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def score(self, judge_input: JudgeInput) -> QualityScore | None:
        if self.settings.app_mode == AppMode.DEMO:
            return self._demo_score(judge_input)
        return await self._real_score(judge_input)

    def _demo_score(self, judge_input: JudgeInput) -> QualityScore:
        response_lower = judge_input.response.lower()
        context_lower = judge_input.context.lower()
        if "unsupported" in response_lower or "hallucinated" in response_lower:
            faithfulness = 0.48
        elif response_lower and response_lower in context_lower:
            faithfulness = 0.92
        else:
            faithfulness = 0.84

        relevance = 0.88 if judge_input.prompt else 0.70
        coherence = 0.86 if len(judge_input.response.split()) >= 4 else 0.72
        quality = QualityScore(
            use_case=judge_input.use_case,
            model=judge_input.model,
            faithfulness=faithfulness,
            relevance=relevance,
            coherence=coherence,
            gate_passed=False,
        )
        return quality.model_copy(update={"gate_passed": quality.composite_score >= 0.70})

    async def _real_score(self, judge_input: JudgeInput) -> QualityScore | None:
        try:
            response = await litellm.acompletion(
                model=self.settings.litellm_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a quality evaluator for LLM responses. "
                            "Return only JSON with faithfulness, relevance, and coherence scores."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Context: {judge_input.context}\n"
                            f"Question/Prompt: {judge_input.prompt}\n"
                            f"Response to evaluate: {judge_input.response}\n"
                            'Return ONLY: {"faithfulness": 0.0, "relevance": 0.0, "coherence": 0.0}'
                        ),
                    },
                ],
            )
            content = response.choices[0].message.content or "{}"
            payload = json.loads(content)
            quality = QualityScore(
                use_case=judge_input.use_case,
                model=judge_input.model,
                faithfulness=float(payload["faithfulness"]),
                relevance=float(payload["relevance"]),
                coherence=float(payload["coherence"]),
                gate_passed=False,
            )
            return quality.model_copy(
                update={
                    "gate_passed": (
                        quality.composite_score >= self.settings.quality_gate_threshold
                    )
                }
            )
        except Exception:
            logger.exception("LLM judge failed")
            return None
