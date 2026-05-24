"""
Provider abstraction that executes agent prompts through local, mock, or optional
OpenAI-compatible paths.

Author: Sarala Biswal
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import httpx

from api.dependencies import Settings
from revenue_desk.models import LLMMode, LocalLLMModel, RenewalOpportunity


@dataclass(frozen=True)
class RevenueLLMResult:
    """Normalized generated text and usage metadata from any provider mode."""

    text: str
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    latency_ms: int


class RevenueLLMClient:
    """Generate quote-analysis language with mock, Ollama, or OpenAI-compatible modes."""

    def __init__(
        self,
        settings: Settings,
        mode: LLMMode | None = None,
        local_model: LocalLLMModel | None = None,
    ) -> None:
        configured_mode = mode or LLMMode(settings.llm_mode.strip().lower())
        self.mode = configured_mode
        self.settings = settings
        self.local_model = local_model.value if local_model is not None else settings.ollama_model

    async def generate_prompt(
        self,
        *,
        prompt: str,
        opportunity: RenewalOpportunity,
        mock_text: str,
        latency_offset_ms: int = 0,
    ) -> RevenueLLMResult:
        """Generate one agent prompt result with provider-specific usage metadata."""
        if self.mode is LLMMode.OLLAMA:
            return await self._generate_ollama(prompt, opportunity)
        if self.mode is LLMMode.OPENAI:
            return await self._generate_openai(prompt)
        return self._generate_mock_text(prompt, opportunity, mock_text, latency_offset_ms)

    def _generate_mock(self, prompt: str, opportunity: RenewalOpportunity) -> RevenueLLMResult:
        text = (
            f"{opportunity.account.name} should receive a guarded renewal quote for "
            f"{opportunity.name}. Anchor the negotiation on documented value, keep "
            "discounting tied to term or expansion commitments, and route the deal "
            "through approval when margin or policy flags are present."
        )
        latency_ms = _mock_latency_ms(opportunity)
        return RevenueLLMResult(
            text=text,
            model="gpt-4o-mini",
            provider="openai",
            input_tokens=_estimate_tokens(prompt),
            output_tokens=_estimate_tokens(text),
            latency_ms=latency_ms,
        )

    def _generate_mock_text(
        self,
        prompt: str,
        opportunity: RenewalOpportunity,
        text: str,
        latency_offset_ms: int,
    ) -> RevenueLLMResult:
        return RevenueLLMResult(
            text=text,
            model="gpt-4o-mini",
            provider="openai",
            input_tokens=_estimate_tokens(prompt),
            output_tokens=_estimate_tokens(text),
            latency_ms=max(120, _mock_latency_ms(opportunity) + latency_offset_ms),
        )

    async def _generate_ollama(
        self,
        prompt: str,
        opportunity: RenewalOpportunity,
    ) -> RevenueLLMResult:
        start = time.perf_counter()
        model = self.local_model
        url = f"{self.settings.ollama_base_url.rstrip('/')}/api/generate"
        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                response = await client.post(
                    url,
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "keep_alive": "5m",
                        "options": {"num_predict": 64, "temperature": 0.1},
                    },
                )
                response.raise_for_status()
                payload = response.json()
                text = str(payload.get("response") or "").strip()
        except Exception:
            fallback = self._generate_mock(prompt, opportunity)
            return RevenueLLMResult(
                text=fallback.text,
                model=model,
                provider="ollama",
                input_tokens=fallback.input_tokens,
                output_tokens=fallback.output_tokens,
                latency_ms=fallback.latency_ms,
            )
        latency_ms = int((time.perf_counter() - start) * 1000)
        return RevenueLLMResult(
            text=text or "Ollama returned an empty response; use deterministic recommendation.",
            model=model,
            provider="ollama",
            input_tokens=_estimate_tokens(prompt),
            output_tokens=_estimate_tokens(text),
            latency_ms=latency_ms,
        )

    async def _generate_openai(self, prompt: str) -> RevenueLLMResult:
        if not self.settings.has_openai_api_key:
            fallback = self._generate_mock(prompt, _fallback_opportunity())
            return RevenueLLMResult(
                text=fallback.text,
                model=self.settings.litellm_model,
                provider="openai",
                input_tokens=fallback.input_tokens,
                output_tokens=fallback.output_tokens,
                latency_ms=fallback.latency_ms,
            )

        start = time.perf_counter()
        try:
            from litellm import acompletion

            response = await acompletion(
                model=self.settings.litellm_model,
                messages=[{"role": "user", "content": prompt}],
                api_key=self.settings.openai_api_key,
            )
            text = str(response.choices[0].message.content or "")
        except Exception:
            fallback = self._generate_mock(prompt, _fallback_opportunity())
            return RevenueLLMResult(
                text=fallback.text,
                model=self.settings.litellm_model,
                provider="openai",
                input_tokens=fallback.input_tokens,
                output_tokens=fallback.output_tokens,
                latency_ms=fallback.latency_ms,
            )

        latency_ms = int((time.perf_counter() - start) * 1000)
        return RevenueLLMResult(
            text=text,
            model=self.settings.litellm_model,
            provider="openai",
            input_tokens=_estimate_tokens(prompt),
            output_tokens=_estimate_tokens(text),
            latency_ms=latency_ms,
        )


def _estimate_tokens(text: str) -> int:
    return max(1, round(len(text.split()) * 1.25))


def _mock_latency_ms(opportunity: RenewalOpportunity) -> int:
    risk_weight = {
        "low": 0,
        "medium": 160,
        "high": 310,
        "critical": 430,
    }.get(opportunity.renewal_risk.value, 120)
    approval_weight = len(opportunity.approval_flags) * 45
    evidence_weight = len(opportunity.grounded_evidence) * 18
    return 420 + risk_weight + approval_weight + evidence_weight


def _fallback_opportunity() -> RenewalOpportunity:
    from revenue_desk.catalog import list_opportunities

    return list_opportunities()[0]
