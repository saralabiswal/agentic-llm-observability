"""
Quality gates, hallucination checks, and judge-backed scoring for production LLM output.

Author: Sarala Biswal
"""

import json
import logging

import litellm

from api.dependencies import AppMode, Settings, get_settings

logger = logging.getLogger(__name__)


class HallucinationDetector:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def detect(self, response: str, context: str) -> bool | None:
        if self.settings.app_mode == AppMode.DEMO:
            return self._demo_detect(response, context)
        return await self._real_detect(response, context)

    @staticmethod
    def _demo_detect(response: str, context: str) -> bool:
        response_lower = response.lower()
        context_lower = context.lower()
        if not response.strip():
            return False
        if "unsupported" in response_lower or "hallucinated" in response_lower:
            return True
        return len(response_lower) > 20 and response_lower not in context_lower

    async def _real_detect(self, response: str, context: str) -> bool | None:
        try:
            completion = await litellm.acompletion(
                model=self.settings.litellm_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You detect whether an LLM response is grounded in the "
                            "provided context. "
                            "Return only JSON."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Context: {context}\nResponse: {response}\n"
                            'Return ONLY: {"hallucination": true} or {"hallucination": false}'
                        ),
                    },
                ],
            )
            content = completion.choices[0].message.content or "{}"
            payload = json.loads(content)
            return bool(payload["hallucination"])
        except Exception:
            logger.exception("Hallucination detector failed")
            return None
