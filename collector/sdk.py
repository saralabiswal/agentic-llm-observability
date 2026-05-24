"""
SDK and middleware entry points that instrument external LLM application calls.

Author: Sarala Biswal
"""

import asyncio
import functools
from collections.abc import Awaitable, Callable
from typing import ParamSpec, TypeVar
from uuid import uuid4

import httpx

P = ParamSpec("P")
R = TypeVar("R")


def track_llm_call(
    *,
    use_case: str,
    prompt_version: str,
    collector_url: str = "http://localhost:9100",
    model: str = "gpt-4o-mini",
    provider: str = "openai",
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            result = await func(*args, **kwargs)
            response_text = str(result)
            payload = {
                "call_id": str(uuid4()),
                "model": model,
                "provider": provider,
                "use_case": use_case,
                "prompt_version": prompt_version,
                "input_tokens": _estimate_tokens(str(args) + str(kwargs)),
                "output_tokens": _estimate_tokens(response_text),
                "latency_ms": 0,
                "cost_usd": "0.0",
                "response_text": response_text,
                "context_text": str(kwargs.get("context", "")),
            }
            asyncio.create_task(_post_ingest(collector_url, payload))
            return result

        return wrapper

    return decorator


async def _post_ingest(collector_url: str, payload: dict[str, object]) -> None:
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            await client.post(f"{collector_url.rstrip('/')}/ingest", json=payload)
    except Exception:
        return


def _estimate_tokens(text: str) -> int:
    return max(1, len(text.split()) + len(text) // 4)
