"""Shared pytest fixtures and markers for Aguia Trader."""

import json
import socket
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "network: test requires outbound access to Yahoo Finance",
    )


@pytest.fixture(scope="session")
def network_available() -> bool:
    """Check whether outbound access to the market data host is reachable."""
    try:
        with socket.create_connection(("query1.finance.yahoo.com", 443), timeout=3):
            return True
    except OSError:
        return False


@pytest.fixture
def require_network(network_available):
    if not network_available:
        pytest.skip("Rede externa indisponível: teste de rede ignorado")


@pytest.fixture(scope="session")
def demo_analysis() -> dict:
    """Labelled demo fixture (SIMULADO) used by offline checks."""
    with open(FIXTURES_DIR / "demo_analysis.json", "r", encoding="utf-8") as f:
        return json.load(f)
