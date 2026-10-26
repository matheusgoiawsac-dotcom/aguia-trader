"""REST API routing and financial motor endpoints."""

from datetime import datetime, timezone
import logging
import math
import sys
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from aguia.config import get_yfinance_period, load_config, load_universe
from aguia.db import init_db, pooled_db, prune_history, upsert_candles, upsert_explanation, upsert_setup
from aguia.explain.ollama import gerar_racional_ia, verificar_status_ollama
from aguia.explain.validator import hash_facts
from aguia.forecast.signals import build_setup
from aguia.icons import categoria_do_ativo, setor_do_ativo
from aguia.modes import (
    ATIVOS_DAY,
    MODO_PADRAO,
    catalogo_modos,
    get_modo,
    normalizar_intervalo,
    normalizar_modo,
    periodo_yahoo,
    rotulo_ativo,
    simbolo_yahoo,
    universo_do_modo,
)
from aguia.providers.yfinance_provider import obter_dados_mercado
from aguia.strategies.macro_jr import MacroJRParams, filtrar_ativos_macro_jr, params_from_dict, params_to_dict, calcular_macro_jr_detalhado

logger = logging.getLogger("aguia.routes")

# Number of candles shipped to the Canvas chart
CHART_CANDLES = 65

# Analysis payloads are memoised: the underlying market data is already
# cached by the provider, so rebuilding the payload on every click only burns
# CPU and re-triggers the LLM round-trip.
ANALYSIS_CACHE_TTL_SECONDS = 60.0
_analysis_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_analysis_lock = threading.Lock()

# Fallback reference prices used only when a ticker has no stored data yet.
BASELINE_PRICES: Dict[str, float] = {
    "ASAI3": 13.27, "ANIM3": 5.29, "ARML3": 6.48, "AURE3": 15.59,
    "PETR4": 38.45, "VALE3": 61.20, "ITUB4": 34.80, "BBAS3": 27.60,
    "BBDC4": 14.90, "WEGE3": 52.80, "MGLU3": 8.90, "PRIO3": 44.50,
    "RENT3": 54.30, "EMBR3": 49.80, "GGBR4": 21.15, "CSNA3": 12.40,
    "SUZB3": 58.70, "JBSS3": 35.10
}

# Labelled placeholders for the intraday workspace (SIMULADO until the first
# real intraday quote is stored).
BASELINE_PRICES_DAY: Dict[str, float] = {
    "SPY": 645.10, "DIA": 438.75, "GC=F": 2678.40, "BTC-USD": 68420.00
}

BASELINE_ALTA = {"PETR4", "WEGE3", "PRIO3", "ASAI3"}
BASELINE_BAIXA = {"VALE3", "MGLU3"}

TREND_TEXT = {
    "ALTA": "ALTA (BULLISH)",
    "BAIXA": "BAIXA (BEARISH)",
    "NEUTRO": "LATERAL (NEUTRAL)",
}

DEFAULT_DISCLAIMER = (
    "Análise experimental gerada por modelo estatístico. "
    "Não constitui recomendação de investimento. Sem backtest validado."
)

_SNAPSHOT_SQL = """
WITH latest_setup AS (
    SELECT s.ticker AS ticker, s.timeframe AS timeframe, s.asof AS asof,
           s.signal AS signal, s.target AS target, s.stop AS stop,
           s.payoff AS payoff, s.ret AS ret
    FROM setups s
    JOIN (
        SELECT ticker, timeframe, MAX(asof) AS asof
        FROM setups
        {where}
        GROUP BY ticker, timeframe
    ) m ON m.ticker = s.ticker AND m.timeframe = s.timeframe AND m.asof = s.asof
),
latest_candle AS (
    SELECT c.ticker AS ticker, c.timeframe AS timeframe, c.open AS open, c.close AS close
    FROM candles c
    JOIN (
        SELECT ticker, timeframe, MAX(ts) AS ts
        FROM candles
        {where}
        GROUP BY ticker, timeframe
    ) m ON m.ticker = c.ticker AND m.timeframe = c.timeframe AND m.ts = c.ts
)
SELECT ls.ticker AS ticker, ls.timeframe AS timeframe, ls.asof AS asof,
       ls.signal AS signal, ls.target AS target, ls.stop AS stop,
       ls.payoff AS payoff, ls.ret AS ret, lc.open AS open, lc.close AS close
FROM latest_setup ls
LEFT JOIN latest_candle lc
       ON lc.ticker = ls.ticker AND lc.timeframe = ls.timeframe
ORDER BY ls.ticker, CASE ls.timeframe WHEN '1d' THEN 0 ELSE 1 END
"""

_SNAPSHOT_SQL_BY_TF = _SNAPSHOT_SQL.format(where="WHERE timeframe = ?")
_SNAPSHOT_SQL_ANY = _SNAPSHOT_SQL.format(where="")


def _disclaimer(config: Dict[str, Any]) -> str:
    return config.get("compliance", {}).get("disclaimer", DEFAULT_DISCLAIMER)


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
        "disclaimer": _disclaimer(config)
    }


def handle_api_status_ollama() -> Dict[str, Any]:
    """Handle GET /api/status_ollama."""
    status = verificar_status_ollama()
    return {
        "sucesso": True,
        "dados": status,
        "erro": None
    }


def _load_snapshot(timeframe: Optional[str]) -> Dict[str, Dict[str, Any]]:
    """Load the latest setup + last candle for every ticker in a single query."""
    if timeframe:
        sql, params = _SNAPSHOT_SQL_BY_TF, [timeframe, timeframe]
    else:
        sql, params = _SNAPSHOT_SQL_ANY, []

    with pooled_db() as conn:
        rows = conn.execute(sql, params).fetchall()

    snapshot: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        # The first row per ticker wins: the query orders the daily timeframe first.
        snapshot.setdefault(row["ticker"], dict(row))
    return snapshot


def _baseline_asset(ticker: str, modo: str = MODO_PADRAO) -> Dict[str, Any]:
    """Build the labelled placeholder entry used before real data is stored."""
    base_p = BASELINE_PRICES_DAY.get(ticker, 100.0) if modo == "day" else BASELINE_PRICES.get(ticker, 25.0)
    trend = "NEUTRO" if modo == "day" else (
        "ALTA" if ticker in BASELINE_ALTA else ("BAIXA" if ticker in BASELINE_BAIXA else "NEUTRO")
    )

    # Reuse the canonical setup builder so the baseline never drifts from the
    # real setup logic (target, stop, payoff and projection are derived from
    # the same formula the API uses when real data is available).
    from aguia.forecast.signals import build_setup
    setup = build_setup(
        preco=base_p,
        sma200=base_p * 0.95,
        wma30=base_p * 0.98,
        atr14=base_p * 0.025,
    )

    return {
        "ticker": ticker,
        "rotulo": rotulo_ativo(ticker, modo),
        "categoria": categoria_do_ativo(ticker),
        "setor": setor_do_ativo(ticker),
        "price": setup["preco"],
        "preco": setup["preco"],
        "trend": setup["tendencia"],
        "tendencia": setup["tendencia"],
        "trendText": setup["tendencia_texto"],
        "returnPct": setup["projecao_pct"],
        "target": setup["alvo"],
        "alvo": setup["alvo"],
        "stop": setup["stop"],
        "payoff": setup["payoff"],
        "dayVar": "+0.85%",
        "asof": None,
        "simulado": True,
    }


def handle_api_modos() -> Dict[str, Any]:
    """Handle GET /api/modos — the mode catalogue consumed by the front-end."""
    return {
        "sucesso": True,
        "dados": catalogo_modos(),
        "erro": None
    }


def handle_api_acoes(modo: Optional[str] = None) -> Dict[str, Any]:
    """Handle GET /api/acoes, GET /api/assets, and GET /api/universe."""
    modo_id = normalizar_modo(modo)
    definicao = get_modo(modo_id)
    universe = universo_do_modo(modo_id)
    init_db()

    default_tf = definicao["timeframe"]
    snapshot = _load_snapshot(default_tf)
    if not snapshot:
        # No data for the default timeframe yet: fall back to any stored one.
        snapshot = _load_snapshot(None)

    assets: List[Dict[str, Any]] = []

    for ticker in universe:
        row = snapshot.get(ticker)
        if not row or row.get("close") is None:
            assets.append(_baseline_asset(ticker, modo_id))
            continue

        price = round(float(row["close"]), 2)
        prev_open = float(row["open"])
        day_var_pct = round(((price - prev_open) / prev_open) * 100, 2) if prev_open else 0.0
        sign = "+" if day_var_pct >= 0 else ""
        trend = row["signal"]
        payoff_val = row["payoff"]
        payoff_str = f"{payoff_val:.2f} : 1" if payoff_val is not None else "—"

        assets.append({
            "ticker": ticker,
            "rotulo": rotulo_ativo(ticker, modo_id),
            "categoria": categoria_do_ativo(ticker),
            "setor": setor_do_ativo(ticker),
            "price": price,
            "preco": price,
            "trend": trend,
            "tendencia": trend,
            "trendText": TREND_TEXT.get(trend, "LATERAL (NEUTRAL)"),
            "returnPct": round((row["ret"] or 0.0) * 100, 2),
            "target": row["target"],
            "alvo": row["target"],
            "stop": row["stop"],
            "payoff": payoff_str,
            "dayVar": f"{sign}{day_var_pct:.2f}%",
            "asof": row["asof"],
            "simulado": False,
        })

    return {
        "sucesso": True,
        "modo": modo_id,
        "total": len(assets),
        "assets": assets,
        "dados": assets,
        "erro": None
    }


def _round_or_none(values: np.ndarray) -> List[Optional[float]]:
    """Round a float array, mapping NaN to None so the JSON stays valid."""
    out: List[Optional[float]] = []
    for value in values:
        if value is None or (isinstance(value, float) and math.isnan(value)):
            out.append(None)
        else:
            out.append(round(float(value), 2))
    return out


def _build_candles(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Serialise the last candles of a DataFrame without row-by-row pandas access."""
    recent = df.tail(CHART_CANDLES)
    if recent.empty:
        return []

    dates = [
        ts.strftime("%Y-%m-%d") if hasattr(ts, "strftime") else str(ts)[:10]
        for ts in recent.index
    ]
    opens = _round_or_none(recent["open"].to_numpy(dtype=float))
    highs = _round_or_none(recent["high"].to_numpy(dtype=float))
    lows = _round_or_none(recent["low"].to_numpy(dtype=float))
    closes = _round_or_none(recent["close"].to_numpy(dtype=float))
    volumes = _round_or_none(recent["volume"].to_numpy(dtype=float))
    wma30 = _round_or_none(recent["wma30"].to_numpy(dtype=float)) if "wma30" in recent else [None] * len(dates)
    sma200 = _round_or_none(recent["sma200"].to_numpy(dtype=float)) if "sma200" in recent else [None] * len(dates)

    return [
        {
            "date": date,
            "open": o,
            "high": h,
            "low": l,
            "close": c,
            "volume": v,
            "wma30": w,
            "sma200": s,
        }
        for date, o, h, l, c, v, w, s in zip(
            dates, opens, highs, lows, closes, volumes, wma30, sma200
        )
    ]


def handle_api_dados(
    ticker: str,
    modo: Optional[str] = None,
    intervalo: Optional[str] = None
) -> Dict[str, Any]:
    """
    Handle GET /api/dados?ticker=...&modo=day|swing&intervalo=...

    Real market data from Yahoo Finance, calculated indicators, and the
    Ollama/deterministic rationale for the active trading mode.
    """
    modo_id = normalizar_modo(modo)
    definicao = get_modo(modo_id)
    intervalo_ativo = normalizar_intervalo(modo_id, intervalo)
    timeframe = definicao["timeframe"] if modo_id == "swing" else intervalo_ativo

    ticker = ticker.upper().strip()
    config = load_config()

    cache_key = f"{ticker}|{modo_id}|{intervalo_ativo}"
    now = time.monotonic()
    with _analysis_lock:
        cached = _analysis_cache.get(cache_key)
        if cached and (now - cached[0]) < ANALYSIS_CACHE_TTL_SECONDS:
            dados = cached[1]
            return {
                "sucesso": True,
                "dados": dados,
                "asset": dados,  # Backward compatibility
                "erro": None
            }

    try:
        df = obter_dados_mercado(
            ticker,
            periodo=periodo_yahoo(modo_id, intervalo_ativo),
            intervalo=intervalo_ativo,
            mercado=definicao["mercado"],
        )
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

    setup = build_setup(
        preco=preco,
        sma200=float(last_row["sma200"]) if pd.notna(last_row["sma200"]) else None,
        wma30=float(last_row["wma30"]) if pd.notna(last_row["wma30"]) else None,
        atr14=float(last_row["atr14"]) if pd.notna(last_row["atr14"]) else None,
    )

    candles_json = _build_candles(df)

    setup_dict = {
        "ticker": ticker,
        "preco": setup["preco"],
        "alvo": setup["alvo"],
        "stop": setup["stop"],
        "payoff": setup["payoff"],
        "projecao_pct": setup["projecao_pct"],
        "risco_pct": setup["risco_pct"],
        "tendencia": setup["tendencia"],
        "indicadores": setup["indicadores"],
        "modo": modo_id,
        "intervalo": intervalo_ativo,
        "horizonte": definicao["horizonte"],
        "moeda": definicao["moeda"],
        "vela_anterior": {
            "abertura": round(float(prev_row["open"]), 2),
            "maxima": round(float(prev_row["high"]), 2),
            "minima": round(float(prev_row["low"]), 2),
            "fechamento": round(float(prev_row["close"]), 2),
        },
    }

    # Generate the operational tips via Ollama / Deterministic Fallback
    resumo_texto, fonte_resumo = gerar_racional_ia(setup_dict, modo=modo_id)

    # Persist setup and candles into SQLite
    try:
        init_db()
        with pooled_db() as conn:
            now_iso = datetime.now(timezone.utc).isoformat()
            upsert_setup(conn, {
                "ticker": ticker,
                "timeframe": timeframe,
                "asof": now_iso,
                "signal": setup["tendencia"],
                "entry": setup["preco"],
                "target": setup["alvo"],
                "stop": setup["stop"],
                "payoff": setup["payoff_num"],
                "ret": setup["projecao_pct"] / 100.0,
                "atr_pct": setup["indicadores"]["atr14"] / setup["preco"] if setup["preco"] else 0.0,
                "p_up": 0.65 if setup["tendencia"] == "ALTA" else (0.35 if setup["tendencia"] == "BAIXA" else 0.50)
            })

            upsert_candles(conn, [{
                "ticker": ticker,
                "timeframe": timeframe,
                "ts": c["date"],
                "open": c["open"],
                "high": c["high"],
                "low": c["low"],
                "close": c["close"],
                "volume": c["volume"],
                "source": "yfinance",
                "adjusted": 1
            } for c in candles_json])

            upsert_explanation(conn, {
                "ticker": ticker,
                "timeframe": timeframe,
                "asof": now_iso,
                "rationale": resumo_texto,
                "source": fonte_resumo,
                "model": fonte_resumo,
                "facts_hash": hash_facts(setup_dict)
            })
            prune_history(conn, ticker, timeframe)
    except Exception:
        logger.exception("Falha ao persistir a análise de %s", ticker)

    dados = {
        "ticker": ticker,
        "rotulo": rotulo_ativo(ticker, modo_id),
        "categoria": categoria_do_ativo(ticker),
        "setor": setor_do_ativo(ticker),
        "modo": modo_id,
        "intervalo": intervalo_ativo,
        "timeframe": timeframe,
        "horizonte": definicao["horizonte"],
        "moeda": definicao["moeda"],
        "contexto": definicao["contexto"],
        "preco": setup["preco"],
        "price": setup["preco"],
        "variacao_dia": variacao_dia,
        "dayVar": variacao_dia,
        "tendencia": setup["tendencia"],
        "trend": setup["tendencia"],
        "tendencia_texto": setup["tendencia_texto"],
        "trendText": setup["tendencia_texto"],
        "alvo": setup["alvo"],
        "target": setup["alvo"],
        "projecao_pct": setup["projecao_pct"],
        "returnPct": setup["projecao_pct"],
        "stop": setup["stop"],
        "risco_pct": setup["risco_pct"],
        "payoff": setup["payoff"],
        "resumo": resumo_texto,
        "fonte_resumo": fonte_resumo,
        "indicadores": setup["indicadores"],
        "candles": candles_json,
        "disclaimer": _disclaimer(config)
    }

    with _analysis_lock:
        _analysis_cache[cache_key] = (time.monotonic(), dados)

    return {
        "sucesso": True,
        "dados": dados,
        "asset": dados,  # Backward compatibility
        "erro": None
    }


def handle_api_analise(ticker: str) -> Dict[str, Any]:
    """
    Handle GET /api/analise?ticker=...

    Backward compatible alias of ``/api/dados`` in Swing Trade mode.
    """
    return handle_api_dados(ticker, modo=MODO_PADRAO)


def handle_api_estrategia_macro_jr(payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    POST /api/estrategia - Estratégia MACRO JR
    """
    if payload is None:
        payload = {}
    try:
        params = params_from_dict(payload.get("params") or payload)
        if getattr(params, "InpADXMinLevel", 25.0) < 25.0:
            params.InpADXMinLevel = 25.0

        modo_id = normalizar_modo(payload.get("modo"))
        definicao = get_modo(modo_id)
        universo = universo_do_modo(modo_id)
        ticker = payload.get("ticker")
        init_db()

        periodo = periodo_yahoo(modo_id, definicao["intervalo"])
        intervalo = definicao["intervalo"]

        # Se ticker específico, retornar análise detalhada para o ativo selecionado
        if ticker:
            ticker = str(ticker).upper().strip()
            try:
                df = obter_dados_mercado(
                    ticker,
                    periodo=periodo,
                    intervalo=intervalo,
                    mercado=definicao["mercado"],
                )
                detalhado = calcular_macro_jr_detalhado(df, params)
                detalhado["ticker"] = ticker
                detalhado["rotulo"] = rotulo_ativo(ticker, modo_id)
                detalhado["moeda"] = definicao["moeda"]
                detalhado["modo"] = modo_id
                return {
                    "sucesso": True,
                    "dados": detalhado,
                    "erro": None,
                }
            except Exception as e:
                return {
                    "sucesso": False,
                    "dados": None,
                    "erro": f"Erro ao analisar {ticker}: {str(e)}",
                }

        df_por_ticker: Dict[str, Any] = {}
        for t in universo:
            try:
                df = obter_dados_mercado(
                    t,
                    periodo=periodo,
                    intervalo=intervalo,
                    mercado=definicao["mercado"],
                )
                if df is not None and not df.empty and len(df) > 250:
                    df_por_ticker[t] = df
            except Exception:
                continue

        resultados = filtrar_ativos_macro_jr(df_por_ticker, params)
        enriquecidos = []
        for r in resultados:
            t = r["ticker"]
            enriquecidos.append(
                {
                    **r,
                    "rotulo": rotulo_ativo(t, modo_id),
                    "categoria": categoria_do_ativo(t),
                    "setor": setor_do_ativo(t),
                    "moeda": definicao["moeda"],
                    "modo": modo_id,
                }
            )

        return {
            "sucesso": True,
            "dados": {
                "ativos": enriquecidos,
                "total": len(enriquecidos),
                "params": params_to_dict(params),
                "modo": modo_id,
            },
            "erro": None,
        }
    except Exception as e:
        return {
            "sucesso": False,
            "dados": None,
            "erro": f"Erro ao executar Estratégia MACRO JR: {str(e)}",
        }

