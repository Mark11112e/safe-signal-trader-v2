"""Dashboard UI unit tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from signal_bot.main import create_app


def test_dashboard_root_returns_html():
    client = TestClient(create_app())
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")
    body = r.text
    assert "Safe Signal Trader" in body
    assert "Phase" in body or "2-source-parser" in body or "1-foundation" in body
    assert "Gated OFF" in body or "Live" in body or "OFF" in body


def test_dashboard_not_json_404():
    client = TestClient(create_app())
    r = client.get("/")
    assert r.status_code != 404
    assert "Not Found" not in r.text or "Safe Signal Trader" in r.text
