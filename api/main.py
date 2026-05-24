"""
API bootstrap, settings, schemas, and shared dependency wiring for the observability
service.

Author: Sarala Biswal
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_engine, get_session
from api.routers import alerts, costs, drift, ingest, latency, prompts, quality, revenue_desk
from audit.models import AlertHistory, Base, LLMCall


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="agentic-llm-observability", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(ingest.router)
app.include_router(costs.router)
app.include_router(quality.router)
app.include_router(latency.router)
app.include_router(prompts.router)
app.include_router(drift.router)
app.include_router(alerts.router)
app.include_router(revenue_desk.router)


@app.get("/health")
async def health(session: Annotated[AsyncSession, Depends(get_session)]) -> dict[str, str]:
    await session.execute(select(1))
    return {"status": "ok", "db": "ok", "version": "0.1.0"}


@app.get("/metrics")
async def metrics(session: Annotated[AsyncSession, Depends(get_session)]) -> Response:
    total_calls = await session.scalar(select(func.count(LLMCall.call_id)))
    total_cost = await session.scalar(select(func.coalesce(func.sum(LLMCall.cost_usd), 0)))
    active_alerts = await session.scalar(
        select(func.count(AlertHistory.alert_id)).where(AlertHistory.resolved.is_(False))
    )
    body = "\n".join(
        [
            "# HELP llm_calls_total Total observed LLM calls.",
            "# TYPE llm_calls_total counter",
            f"llm_calls_total {int(total_calls or 0)}",
            "# HELP llm_cost_usd_total Total observed LLM cost in USD.",
            "# TYPE llm_cost_usd_total counter",
            f"llm_cost_usd_total {float(total_cost or 0):.6f}",
            "# HELP active_alerts Current unresolved alerts.",
            "# TYPE active_alerts gauge",
            f"active_alerts {int(active_alerts or 0)}",
            "",
        ]
    )
    return Response(content=body, media_type="text/plain; version=0.0.4")
