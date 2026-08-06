"""Health endpoint unit tests – TestClient, no network."""

from __future__ import annotations

from fastapi.testclient import TestClient

from signal_bot.main import create_app


def test_health_endpoint():
    client = TestClient(create_app())
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["live_trading_enabled"] is False
    assert data["live_allowed"] is False


def test_ready_endpoint():
    assert TestClient(create_app()).get("/ready").status_code == 200


def test_status_endpoint():
    data = TestClient(create_app()).get("/status").json()
    assert data["phase"] == "2-source-parser"
    assert data["components"]["exchange_adapters"] == "interfaces-only"
    assert "parsers" in data["components"]
    assert "source_registry" in data["components"]
    assert data["components"]["ingestion"] == "pipeline+dedup"


def test_docs_available():
    assert TestClient(create_app()).get("/docs").status_code == 200
