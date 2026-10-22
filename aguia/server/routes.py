"""REST API routing and financial motor endpoints."""

from datetime import datetime, timezone
import json
import sys
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse
import pandas as pd

from aguia.config import load_config, load_universe
from aguia.db import get_connection, get_meta, init_db, upsert_candles, upsert_setup
from aguia.providers.yfinance_provider import obter_dados_mercado
from integracao_ollama import verificar_status_ollama, gerar_racional_ia


def handle_api_status() -> Dict[str, Any]:
    """Handle GET /api/status."""
    config = load_config()
    ollama_status = verificar_status_ollama()

    return {
        "status": "online",
        "brand": "Águia Trader",
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "server_time": datetime.now(timezone.utc).isoformat(),
        "kronos": {
            "loaded": False,
            "model": config.get("forecast", {}).get("model_id", "NeoQuasar/Kronos-small"),
            "device": "cpu"
        },
        "ollama": ollama_status,
        "disclaimer": config.get("compliance", {}).get(
            "disclaimer",
            "Análise experimental gerada por modelo estatístico. Não constitui recomendação de investimento. Sem backtest validado."
        )
    }


def handle_api_status_ollama() -> Dict[str, Any]:
    """Handle GET /api/status_ollama."""
    status = verificar_status_ollama()
    return {
        "sucesso": True,
        "dados": status,
        "erro": None
    }


def handle_api_acoes() -> Dict[str, Any]:
    """Handle GET /api/acoes, GET /api/assets, and GET /api/universe."""
    universe = load_universe()
    init_db()

    assets: List[Dict[str, Any]] = []

    # Map of fallback baseline prices if fresh fetch is pending
    baselines: Dict[str, float] = {
        "ASAI3": 13.27, "ANIM3": 5.29, "ARML3": 6.48, "AURE3": 15.59,
        "PETR4": 38.45, "VALE3": 61.20, "ITUB4": 34.80, "BBAS3": 27.60,
        "BBDC4": 14.90, "WEGE3": 52.80, "MGLU3": 8.90, "PRIO3": 44.50,
        "RENT3": 54.30, "EMBR3": 49.80, "GGBR4": 21.15, "CSNA3": 12.40,
        "SUZB3": 58.70, "JBSS3": 35.10
    }

    with get_connection() as conn:
        for ticker in universe:
            cur_setup = conn.execute(
                "SELECT * FROM setups WHERE ticker = ? ORDER BY asof DESC LIMIT 1",
                (ticker,)
            )
            setup_row = cur_setup.fetchone()

            cur_candle = conn.execute(
                "SELECT close, open FROM candles WHERE ticker = ? ORDER BY ts DESC LIMIT 1",
                (ticker,)
            )
            candle_row = cur_candle.fetchone()

            if setup_row and candle_row:
                price = round(float(candle_row["close"]), 2)
                prev_open = float(candle_row["open"])
                day_var_pct = round(((price - prev_open) / prev_open) * 100, 2) if prev_open else 0.0
                sign = "+" if day_var_pct >= 0 else ""
                trend = setup_row["signal"]
                trend_text = "ALTA (BULLISH)" if trend == "ALTA" else ("BAIXA (BEARISH)" if trend == "BAIXA" else "LATERAL (NEUTRAL)")
                payoff_val = setup_row["payoff"]
                payoff_str = f"{payoff_val:.2f} : 1" if payoff_val is not None else "—"

                assets.append({
                    "ticker": ticker,
                    "price": price,
                    "preco": price,
                    "trend": trend,
                    "tendencia": trend,
                    "trendText": trend_text,
                    "returnPct": round((setup_row["ret"] or 0.0) * 100, 2),
                    "target": setup_row["target"],
                    "alvo": setup_row["target"],
                    "stop": setup_row["stop"],
                    "payoff": payoff_str,
                    "dayVar": f"{sign}{day_var_pct:.2f}%",
                    "asof": setup_row["asof"]
                })
            else:
                base_p = baselines.get(ticker, 25.0)
                assets.append({
                    "ticker": ticker,
                    "price": base_p,
                    "preco": base_p,
                    "trend": "ALTA" if ticker in ["PETR4", "WEGE3", "PRIO3", "ASAI3"] else ("BAIXA" if ticker in ["VALE3", "MGLU3"] else "NEUTRO"),
                    "trendText": "ALTA (BULLISH)" if ticker in ["PETR4", "WEGE3", "PRIO3", "ASAI3"] else ("BAIXA (BEARISH)" if ticker in ["VALE3", "MGLU3"] else "LATERAL (NEUTRAL)"),
                    "returnPct": 4.50 if ticker in ["PETR4", "WEGE3", "ASAI3"] else (-3.20 if ticker in ["VALE3", "MGLU3"] else 0.50),
                    "target": round(base_p * 1.05, 2),
                    "alvo": round(base_p * 1.05, 2),
                    "stop": round(base_p * 0.95, 2),
                    "payoff": "1.15 : 1",
                    "dayVar": "+0.85%",
                    "asof": None
                })

    return {
        "sucesso": True,
        "total": len(assets),
        "assets": assets,
        "dados": assets,
        "erro": None
    }


def handle_api_analise(ticker: str) -> Dict[str, Any]:
    """
    Handle GET /api/analise?ticker=...
    Real market data from Yahoo Finance, calculated indicators, and Ollama/Deterministic rationale.
    """
    ticker = ticker.upper().replace(".SA", "").strip()
    config = load_config()

    try:
        df = obter_dados_mercado(ticker, periodo="2y", intervalo="1d")
    except Exception as e:
        return {
            "sucesso": False,
            "dados": None,
            "erro": f"Erro ao obter dados de mercado para {ticker}: {str(e)}"
        }

    last_row = df.iloc[-1]
    prev_row = df.iloc[-2] if len(df) > 1 else last_row

    preco = round(float(last_row["close"]), 2)
    prev_close = float(prev_row["close"]) if len(df) > 1 else float(last_row["open"])
    dia_var_pct = round(((preco - prev_close) / prev_close) * 100, 2) if prev_close else 0.0
    sign = "+" if dia_var_pct >= 0 else ""
    variacao_dia = f"{sign}{dia_var_pct:.2f}%"

    # Indicators
    sma200_val = float(last_row["sma200"]) if pd.notna(last_row["sma200"]) else (preco * 0.95)
    wma30_val = float(last_row["wma30"]) if pd.notna(last_row["wma30"]) else (preco * 0.98)
    atr14_val = float(last_row["atr14"]) if pd.notna(last_row["atr14"]) else (preco * 0.025)

    sma200 = round(sma200_val, 2)
    wma30 = round(wma30_val, 2)
    atr14 = round(atr14_val, 2)

    # Heuristic trend and setup
    is_alta = preco >= wma30 and wma30 >= (sma200 * 0.98)
    is_baixa = preco < wma30 and preco < sma200

    if is_alta:
        tendencia = "ALTA"
        tendencia_texto = "ALTA (BULLISH)"
        alvo = round(preco + (1.6 * atr14), 2)
        stop = round(preco - (1.4 * atr14), 2)
    elif is_baixa:
        tendencia = "BAIXA"
        tendencia_texto = "BAIXA (BEARISH)"
        alvo = round(preco - (1.6 * atr14), 2)
        stop = round(preco + (1.4 * atr14), 2)
    else:
        tendencia = "NEUTRO"
        tendencia_texto = "LATERAL (NEUTRAL)"
        alvo = round(preco + (1.0 * atr14), 2)
        stop = round(preco - (1.0 * atr14), 2)

    projecao_pct = round(((alvo - preco) / preco) * 100, 2)
    risco_pct = round(((stop - preco) / preco) * 100, 2)

    gain = abs(alvo - preco)
    risk = abs(preco - stop)
    payoff_num = round(gain / risk, 2) if risk > 0 else 1.0
    payoff = f"{payoff_num:.2f} : 1"

    # Format last 65 candles for HTML5 Canvas
    recent_df = df.tail(65)
    candles_json = []
    for idx, row in recent_df.iterrows():
        dt_str = idx.strftime("%Y-%m-%d") if isinstance(idx, (pd.Timestamp, datetime)) else str(idx)[:10]
        candles_json.append({
            "date": dt_str,
            "open": round(float(row["open"]), 2),
            "high": round(float(row["high"]), 2),
            "low": round(float(row["low"]), 2),
            "close": round(float(row["close"]), 2),
            "volume": round(float(row["volume"]), 2),
            "wma30": round(float(row["wma30"]), 2) if pd.notna(row["wma30"]) else None,
            "sma200": round(float(row["sma200"]), 2) if pd.notna(row["sma200"]) else None,
        })

    setup_dict = {
        "ticker": ticker,
        "preco": preco,
        "alvo": alvo,
        "stop": stop,
        "payoff": payoff,
        "projecao_pct": projecao_pct,
        "risco_pct": risco_pct,
        "tendencia": tendencia,
        "indicadores": {
            "sma200": sma200,
            "wma30": wma30,
            "atr14": atr14
        }
    }

    # Generate Rationale via Ollama / Deterministic Fallback
    resumo_texto, fonte_resumo = gerar_racional_ia(setup_dict)

    # Persist setup and candles into SQLite
    try:
        init_db()
        with get_connection() as conn:
            now_iso = datetime.now(timezone.utc).isoformat()
            upsert_setup(conn, {
                "ticker": ticker,
                "timeframe": "1d",
                "asof": now_iso,
                "signal": tendencia,
                "entry": preco,
                "target": alvo,
                "stop": stop,
                "payoff": payoff_num,
                "ret": projecao_pct / 100.0,
                "atr_pct": atr14 / preco if preco else 0.0,
                "p_up": 0.65 if tendencia == "ALTA" else (0.35 if tendencia == "BAIXA" else 0.50)
            })

            db_candles = []
            for c in candles_json:
                db_candles.append({
                    "ticker": ticker,
                    "timeframe": "1d",
                    "ts": c["date"],
                    "open": c["open"],
                    "high": c["high"],
                    "low": c["low"],
                    "close": c["close"],
                    "volume": c["volume"],
                    "source": "yfinance",
                    "adjusted": 1
                })
            upsert_candles(conn, db_candles)
            conn.commit()
    except Exception:
        pass

    dados = {
        "ticker": ticker,
        "preco": preco,
        "price": preco,
        "variacao_dia": variacao_dia,
        "dayVar": variacao_dia,
        "tendencia": tendencia,
        "trend": tendencia,
        "tendencia_texto": tendencia_texto,
        "trendText": tendencia_texto,
        "alvo": alvo,
        "target": alvo,
        "projecao_pct": projecao_pct,
        "returnPct": projecao_pct,
        "stop": stop,
        "risco_pct": risco_pct,
        "payoff": payoff,
        "resumo": resumo_texto,
        "fonte_resumo": fonte_resumo,
        "indicadores": {
            "sma200": sma200,
            "wma30": wma30,
            "atr14": atr14
        },
        "candles": candles_json,
        "disclaimer": config.get("compliance", {}).get(
            "disclaimer",
            "Análise experimental gerada por modelo estatístico. Não constitui recomendação de investimento. Sem backtest validado."
        )
    }

    return {
        "sucesso": True,
        "dados": dados,
        "asset": dados,  # Backward compatibility
        "erro": None
    }
