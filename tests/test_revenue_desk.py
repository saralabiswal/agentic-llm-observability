"""
Regression tests that keep the API, telemetry math, and Quote-to-Cash flow behavior
honest.

Author: Sarala Biswal
"""

import pytest
from httpx import ASGITransport, AsyncClient

from api.main import app
from revenue_desk import llm as revenue_llm


class _FakeOllamaResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, str]:
        return {"response": "Local Ollama quote analysis with grounded revenue guidance."}


class _FakeOllamaClient:
    calls: list[dict[str, object]] = []

    def __init__(self, *args: object, **kwargs: object) -> None:
        return None

    async def __aenter__(self) -> "_FakeOllamaClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def post(self, url: str, json: dict[str, object]) -> _FakeOllamaResponse:
        self.calls.append({"url": url, "json": json})
        return _FakeOllamaResponse()


@pytest.fixture
async def client():
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as async_client:
            yield async_client


@pytest.mark.asyncio
async def test_revenue_opportunities_return_realistic_scenarios(client: AsyncClient) -> None:
    response = await client.get("/revenue-desk/opportunities")

    assert response.status_code == 200
    opportunities = response.json()
    assert len(opportunities) == 5
    assert {item["scenario"] for item in opportunities} == {
        "enterprise_expansion",
        "renewal_at_risk",
        "discount_pressure",
        "margin_protection",
        "multi_product_upsell",
    }
    assert all(item["grounded_evidence"] for item in opportunities)


@pytest.mark.asyncio
async def test_developer_prompts_preview_uses_agent_prompt_builder(client: AsyncClient) -> None:
    response = await client.get(
        "/revenue-desk/developer/prompts",
        params={
            "opportunity_id": "RCC-OPP-002",
            "prompt_version": "v2.2",
            "approval_guardrails_enabled": "true",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["prompt_version"] == "v2.2"
    assert payload["approval_guardrails_enabled"] is True
    assert len(payload["prompts"]) == 5
    margin_prompt = next(
        item for item in payload["prompts"] if item["prompt_name"] == "margin_risk"
    )
    assert margin_prompt["prompt_contract"] == "v2.2.margin_risk"
    assert "Agent: Margin Risk Agent" in margin_prompt["prompt"]
    assert "Task context: Assess expected margin" in margin_prompt["prompt"]
    assert "approval guardrails enforced" in margin_prompt["prompt"]
    assert margin_prompt["policy_source"]["policy_id"] == "REV-MARGIN-2026.05"
    assert margin_prompt["policy_source"]["title"] == "Gross Margin Protection Policy"
    assert any("Target margin" in rule for rule in margin_prompt["policy_source"]["rules"])
    assert {"input_tokens", "cost_usd", "quality_score"}.issubset(
        set(margin_prompt["observability_fields"])
    )


@pytest.mark.asyncio
async def test_approval_guardrail_is_only_effective_for_v22(client: AsyncClient) -> None:
    response = await client.get(
        "/revenue-desk/developer/prompts",
        params={
            "opportunity_id": "RCC-OPP-002",
            "prompt_version": "v2.1",
            "approval_guardrails_enabled": "true",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["prompt_version"] == "v2.1"
    assert payload["approval_guardrails_enabled"] is False
    margin_prompt = next(
        item for item in payload["prompts"] if item["prompt_name"] == "margin_risk"
    )
    assert "approval guardrails advisory" in margin_prompt["prompt"]


@pytest.mark.asyncio
async def test_revenue_analysis_returns_structured_output_and_persists_telemetry(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/revenue-desk/analyze",
        json={
            "opportunity_id": "RCC-OPP-002",
            "prompt_version": "v2.2",
            "model_mode": "mock",
            "approval_guardrails_enabled": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["recommendation"]["approval_recommendation"] in {
        "approval_required",
        "executive_review",
    }
    assert payload["recommendation"]["evidence_citations"]
    assert payload["trace"]["prompt_version"] == "v2.2"
    assert payload["trace"]["model_mode"] == "mock"
    assert payload["trace"]["call_id"].startswith("rcc-")
    assert float(payload["trace"]["cost_usd"]) >= 0
    assert len(payload["trace"]["steps"]) == 5
    assert {
        step["prompt_version"]
        for step in payload["trace"]["steps"]
    } == {
        "v2.2.context",
        "v2.2.discount_policy",
        "v2.2.margin_risk",
        "v2.2.approval_route",
        "v2.2.negotiation_guidance",
    }
    assert all(
        step["agent_name"] and step["call_id"].startswith("rcc-")
        for step in payload["trace"]["steps"]
    )
    assert sum(
        step["input_tokens"] + step["output_tokens"]
        for step in payload["trace"]["steps"]
    ) == (payload["trace"]["input_tokens"] + payload["trace"]["output_tokens"])

    summary = (
        await client.get(
            "/costs/summary?use_case=quote_to_cash_revenue_command_center"
        )
    ).json()
    assert summary["total_calls"] >= 5
    assert summary["cost_by_usecase"]["quote_to_cash_revenue_command_center"]

    hallucinations = (await client.get("/quality/hallucinations")).json()
    assert any(
        item["use_case"] == "quote_to_cash_revenue_command_center"
        for item in hallucinations
    )

    drift_scores = (await client.get("/drift/scores")).json()
    assert any(
        item["use_case"] == "quote_to_cash_revenue_command_center"
        for item in drift_scores
    )

    versions = (
        await client.get("/prompts/versions?use_case=quote_to_cash_revenue_command_center")
    ).json()
    assert {item["version"] for item in versions} >= {"v1.0", "v2.1", "v2.2"}
    assert {item["version"] for item in versions} >= {
        "v2.2.margin_risk",
        "v2.2.approval_route",
    }


@pytest.mark.asyncio
async def test_revenue_analysis_default_uses_local_ollama_llm(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _FakeOllamaClient.calls = []
    monkeypatch.setattr(revenue_llm.httpx, "AsyncClient", _FakeOllamaClient)

    response = await client.post(
        "/revenue-desk/analyze",
        json={
            "opportunity_id": "RCC-OPP-001",
            "prompt_version": "v2.2",
            "approval_guardrails_enabled": True,
        },
    )

    assert response.status_code == 200
    trace = response.json()["trace"]
    assert trace["model_mode"] == "ollama"
    assert trace["provider"] == "ollama"
    assert trace["model"] == "llama3.2"
    assert len(trace["steps"]) == 5
    assert len(_FakeOllamaClient.calls) == 5
    assert all(step["provider"] == "ollama" for step in trace["steps"])
    assert all(call["json"]["model"] == "llama3.2" for call in _FakeOllamaClient.calls)


@pytest.mark.asyncio
async def test_revenue_analysis_mock_mode_does_not_require_ollama(client: AsyncClient) -> None:
    response = await client.post(
        "/revenue-desk/analyze",
        json={
            "opportunity_id": "RCC-OPP-004",
            "prompt_version": "v2.1",
            "model_mode": "mock",
            "approval_guardrails_enabled": False,
        },
    )

    assert response.status_code == 200
    trace = response.json()["trace"]
    assert trace["model_mode"] == "mock"
    assert trace["provider"] == "openai"


@pytest.mark.asyncio
async def test_revenue_analysis_uses_selected_local_model(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _FakeOllamaClient.calls = []
    monkeypatch.setattr(revenue_llm.httpx, "AsyncClient", _FakeOllamaClient)

    response = await client.post(
        "/revenue-desk/analyze",
        json={
            "opportunity_id": "RCC-OPP-001",
            "prompt_version": "v2.2",
            "model_mode": "ollama",
            "local_model": "qwen2.5:7b",
            "approval_guardrails_enabled": True,
        },
    )

    assert response.status_code == 200
    trace = response.json()["trace"]
    assert trace["model"] == "qwen2.5:7b"
    assert all(step["model"] == "qwen2.5:7b" for step in trace["steps"])
    assert all(call["json"]["model"] == "qwen2.5:7b" for call in _FakeOllamaClient.calls)
