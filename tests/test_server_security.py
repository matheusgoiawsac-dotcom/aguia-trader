"""Tests for HTTP server security, sandbox restrictions, and CORS allowlisting."""

import threading
import time
import urllib.request
import urllib.error
import json
import pytest

from aguia.server.handler import create_server


@pytest.fixture(scope="module")
def running_server():
    """Spin up a test server on an ephemeral port on 127.0.0.1."""
    server = create_server(host="127.0.0.1", port=8001)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.1)
    yield "http://127.0.0.1:8001"
    server.shutdown()
    server.server_close()


def test_api_status_returns_200(running_server: str):
    url = f"{running_server}/api/status"
    req = urllib.request.Request(url, headers={"Origin": "http://localhost:8000"})
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        assert resp.headers.get("Access-Control-Allow-Origin") == "http://localhost:8000"
        data = json.loads(resp.read().decode("utf-8"))
        assert data["status"] == "online"
        assert "python_version" in data
        assert "kronos" in data
        assert "ollama" in data


def test_cors_rejects_unauthorized_origin(running_server: str):
    url = f"{running_server}/api/status"
    req = urllib.request.Request(url, headers={"Origin": "http://malicious-website.com"})
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        assert resp.headers.get("Access-Control-Allow-Origin") is None


def test_get_app_py_returns_404(running_server: str):
    url = f"{running_server}/app.py"
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(url)
    assert exc_info.value.code == 404
    body = json.loads(exc_info.value.read().decode("utf-8"))
    assert body["success"] is False
    assert body["code"] == 404


def test_directory_traversal_returns_404(running_server: str):
    url = f"{running_server}/../config/config.toml"
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(url)
    assert exc_info.value.code == 404


def test_serves_static_index(running_server: str):
    url = f"{running_server}/"
    with urllib.request.urlopen(url) as resp:
        assert resp.status == 200
        content = resp.read().decode("utf-8")
        assert "<!DOCTYPE html>" in content
        assert "Águia Trader" in content


def test_api_status_ollama_endpoint_http(running_server: str):
    url = f"{running_server}/api/status_ollama"
    with urllib.request.urlopen(url) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data["sucesso"] is True
        assert "dados" in data
        assert "online" in data["dados"]


def test_api_acoes_endpoint_http(running_server: str):
    url = f"{running_server}/api/acoes"
    with urllib.request.urlopen(url) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data["sucesso"] is True
        assert "assets" in data or "dados" in data
        tickers = [a["ticker"] for a in data.get("assets", [])]
        assert "PETR4" in tickers
        assert "VALE3" in tickers


@pytest.mark.network
def test_api_analise_endpoint_http(running_server: str, require_network):
    url = f"{running_server}/api/analise?ticker=PETR4"
    with urllib.request.urlopen(url) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data["sucesso"] is True
        assert data["dados"]["ticker"] == "PETR4"
        assert "preco" in data["dados"]
        assert "alvo" in data["dados"]
        assert "stop" in data["dados"]
        assert "resumo" in data["dados"]
        assert len(data["dados"]["candles"]) > 0


@pytest.mark.network
def test_api_chart_png_endpoint_http(running_server: str, require_network):
    url = f"{running_server}/api/chart.png?ticker=PETR4"
    with urllib.request.urlopen(url) as resp:
        assert resp.status == 200
        assert resp.headers.get("Content-Type") == "image/png"
        raw_bytes = resp.read()
        assert len(raw_bytes) > 1000
        assert raw_bytes[:4] == b"\x89PNG"
