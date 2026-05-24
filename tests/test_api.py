"""
Regression tests that keep the API, telemetry math, and Quote-to-Cash flow behavior
honest.

Author: Sarala Biswal
"""

from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from api.main import app


@pytest.fixture
async def client():
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as async_client:
            yield async_client


@pytest.mark.asyncio
async def test_api_endpoints_return_expected_shapes(client: AsyncClient) -> None:
    endpoints = [
        "/health",
        "/costs/summary",
        "/costs/by-model",
        "/costs/by-usecase",
        "/costs/timeline",
        "/costs/optimize?use_case=banking_payment_risk",
        "/quality/scores",
        "/quality/hallucinations",
        "/quality/gate-results",
        "/latency/percentiles",
        "/latency/slos",
        "/latency/timeline",
        "/prompts/versions?use_case=banking_payment_risk",
        "/drift/scores",
        "/drift/alerts",
        "/alerts/history",
    ]

    for endpoint in endpoints:
        response = await client.get(endpoint)
        assert response.status_code == 200, endpoint

    health = (await client.get("/health")).json()
    assert health["db"] == "ok"

    summary = (await client.get("/costs/summary")).json()
    assert {"total_cost_usd", "total_calls", "cost_by_model"} <= set(summary)

    empty_versions = (await client.get("/prompts/versions?use_case=unknown")).json()
    assert empty_versions == []


@pytest.mark.asyncio
async def test_ingest_and_prompt_compare_and_config(client: AsyncClient) -> None:
    call_id = f"api-test-call-{uuid4()}"
    ingest_response = await client.post(
        "/ingest",
        json={
            "call_id": call_id,
            "model": "gpt-4o-mini",
            "provider": "openai",
            "use_case": "api_test",
            "prompt_version": "v1.0",
            "input_tokens": 100,
            "output_tokens": 50,
            "latency_ms": 200,
            "cost_usd": str(Decimal("0.0")),
            "response_text": "Grounded answer",
            "context_text": "Grounded answer",
        },
    )
    assert ingest_response.status_code == 200
    assert ingest_response.json()["status"] == "accepted"

    create_response = await client.post(
        "/prompts/versions",
        json={
            "use_case": "api_test",
            "version": "v9.0",
            "prompt_text": "Prompt",
            "model": "gpt-4o-mini",
            "status": "testing",
        },
    )
    assert create_response.status_code == 200

    versions = (await client.get("/prompts/versions?use_case=banking_payment_risk")).json()
    compare = await client.get(
        f"/prompts/compare?a={versions[0]['version_id']}&b={versions[1]['version_id']}"
    )
    assert compare.status_code == 200
    assert "winner_version_id" in compare.json()

    config = await client.post("/alerts/config", json={"drift_alert_threshold": 0.4})
    assert config.status_code == 200
    assert config.json()["drift_alert_threshold"] == 0.4

    metrics = await client.get("/metrics")
    assert metrics.status_code == 200
    assert "llm_calls_total" in metrics.text
