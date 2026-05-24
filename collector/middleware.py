"""
SDK and middleware entry points that instrument external LLM application calls.

Author: Sarala Biswal
"""

import asyncio
import time
from collections.abc import Awaitable, Callable
from uuid import uuid4

import httpx
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp


class ObservabilityMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        collector_url: str = "http://localhost:9100",
        use_case: str = "default",
        enable_quality_scoring: bool = True,
    ) -> None:
        super().__init__(app)
        self.collector_url = collector_url.rstrip("/")
        self.use_case = use_case
        self.enable_quality_scoring = enable_quality_scoring

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        started = time.perf_counter()
        response = await call_next(request)
        latency_ms = int((time.perf_counter() - started) * 1000)
        if _looks_like_llm_endpoint(request):
            asyncio.create_task(self._post_call(request, response, latency_ms))
        return response

    async def _post_call(self, request: Request, response: Response, latency_ms: int) -> None:
        payload = {
            "call_id": str(uuid4()),
            "model": request.headers.get("x-llm-model", "gpt-4o-mini"),
            "provider": request.headers.get("x-llm-provider", "openai"),
            "use_case": self.use_case,
            "prompt_version": request.headers.get("x-prompt-version", "unknown"),
            "input_tokens": int(request.headers.get("x-input-tokens", "1")),
            "output_tokens": int(request.headers.get("x-output-tokens", "1")),
            "latency_ms": latency_ms,
            "cost_usd": "0.0",
            "response_text": f"HTTP {response.status_code} from {request.url.path}",
            "context_text": request.url.path,
        }
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                await client.post(f"{self.collector_url}/ingest", json=payload)
        except Exception:
            return


def _looks_like_llm_endpoint(request: Request) -> bool:
    path = request.url.path.lower()
    return "llm" in path or "chat" in path or "completion" in path or "generate" in path
