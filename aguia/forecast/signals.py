"""Quantitative setup calculation and heuristic signal classification."""

from typing import Any, Dict, Optional
import numpy as np


def classify_setup(
    entry: float,
    target: float,
    atr14: float,
    p_up: float,
    wma30: Optional[float] = None,
    sma200: Optional[float] = None
) -> Dict[str, Any]:
    """
    Compute setup parameters and classify signal into ALTA, BAIXA, or NEUTRO.
    Follows B3 quantitative risk/reward parameters and Wilder ATR bands.
    """
    if entry <= 0:
        raise ValueError("Entry price must be positive")

    ret = (target - entry) / entry
    atr_pct = (atr14 / entry) if atr14 > 0 else 0.025

    is_long = (p_up >= 0.55 and ret > 0)
    is_short = (p_up <= 0.45 and ret < 0)

    if is_long:
        stop = round(entry - 1.5 * atr14, 2)
        gain = abs(target - entry)
        risk = abs(entry - stop)
        payoff = round(gain / risk, 2) if risk > 0 else 1.0

        if p_up >= 0.60 and ret >= 0.5 * atr_pct and payoff >= 1.0:
            signal = "ALTA"
            signal_text = "ALTA (BULLISH)"
        else:
            signal = "NEUTRO"
            signal_text = "LATERAL (NEUTRAL)"
    elif is_short:
        stop = round(entry + 1.5 * atr14, 2)
        gain = abs(entry - target)
        risk = abs(stop - entry)
        payoff = round(gain / risk, 2) if risk > 0 else 1.0

        if p_up <= 0.40 and ret <= -0.5 * atr_pct and payoff >= 1.0:
            signal = "BAIXA"
            signal_text = "BAIXA (BEARISH)"
        else:
            signal = "NEUTRO"
            signal_text = "LATERAL (NEUTRAL)"
    else:
        signal = "NEUTRO"
        signal_text = "LATERAL (NEUTRAL)"
        stop = round(entry - 1.0 * atr14, 2)
        payoff = 1.0

    projecao_pct = round(ret * 100, 2)
    risco_pct = round(((stop - entry) / entry) * 100, 2)

    return {
        "signal": signal,
        "signal_text": signal_text,
        "entry": round(entry, 2),
        "target": round(target, 2),
        "stop": round(stop, 2),
        "payoff": f"{payoff:.2f} : 1",
        "payoff_num": payoff,
        "ret": ret,
        "projecao_pct": projecao_pct,
        "risco_pct": risco_pct,
        "atr_pct": atr_pct,
        "p_up": round(p_up, 4)
    }
