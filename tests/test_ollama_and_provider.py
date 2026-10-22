"""Tests for Ollama integration, deterministic fallback, and market data provider."""

import pytest
from integracao_ollama import (
    verificar_status_ollama,
    gerar_racional_deterministico,
    gerar_racional_ia
)
from aguia.server.routes import handle_api_status_ollama, handle_api_analise


def test_status_ollama_structure():
    status = verificar_status_ollama()
    assert "online" in status
    assert "modelo" in status
    assert "url" in status
    assert status["url"] == "http://localhost:11434"


def test_deterministic_rationale_alta():
    setup = {
        "ticker": "PETR4",
        "preco": 38.50,
        "alvo": 41.20,
        "stop": 36.80,
        "payoff": "1.59 : 1",
        "projecao_pct": 7.01,
        "risco_pct": -4.42,
        "tendencia": "ALTA",
        "indicadores": {
            "sma200": 34.00,
            "wma30": 36.50,
            "atr14": 1.70
        }
    }
    rationale = gerar_racional_deterministico(setup)
    assert "PETR4" in rationale
    assert "R$ 41,20" in rationale or "R$ 41.20" in rationale
    assert "R$ 36,80" in rationale or "R$ 36.80" in rationale
    assert "1.59 : 1" in rationale
    assert "WMA 30" in rationale


def test_deterministic_rationale_baixa():
    setup = {
        "ticker": "VALE3",
        "preco": 60.00,
        "alvo": 57.00,
        "stop": 62.00,
        "payoff": "1.50 : 1",
        "projecao_pct": -5.00,
        "risco_pct": 3.33,
        "tendencia": "BAIXA",
        "indicadores": {
            "sma200": 65.00,
            "wma30": 62.00,
            "atr14": 2.00
        }
    }
    rationale = gerar_racional_deterministico(setup)
    assert "VALE3" in rationale
    assert "vendedora" in rationale or "recuo" in rationale
    assert "1.50 : 1" in rationale


def test_gerar_racional_ia_offline_fallback():
    # With Ollama offline, must return deterministic text with source 'deterministico'
    setup = {
        "ticker": "WEGE3",
        "preco": 50.00,
        "alvo": 54.00,
        "stop": 47.00,
        "payoff": "1.33 : 1",
        "projecao_pct": 8.00,
        "risco_pct": -6.00,
        "tendencia": "ALTA",
        "indicadores": {
            "sma200": 42.00,
            "wma30": 47.00,
            "atr14": 2.50
        }
    }
    texto, fonte = gerar_racional_ia(setup)
    assert fonte == "deterministico"
    assert "WEGE3" in texto
    assert len(texto) > 40


def test_api_status_ollama_endpoint():
    res = handle_api_status_ollama()
    assert res["sucesso"] is True
    assert "online" in res["dados"]
    assert res["erro"] is None
