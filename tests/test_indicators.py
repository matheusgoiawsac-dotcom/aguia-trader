"""Tests for technical indicators: SMA, WMA, and ATR with Wilder smoothing.

All fixtures are computed by hand with step-by-step arithmetic shown in comments.
"""

import math
import numpy as np
import pandas as pd
import pytest

from aguia.indicators import calc_sma, calc_wma, calc_atr


def test_sma_hand_computed_fixture():
    """
    Hand-computed SMA(window=3):
    Prices: [10.0, 20.0, 30.0, 40.0, 50.0]
    Window k = 3
    
    t=0: count 1 < 3 -> NaN
    t=1: count 2 < 3 -> NaN
    t=2: (10 + 20 + 30) / 3 = 60 / 3 = 20.0
    t=3: (20 + 30 + 40) / 3 = 90 / 3 = 30.0
    t=4: (30 + 40 + 50) / 3 = 120 / 3 = 40.0
    """
    prices = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])
    result = calc_sma(prices, window=3)

    assert math.isnan(result.iloc[0])
    assert math.isnan(result.iloc[1])
    assert pytest.approx(result.iloc[2]) == 20.0
    assert pytest.approx(result.iloc[3]) == 30.0
    assert pytest.approx(result.iloc[4]) == 40.0


def test_sma200_nan_before_full_window():
    """SMA 200 must be NaN until exactly 200 candles exist."""
    # 199 candles: all must be NaN
    short_series = pd.Series(np.full(199, 100.0))
    res_short = calc_sma(short_series, window=200)
    assert res_short.isna().all()

    # 200 candles: indices 0..198 are NaN, index 199 is 100.0
    full_series = pd.Series(np.full(200, 100.0))
    res_full = calc_sma(full_series, window=200)
    assert res_full.iloc[:199].isna().all()
    assert pytest.approx(res_full.iloc[199]) == 100.0


def test_wma_hand_computed_fixture():
    """
    Hand-computed WMA(window=3):
    Prices: [10.0, 20.0, 30.0, 40.0, 50.0]
    Window k = 3
    Weights: 1, 2, 3 -> Sum of weights W = 1 + 2 + 3 = 6
    
    t=0: count 1 < 3 -> NaN (window is NEVER shrunk)
    t=1: count 2 < 3 -> NaN
    t=2: (10*1 + 20*2 + 30*3) / 6 = (10 + 40 + 90) / 6 = 140 / 6 = 23.333333...
    t=3: (20*1 + 30*2 + 40*3) / 6 = (20 + 60 + 120) / 6 = 200 / 6 = 33.333333...
    t=4: (30*1 + 40*2 + 50*3) / 6 = (30 + 80 + 150) / 6 = 260 / 6 = 43.333333...
    """
    prices = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])
    result = calc_wma(prices, window=3)

    assert math.isnan(result.iloc[0])
    assert math.isnan(result.iloc[1])
    assert pytest.approx(result.iloc[2]) == 140.0 / 6.0
    assert pytest.approx(result.iloc[3]) == 200.0 / 6.0
    assert pytest.approx(result.iloc[4]) == 260.0 / 6.0


def test_wma30_nan_before_full_window():
    """WMA 30 must be NaN until exactly 30 candles exist."""
    # 29 candles: all must be NaN
    short_series = pd.Series(np.full(29, 50.0))
    res_short = calc_wma(short_series, window=30)
    assert res_short.isna().all()

    # 30 candles: indices 0..28 are NaN, index 29 is 50.0
    full_series = pd.Series(np.full(30, 50.0))
    res_full = calc_wma(full_series, window=30)
    assert res_full.iloc[:29].isna().all()
    assert pytest.approx(res_full.iloc[29]) == 50.0


def test_atr_hand_computed_fixture():
    """
    Hand-computed ATR(window=3) with Wilder smoothing:
    
    Bar 0: H=12, L=10, C=11 -> TR_0 = 12 - 10 = 2.0
    Bar 1: H=14, L=9,  C=13 -> C_prev=11 -> TR_1 = max(14-9, |14-11|, |9-11|) = max(5, 3, 2) = 5.0
    Bar 2: H=15, L=12, C=14 -> C_prev=13 -> TR_2 = max(15-12, |15-13|, |12-13|) = max(3, 2, 1) = 3.0
    Bar 3: H=16, L=13, C=15 -> C_prev=14 -> TR_3 = max(16-13, |16-14|, |13-14|) = max(3, 2, 1) = 3.0
    Bar 4: H=18, L=14, C=17 -> C_prev=15 -> TR_4 = max(18-14, |18-15|, |14-15|) = max(4, 3, 1) = 4.0
    
    Window n = 3:
    t=0: NaN
    t=1: NaN
    t=2: First ATR is simple mean of first 3 TRs:
         ATR_2 = (2.0 + 5.0 + 3.0) / 3 = 10.0 / 3 = 3.333333...
    t=3: Wilder smoothing:
         ATR_3 = (ATR_2 * 2 + TR_3) / 3 = ((10/3)*2 + 3) / 3 = (20/3 + 9/3) / 3 = 29/9 = 3.222222...
    t=4: Wilder smoothing:
         ATR_4 = (ATR_3 * 2 + TR_4) / 3 = ((29/9)*2 + 4) / 3 = (58/9 + 36/9) / 3 = 94/27 = 3.481481...
    """
    high = pd.Series([12.0, 14.0, 15.0, 16.0, 18.0])
    low = pd.Series([10.0, 9.0, 12.0, 13.0, 14.0])
    close = pd.Series([11.0, 13.0, 14.0, 15.0, 17.0])

    result = calc_atr(high, low, close, window=3)

    assert math.isnan(result.iloc[0])
    assert math.isnan(result.iloc[1])
    assert pytest.approx(result.iloc[2]) == 10.0 / 3.0
    assert pytest.approx(result.iloc[3]) == 29.0 / 9.0
    assert pytest.approx(result.iloc[4]) == 94.0 / 27.0


def test_atr14_nan_before_full_window():
    """ATR 14 must be NaN for the first 13 candles."""
    n = 20
    high = pd.Series(np.full(n, 10.0))
    low = pd.Series(np.full(n, 8.0))
    close = pd.Series(np.full(n, 9.0))

    result = calc_atr(high, low, close, window=14)

    assert result.iloc[:13].isna().all()
    # TR is constant 2.0, so ATR should be 2.0 at index 13 and onward
    assert pytest.approx(result.iloc[13]) == 2.0
    assert pytest.approx(result.iloc[14]) == 2.0
    assert pytest.approx(result.iloc[19]) == 2.0
