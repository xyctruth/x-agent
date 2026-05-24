import pytest
from fastapi.testclient import TestClient

from x_agent.core.config import get_settings
from x_agent.main import create_app


def test_generate_sql_returns_agentic_rag_result(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("X_AGENT_NL2SQL_KNOWLEDGE_SOURCE", "memory")
    get_settings.cache_clear()
    client = TestClient(create_app())
    get_settings.cache_clear()

    response = client.post(
        "/api/v1/nl2sql/generate",
        json={
            "question": "统计最近 7 天订单数和支付金额",
            "metadata": {"biz_domain": "demo"},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["question"] == "统计最近 7 天订单数和支付金额"
    assert [step["knowledge_types"] for step in body["retrieval_plan"]] == [
        ["term", "metric"],
        ["table"],
        ["example"],
    ]
    assert "LEFT JOIN fact_payments" in body["generated_sql"]["sql"]
    assert body["validation"]["is_valid"] is True
    assert body["validation"]["referenced_tables"] == ["fact_orders", "fact_payments"]
    assert body["retrieved_context"]


def test_generate_sql_rejects_empty_question(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("X_AGENT_NL2SQL_KNOWLEDGE_SOURCE", "memory")
    get_settings.cache_clear()
    client = TestClient(create_app())
    get_settings.cache_clear()

    response = client.post(
        "/api/v1/nl2sql/generate",
        json={"question": ""},
    )

    assert response.status_code == 422
