"""Tests for Kronos engine, FakePredictor, and quantitative signal classification."""

import numpy as np
import pandas as pd

from aguia.forecast.signals import classify_setup
from aguia.forecast.kronos_engine import FakePredictor, KronosEngine


def test_classify_setup_alta():
    # Setup with strong probability of up and positive return
    entry = 50.00
    target = 54.00
    atr14 = 2.00
    p_up = 0.65
    res = classify_setup(entry, target, atr14, p_up)
    assert res["signal"] == "ALTA"
    assert res["signal_text"] == "ALTA (BULLISH)"
    assert res["entry"] == 50.00
    assert res["target"] == 54.00
    assert res["stop"] == 47.00
    assert res["payoff_num"] >= 1.0


def test_classify_setup_baixa():
    # Setup with bearish expectation
    entry = 60.00
    target = 54.00
    atr14 = 2.50
    p_up = 0.30
    res = classify_setup(entry, target, atr14, p_up)
    assert res["signal"] == "BAIXA"
    assert res["signal_text"] == "BAIXA (BEARISH)"
    assert res["target"] < res["entry"]
    assert res["stop"] > res["entry"]


def test_classify_setup_neutro():
    # Setup with weak edge
    entry = 30.00
    target = 30.20
    atr14 = 1.20
    p_up = 0.51
    res = classify_setup(entry, target, atr14, p_up)
    assert res["signal"] == "NEUTRO"
    assert res["signal_text"] == "LATERAL (NEUTRAL)"


def test_fake_predictor_output():
    dates = pd.date_range("2026-01-01", periods=30, freq="B")
    data = {
        "open": np.linspace(20, 25, 30),
        "high": np.linspace(21, 26, 30),
        "low": np.linspace(19, 24, 30),
        "close": np.linspace(20.5, 25.5, 30),
        "volume": np.full(30, 100000.0)
    }
    df = pd.DataFrame(data, index=dates)

    future_dates = pd.date_range("2026-02-15", periods=14, freq="B")
    predictor = FakePredictor(seed=123)
    pred_df = predictor.predict(df, x_timestamp=dates, y_timestamp=future_dates, pred_len=14)

    assert len(pred_df) == 14
    for col in ["open", "high", "low", "close", "volume", "amount"]:
        assert col in pred_df.columns
        assert not pred_df[col].isna().any()


def test_kronos_engine_forecast_14d():
    dates = pd.date_range("2026-01-01", periods=60, freq="B")
    data = {
        "open": np.linspace(30, 40, 60),
        "high": np.linspace(31, 41, 60),
        "low": np.linspace(29, 39, 60),
        "close": np.linspace(30.5, 40.5, 60),
        "volume": np.full(60, 500000.0)
    }
    df = pd.DataFrame(data, index=dates)

    engine = KronosEngine.get_instance()
    forecast = engine.forecast_14d(df, n_samples=5)

    assert len(forecast["steps"]) == 14
    assert "target" in forecast
    assert "p_up" in forecast
    assert 0.0 <= forecast["p_up"] <= 1.0

    for step in forecast["steps"]:
        assert step["p10"] <= step["median"] <= step["p90"]
