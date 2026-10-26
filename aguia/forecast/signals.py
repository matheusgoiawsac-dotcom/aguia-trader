"""Quantitative setup calculation and heuristic signal classification."""

from typing import Any, Dict, Optional

TREND_TEXT = {
    "ALTA": "ALTA (BULLISH)",
    "BAIXA": "BAIXA (BEARISH)",
    "NEUTRO": "LATERAL (NEUTRAL)",
}


def _is_finite(value: Optional[float]) -> bool:
    """NaN-safe check for a finite float (None and NaN both return False)."""
    return value is not None and value == value


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
    risco_pct = round(abs((stop - entry) / entry) * 100, 2)

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


def build_setup(
    preco: float,
    sma200: Optional[float] = None,
    wma30: Optional[float] = None,
    atr14: Optional[float] = None
) -> Dict[str, Any]:
    """
    Build the canonical B3 setup from price and technical indicators.

    Single source of truth shared by the API layer and the refresh job, so the
    sidebar, the detail panel and the database can never disagree about the
    trend, target or stop of the same ticker.

    Missing indicators fall back to proportional proxies of the last price so a
    short history never produces a NaN setup.
    """
    preco = float(preco)
    if preco <= 0:
        raise ValueError("Price must be positive")

    sma200 = float(sma200) if _is_finite(sma200) else preco * 0.95
    wma30 = float(wma30) if _is_finite(wma30) else preco * 0.98
    atr14 = float(atr14) if _is_finite(atr14) else preco * 0.025

    is_alta = preco >= wma30 and wma30 >= (sma200 * 0.98)
    is_baixa = preco < wma30 and preco < sma200

    if is_alta:
        tendencia = "ALTA"
        alvo = round(preco + (1.6 * atr14), 2)
        stop = round(preco - (1.4 * atr14), 2)
    elif is_baixa:
        tendencia = "BAIXA"
        alvo = round(preco - (1.6 * atr14), 2)
        stop = round(preco + (1.4 * atr14), 2)
    else:
        tendencia = "NEUTRO"
        alvo = round(preco + (1.0 * atr14), 2)
        stop = round(preco - (1.0 * atr14), 2)

    gain = abs(alvo - preco)
    risk = abs(preco - stop)
    payoff_num = round(gain / risk, 2) if risk > 0 else 1.0

    return {
        "preco": round(preco, 2),
        "alvo": alvo,
        "stop": stop,
        "payoff": f"{payoff_num:.2f} : 1",
        "payoff_num": payoff_num,
        "tendencia": tendencia,
        "tendencia_texto": TREND_TEXT[tendencia],
        "projecao_pct": round(((alvo - preco) / preco) * 100, 2),
        "risco_pct": round(abs((stop - preco) / preco) * 100, 2),
        "indicadores": {
            "sma200": round(sma200, 2),
            "wma30": round(wma30, 2),
            "atr14": round(atr14, 2),
        },
    }
