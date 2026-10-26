"""Technical indicators with strict window and Wilder smoothing logic."""

import numpy as np
import pandas as pd


def calc_sma(series: pd.Series, window: int = 200) -> pd.Series:
    """
    Calculate Simple Moving Average (SMA).

    Returns NaN for all rows prior to the full window (never shrinks window).
    """
    if len(series) < window:
        return pd.Series(np.nan, index=series.index, dtype=float)
    return series.rolling(window=window, min_periods=window).mean()


def calc_wma(series: pd.Series, window: int = 30) -> pd.Series:
    """
    Calculate Weighted Moving Average (WMA) with linear weights 1..window.

    Newest candle receives weight = window.
    Returns NaN for all rows prior to the full window (never shrinks window).

    The sliding window is evaluated with a single matrix product instead of a
    per-row Python callback, which keeps the cost flat for long histories.
    """
    n = len(series)
    if n < window:
        return pd.Series(np.nan, index=series.index, dtype=float)

    values = series.to_numpy(dtype=float)
    weights = np.arange(1, window + 1, dtype=float)

    windows = np.lib.stride_tricks.sliding_window_view(values, window)
    result = np.full(n, np.nan, dtype=float)
    result[window - 1:] = (windows @ weights) / weights.sum()

    return pd.Series(result, index=series.index, dtype=float)


def calc_atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
    """
    Calculate Average True Range (ATR) using Wilder's smoothing.

    Seeded with the simple arithmetic mean of the first `window` true ranges.
    Returns NaN for the first `window - 1` candles.
    """
    n = len(high)
    if n < window:
        return pd.Series(np.nan, index=high.index, dtype=float)

    # Compute True Range (TR)
    h = high.to_numpy(dtype=float)
    l = low.to_numpy(dtype=float)
    c = close.to_numpy(dtype=float)

    prev_close = np.empty(n, dtype=float)
    prev_close[0] = c[0]
    prev_close[1:] = c[:-1]

    tr = np.maximum.reduce([
        h - l,
        np.abs(h - prev_close),
        np.abs(l - prev_close),
    ])
    tr[0] = h[0] - l[0]

    # Wilder smoothing
    atr = np.full(n, np.nan, dtype=float)
    # First valid ATR at index window - 1 is simple mean of first `window` TRs
    atr[window - 1] = float(np.mean(tr[:window]))

    # Subsequent values use Wilder recursive smoothing
    mult = window - 1
    for t in range(window, n):
        atr[t] = (atr[t - 1] * mult + tr[t]) / window

    return pd.Series(atr, index=high.index, dtype=float)
