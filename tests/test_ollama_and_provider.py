"""Tests for Ollama integration, deterministic fallback, and market data provider."""

from aguia.explain.ollama import (
    verificar_status_ollama,
    gerar_racional_deterministico,
    gerar_racional_ia
)
from aguia.server.routes import handle_api_status_ollama

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


def _synthetic_market_frame(rows: int = 260):
    """Deterministic OHLCV frame shaped like the provider output."""
    import numpy as np
    import pandas as pd

    index = pd.date_range("2025-10-01", periods=rows, freq="B")
    close = np.linspace(30.0, 40.0, rows)
    frame = pd.DataFrame(
        {
            "open": close - 0.2,
            "high": close + 0.5,
            "low": close - 0.5,
            "close": close,
            "volume": np.full(rows, 1_000_000.0),
        },
        index=index,
    )
    from aguia.indicators import calc_atr, calc_sma, calc_wma

    frame["sma200"] = calc_sma(frame["close"], window=200)
    frame["wma30"] = calc_wma(frame["close"], window=30)
    frame["atr14"] = calc_atr(frame["high"], frame["low"], frame["close"], window=14)
    return frame


def test_handle_api_analise_uses_cached_market_data(monkeypatch, tmp_path):
    import aguia.db as db_module
    import aguia.server.routes as routes
    from contextlib import contextmanager

    frame = _synthetic_market_frame()
    monkeypatch.setattr(routes, "obter_dados_mercado", lambda *a, **k: frame)

    # Isolate the persistence layer: synthetic prices must never reach the real DB
    test_db = tmp_path / "analise.db"
    db_module.init_db(test_db)

    @contextmanager
    def _isolated_pooled_db(db_path=None):
        with db_module.pooled_db(test_db) as conn:
            yield conn

    monkeypatch.setattr(routes, "pooled_db", _isolated_pooled_db)
    routes._analysis_cache.clear()

    res = routes.handle_api_analise("petr4")
    assert res["sucesso"] is True
    dados = res["dados"]

    assert dados["ticker"] == "PETR4"
    assert dados["preco"] > 0
    assert dados["alvo"] > 0
    assert dados["stop"] > 0
    assert dados["tendencia"] in ("ALTA", "BAIXA", "NEUTRO")
    assert "R$" in dados["resumo"]
    assert dados["disclaimer"]
    assert len(dados["candles"]) == 65

    # No NaN or Infinity may leak into the JSON payload
    import json

    payload = json.dumps(dados, ensure_ascii=False)
    assert "NaN" not in payload
    assert "Infinity" not in payload

    # The isolated database received the setup, candles and explanation
    with db_module.pooled_db(test_db) as conn:
        assert conn.execute(
            "SELECT COUNT(1) FROM setups WHERE ticker = 'PETR4'"
        ).fetchone()[0] == 1
        assert conn.execute(
            "SELECT COUNT(1) FROM explanations WHERE ticker = 'PETR4'"
        ).fetchone()[0] == 1

    # A second call must be served from the in-process cache
    routes._analysis_cache.clear()
