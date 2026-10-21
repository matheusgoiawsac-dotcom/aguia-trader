"""REST API routing and handlers."""

from datetime import datetime, timezone
import json
import sys
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

from aguia.config import load_config, load_universe
from aguia.db import get_connection, get_meta, init_db

# Baseline values for the 18 monitored B3 tickers prior to first refresh
DEFAULT_BASELINES: Dict[str, Dict[str, Any]] = {
    "ASAI3": {"price": 13.27, "trend": "ALTA", "trendText": "ALTA (BULLISH)", "returnPct": 5.17, "target": 13.96, "stop": 12.65, "payoff": "1.11 : 1", "dayVar": "+0.85%"},
    "ANIM3": {"price": 5.29, "trend": "ALTA", "trendText": "ALTA (BULLISH)", "returnPct": 4.46, "target": 5.53, "stop": 5.08, "payoff": "1.14 : 1", "dayVar": "+1.15%"},
    "ARML3": {"price": 6.48, "trend": "ALTA", "trendText": "ALTA (BULLISH)", "returnPct": 5.45, "target": 6.83, "stop": 6.18, "payoff": "1.17 : 1", "dayVar": "+0.62%"},
    "AURE3": {"price": 15.59, "trend": "ALTA", "trendText": "ALTA (BULLISH)", "returnPct": 4.53, "target": 16.30, "stop": 14.95, "payoff": "1.11 : 1", "dayVar": "+0.32%"},
    "PETR4": {"price": 38.45, "trend": "ALTA", "trendText": "ALTA (BULLISH)", "returnPct": 3.80, "target": 39.91, "stop": 37.10, "payoff": "1.08 : 1", "dayVar": "+1.42%"},
    "VALE3": {"price": 61.20, "trend": "BAIXA", "trendText": "BAIXA (BEARISH)", "returnPct": -2.75, "target": 59.52, "stop": 62.60, "payoff": "1.20 : 1", "dayVar": "-0.95%"},
    "ITUB4": {"price": 34.80, "trend": "ALTA", "trendText": "ALTA (BULLISH)", "returnPct": 4.10, "target": 36.23, "stop": 33.60, "payoff": "1.19 : 1", "dayVar": "+0.78%"},
    "BBAS3": {"price": 27.60, "trend": "ALTA", "trendText": "ALTA (BULLISH)", "returnPct": 3.95, "target": 28.69, "stop": 26.70, "payoff": "1.21 : 1", "dayVar": "+0.55%"},
    "BBDC4": {"price": 14.90, "trend": "NEUTRO", "trendText": "LATERAL (NEUTRAL)", "returnPct": 0.67, "target": 15.00, "stop": 14.60, "payoff": "0.33 : 1", "dayVar": "+0.10%"},
    "WEGE3": {"price": 52.80, "trend": "ALTA", "trendText": "ALTA (BULLISH)", "returnPct": 6.25, "target": 56.10, "stop": 50.40, "payoff": "1.38 : 1", "dayVar": "+1.85%"},
    "MGLU3": {"price": 8.90, "trend": "BAIXA", "trendText": "BAIXA (BEARISH)", "returnPct": -5.40, "target": 8.42, "stop": 9.35, "payoff": "1.07 : 1", "dayVar": "-2.10%"},
    "PRIO3": {"price": 44.50, "trend": "ALTA", "trendText": "ALTA (BULLISH)", "returnPct": 4.85, "target": 46.66, "stop": 42.80, "payoff": "1.27 : 1", "dayVar": "+0.90%"},
    "RENT3": {"price": 54.30, "trend": "ALTA", "trendText": "ALTA (BULLISH)", "returnPct": 4.20, "target": 56.58, "stop": 52.40, "payoff": "1.20 : 1", "dayVar": "+0.60%"},
    "EMBR3": {"price": 49.80, "trend": "ALTA", "trendText": "ALTA (BULLISH)", "returnPct": 5.60, "target": 52.59, "stop": 47.90, "payoff": "1.47 : 1", "dayVar": "+1.95%"},
    "GGBR4": {"price": 21.15, "trend": "NEUTRO", "trendText": "LATERAL (NEUTRAL)", "returnPct": 0.45, "target": 21.25, "stop": 20.80, "payoff": "0.28 : 1", "dayVar": "+0.05%"},
    "CSNA3": {"price": 12.40, "trend": "BAIXA", "trendText": "BAIXA (BEARISH)", "returnPct": -3.80, "target": 11.93, "stop": 12.85, "payoff": "1.04 : 1", "dayVar": "-1.30%"},
    "SUZB3": {"price": 58.70, "trend": "ALTA", "trendText": "ALTA (BULLISH)", "returnPct": 4.30, "target": 61.22, "stop": 56.90, "payoff": "1.40 : 1", "dayVar": "+0.70%"},
    "JBSS3": {"price": 35.10, "trend": "ALTA", "trendText": "ALTA (BULLISH)", "returnPct": 3.70, "target": 36.40, "stop": 34.10, "payoff": "1.30 : 1", "dayVar": "+0.45%"}
}


def handle_api_status() -> Dict[str, Any]:
    """Handle GET /api/status."""
    config = load_config()

    refresh_status = {}
    try:
        init_db()
        conn = get_connection()
        try:
            for tf in config.get("timeframes", {}).get("available", ["1d", "15m", "5m"]):
                refresh_status[tf] = get_meta(conn, f"last_refresh_{tf}")
        finally:
            conn.close()
    except Exception:
        pass

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
        "ollama": {
            "available": False,
            "model": config.get("ollama", {}).get("model", "auto")
        },
        "refresh": refresh_status,
        "disclaimer": config.get("compliance", {}).get(
            "disclaimer",
            "Análise experimental gerada por modelo estatístico. Não constitui recomendação de investimento. Sem backtest validado."
        )
    }


def handle_api_assets() -> Dict[str, Any]:
    """Handle GET /api/assets and GET /api/universe."""
    universe = load_universe()
    init_db()

    assets: List[Dict[str, Any]] = []
    with get_connection() as conn:
        for ticker in universe:
            # Check if setup exists in SQLite
            cur_setup = conn.execute(
                "SELECT * FROM setups WHERE ticker = ? ORDER BY asof DESC LIMIT 1",
                (ticker,)
            )
            setup_row = cur_setup.fetchone()

            # Check latest candle in SQLite
            cur_candle = conn.execute(
                "SELECT close, open FROM candles WHERE ticker = ? ORDER BY ts DESC LIMIT 1",
                (ticker,)
            )
            candle_row = cur_candle.fetchone()

            if setup_row and candle_row:
                price = float(candle_row["close"])
                prev_open = float(candle_row["open"])
                day_var_pct = ((price - prev_open) / prev_open) * 100 if prev_open else 0.0
                sign = "+" if day_var_pct >= 0 else ""
                trend = setup_row["signal"]
                trend_text = "ALTA (BULLISH)" if trend == "ALTA" else ("BAIXA (BEARISH)" if trend == "BAIXA" else "LATERAL (NEUTRAL)")
                payoff_val = setup_row["payoff"]
                payoff_str = f"{payoff_val:.2f} : 1" if payoff_val is not None else "—"

                assets.append({
                    "ticker": ticker,
                    "price": price,
                    "trend": trend,
                    "trendText": trend_text,
                    "returnPct": round((setup_row["ret"] or 0.0) * 100, 2),
                    "target": setup_row["target"],
                    "stop": setup_row["stop"],
                    "payoff": payoff_str,
                    "dayVar": f"{sign}{day_var_pct:.2f}%",
                    "asof": setup_row["asof"]
                })
            elif ticker in DEFAULT_BASELINES:
                item = dict(DEFAULT_BASELINES[ticker])
                item["ticker"] = ticker
                item["asof"] = None
                assets.append(item)
            else:
                assets.append({
                    "ticker": ticker,
                    "price": 0.0,
                    "trend": "NEUTRO",
                    "trendText": "AGUARDANDO ATUALIZAÇÃO",
                    "returnPct": 0.0,
                    "target": 0.0,
                    "stop": 0.0,
                    "payoff": "—",
                    "dayVar": "0.00%",
                    "asof": None
                })

    return {
        "total": len(assets),
        "assets": assets
    }


def handle_api_asset(ticker: str) -> Dict[str, Any]:
    """Handle GET /api/asset?ticker=."""
    all_assets = handle_api_assets()["assets"]
    asset = next((a for a in all_assets if a["ticker"].upper() == ticker.upper()), None)
    if asset:
        return {"success": True, "asset": asset}
    return {"success": False, "error": f"Ativo {ticker} não encontrado"}
