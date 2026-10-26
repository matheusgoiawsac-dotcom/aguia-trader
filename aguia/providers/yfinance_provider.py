"""Market data provider using yfinance with rate-limiting and indicators."""

import logging
import re
import time
from collections import OrderedDict
from typing import Dict, Optional, Tuple
import pandas as pd
import yfinance as yf

from aguia.indicators import calc_sma, calc_wma, calc_atr
from aguia.modes import simbolo_yahoo

logger = logging.getLogger("aguia.providers")

# Bounded LRU cache: (ticker, period, interval) -> (timestamp, DataFrame).
# An unbounded cache silently grows with every distinct ticker the user
# clicks, so the cap is enforced by evicting the least-recently-used entry.
_CACHE: "OrderedDict[Tuple[str, str, str], Tuple[float, pd.DataFrame]]" = OrderedDict()
CACHE_MAX_ENTRIES = 48
CACHE_TTL_SECONDS = 300  # 5 minutes

# Yahoo Finance keeps a short history for intraday intervals. Asking for more
# either errors out or silently truncates, so the range is clamped and logged.
MAX_INTRADAY_PERIOD_DAYS = {
    "1m": 7,
    "2m": 60,
    "5m": 60,
    "15m": 60,
    "30m": 60,
    "60m": 730,
    "90m": 60,
}

# Yahoo's own throttling: 429 responses need a longer backoff than a transient
# network blip, so the retry schedule is asymmetric.
_RETRY_SCHEDULE = (1.0, 2.5, 6.0)

# Aliases for period strings that yfinance accepts but the caller may pass
# in a different shorthand. The trading modes (modes.py) use canonical forms
# ("5d", "15d", "60d", "2y"), so this map is only a safety net.
_PERIOD_ALIASES = {
    "1m": "1mo",
    "3m": "3mo",
    "6m": "6mo",
}

_PERIOD_RE = re.compile(r"^(\d+)([dmo])$")


def _cache_put(key: Tuple[str, str, str], value: Tuple[float, pd.DataFrame]) -> None:
    """Insert into the LRU cache, evicting the oldest entry when full."""
    _CACHE[key] = value
    _CACHE.move_to_end(key)
    while len(_CACHE) > CACHE_MAX_ENTRIES:
        _CACHE.popitem(last=False)


def _cache_get(key: Tuple[str, str, str]) -> Optional[Tuple[float, pd.DataFrame]]:
    """Return a cached value, promoting it to most-recently-used, or None."""
    value = _CACHE.get(key)
    if value is not None:
        _CACHE.move_to_end(key)
    return value


def _period_to_days(period: str) -> Optional[int]:
    """Translate a Yahoo period string ('6mo', '2y', '60d') into a day count."""
    if not period or period == "max":
        return None
    match = _PERIOD_RE.match(period.strip().lower())
    if not match:
        return None
    amount = int(match.group(1))
    unit = match.group(2)
    if unit == "d":
        return amount
    if unit == "m":
        return amount * 30
    return amount * 365


def _clamp_period(periodo: str, intervalo: str) -> str:
    """Clamp intraday ranges to what Yahoo Finance actually serves."""
    limit = MAX_INTRADAY_PERIOD_DAYS.get(intervalo)
    if limit is None:
        return periodo

    requested = _period_to_days(periodo)
    if requested is None or requested <= limit:
        return periodo

    clamped = f"{limit}d"
    logger.warning(
        "Yahoo intraday range clamped for %s: %s -> %s", intervalo, periodo, clamped
    )
    return clamped


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
    use_cache: bool = True,
    mercado: str = "b3"
) -> pd.DataFrame:
    """
    Fetch market data for a ticker via Yahoo Finance, normalize columns,
    and compute technical indicators (SMA 200, WMA 30, ATR 14).

    ``mercado`` selects the symbol namespace: ``b3`` appends the ``.SA``
    suffix, while ``global`` keeps the raw symbol (SPY, DIA, GC=F, BTC-USD).
    """
    clean_ticker = ticker.upper().strip()
    periodo = periodo.lower()
    intervalo = intervalo.lower()
    symbol = simbolo_yahoo(clean_ticker, mercado)
    cache_key = (symbol, periodo, intervalo)

    now = time.time()
    if use_cache:
        cached = _CACHE.get(cache_key)
        if cached is not None and (now - cached[0]) < CACHE_TTL_SECONDS:
            return cached[1].copy()

    period_map = _PERIOD_ALIASES
    yf_period = period_map.get(periodo, periodo)
    yf_period = _clamp_period(yf_period, intervalo)

    # Retry with exponential backoff on network errors. Yahoo throttles with
    # HTTP 429, so the schedule is asymmetric: short initial wait, then
    # progressively longer pauses before giving up.
    last_err: Optional[Exception] = None
    df = None

    for attempt, delay in enumerate(_RETRY_SCHEDULE):
        try:
            yf_ticker = yf.Ticker(symbol)
            df = yf_ticker.history(period=yf_period, interval=intervalo, auto_adjust=True)
            if df is not None and not df.empty:
                break
        except Exception as e:
            last_err = e
            time.sleep(delay)
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

    # Single vectorised cast instead of one conversion per column
    df = df.astype(float)

    # Filter out invalid candles with non-positive prices
    df = df[(df["open"] > 0) & (df["high"] > 0) & (df["low"] > 0) & (df["close"] > 0)].copy()

    # Drop in-progress incomplete candle per AGENTS.md rule
    if len(df) > 1:
        last = df.iloc[-1]
        if last["volume"] == 0 or last["high"] == last["low"]:
            df = df.iloc[:-1].copy()

    # Calculate technical indicators
    df["sma200"] = calc_sma(df["close"], window=200)
    df["wma30"] = calc_wma(df["close"], window=30)
    df["atr14"] = calc_atr(df["high"], df["low"], df["close"], window=14)

    # Cache result
    if use_cache:
        _CACHE[cache_key] = (now, df)
    return df.copy()
