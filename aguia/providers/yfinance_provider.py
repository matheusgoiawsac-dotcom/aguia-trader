"""Market data provider using yfinance with rate-limiting and indicators."""

from datetime import datetime, timezone
import time
from typing import Dict, Optional, Tuple
import numpy as np
import pandas as pd
import yfinance as yf

from aguia.indicators import calc_sma, calc_wma, calc_atr

# In-memory candle cache: (ticker, timeframe) -> (timestamp, DataFrame)
_CACHE: Dict[Tuple[str, str], Tuple[float, pd.DataFrame]] = {}
CACHE_TTL_SECONDS = 300  # 5 minutes


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Flatten yfinance MultiIndex columns and normalize to lowercase."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0].lower() if isinstance(col, tuple) else str(col).lower() for col in df.columns]
    else:
        df.columns = [str(col).lower() for col in df.columns]
    return df


def obter_dados_mercado(
    ticker: str,
    periodo: str = "2y",
    intervalo: str = "1d",
    use_cache: bool = True
) -> pd.DataFrame:
    """
    Fetch market data for a B3 ticker via Yahoo Finance, normalize columns,
    and compute technical indicators (SMA 200, WMA 30, ATR 14).
    """
    clean_ticker = ticker.upper().replace(".SA", "").strip()
    cache_key = (clean_ticker, intervalo)

    now = time.time()
    if use_cache and cache_key in _CACHE:
        cached_time, cached_df = _CACHE[cache_key]
        if now - cached_time < CACHE_TTL_SECONDS:
            return cached_df.copy()

    symbol = f"{clean_ticker}.SA"
    period_map = {"6m": "6mo", "1m": "1mo", "3m": "3mo"}
    yf_period = period_map.get(periodo.lower(), periodo)

    # Retry with exponential backoff on network errors
    max_retries = 3
    delay = 1.0
    last_err: Optional[Exception] = None

    for attempt in range(max_retries):
        try:
            yf_ticker = yf.Ticker(symbol)
            df = yf_ticker.history(period=yf_period, interval=intervalo, auto_adjust=True)
            if df is not None and not df.empty:
                break
        except Exception as e:
            last_err = e
            time.sleep(delay)
            delay *= 2.0
    else:
        if last_err:
            raise RuntimeError(f"Erro ao obter dados de {symbol} no Yahoo Finance: {last_err}")
        raise ValueError(f"Nenhum dado retornado para {symbol}")

    df = _normalize_columns(df)

    # Required columns check
    required = ["open", "high", "low", "close", "volume"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes em {symbol}: {missing}")

    df = df[required].copy()
    df.dropna(subset=["close"], inplace=True)

    if df.empty:
        raise ValueError(f"Série temporal vazia para {symbol}")

    # Drop incomplete in-progress candle if last candle timestamp is today and market is active
    # By default, use all completed historical rows
    df["close"] = df["close"].astype(float)
    df["open"] = df["open"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["volume"] = df["volume"].astype(float)

    # Filter out invalid candles with non-positive prices
    df = df[(df["open"] > 0) & (df["high"] > 0) & (df["low"] > 0) & (df["close"] > 0)].copy()

    # Drop in-progress incomplete candle per AGENTS.md rule
    if len(df) > 1 and (df.iloc[-1]["volume"] == 0 or df.iloc[-1]["high"] == df.iloc[-1]["low"]):
        df = df.iloc[:-1].copy()

    # Calculate technical indicators
    df["sma200"] = calc_sma(df["close"], window=200)
    df["wma30"] = calc_wma(df["close"], window=30)
    df["atr14"] = calc_atr(df["high"], df["low"], df["close"], window=14)

    # Cache result
    _CACHE[cache_key] = (now, df)
    return df.copy()
