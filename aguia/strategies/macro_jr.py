"""
Estratégia MACRO JR - Conversão do indicador MQL5 para Python
Utiliza Pandas/Numpy para calcular EMA, SMA, ADX, Bandas de Bollinger e ATR
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


@dataclass
class MacroJRParams:
    InpTrendPeriod: int = 20
    InpFastEMAPeriod: int = 9
    InpSMAInstitution: int = 50
    InpSMAMacro: int = 200
    InpADXPeriod: int = 14
    InpADXMinLevel: float = 25.0  # Alterado conforme especificação
    InpBBPeriod: int = 20
    InpBBDeviation: float = 2.0
    InpKeltnerMult: float = 1.5


def _ema(series: pd.Series, period: int) -> pd.Series:
    if period <= 0:
        return series.copy()
    return series.ewm(span=period, adjust=False).mean()


def _sma(series: pd.Series, period: int) -> pd.Series:
    if period <= 0:
        return series.copy()
    return series.rolling(window=period, min_periods=period).mean()


def _true_range(df: pd.DataFrame) -> pd.Series:
    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr


def _atr(df: pd.DataFrame, period: int) -> pd.Series:
    tr = _true_range(df)
    if period <= 0:
        return tr
    # Wilder's smoothing aproximado via RMA
    atr = tr.ewm(alpha=1.0 / period, adjust=False).mean()
    return atr


def _adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    if period <= 0:
        period = 14
    high = df["high"]
    low = df["low"]
    close = df["close"]

    up_move = high.diff()
    down_move = -low.diff()

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    plus_dm_s = pd.Series(plus_dm, index=df.index)
    minus_dm_s = pd.Series(minus_dm, index=df.index)

    tr = _true_range(df)
    atr_w = tr.ewm(alpha=1.0 / period, adjust=False).mean()

    plus_di = 100 * plus_dm_s.ewm(alpha=1.0 / period, adjust=False).mean() / atr_w.replace(0, np.nan)
    minus_di = 100 * minus_dm_s.ewm(alpha=1.0 / period, adjust=False).mean() / atr_w.replace(0, np.nan)

    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx = dx.ewm(alpha=1.0 / period, adjust=False).mean()
    return adx


def _bollinger_bands(df: pd.DataFrame, period: int = 20, deviation: float = 2.0) -> tuple[pd.Series, pd.Series, pd.Series]:
    close = df["close"]
    ma = _sma(close, period)
    std = close.rolling(window=period, min_periods=period).std(ddof=0)
    bb_upper = ma + deviation * std
    bb_lower = ma - deviation * std
    return bb_upper, ma, bb_lower


def calcular_macro_jr(df: pd.DataFrame, params: Optional[MacroJRParams] = None) -> pd.DataFrame:
    """
    Calcula os sinais da Estratégia MACRO JR conforme regras traduzidas do MQL5
    Retorna DataFrame com colunas: trendEMA, fastEMA, sma50, sma200, sma50_anterior,
    adx, bbUpper, bbMiddle, bbLower, keltnerUpper, keltnerLower, outOfSqueeze,
    trendIsStrong, macroAlta, macroBaixa, sinal (0=ALTA, 1=BAIXA, 2=LATERAL)
    """
    if params is None:
        params = MacroJRParams()

    out = df.copy()
    close = out["close"]
    high = out["high"]
    low = out["low"]

    # EMAs/SMAs
    out["trendEMA"] = _ema(close, params.InpTrendPeriod)
    out["fastEMA"] = _ema(close, params.InpFastEMAPeriod)
    out["sma50"] = _sma(close, params.InpSMAInstitution)
    out["sma200"] = _sma(close, params.InpSMAMacro)
    out["sma50_anterior"] = out["sma50"].shift(1)

    # ADX
    out["adx"] = _adx(out, params.InpADXPeriod)

    # Bollinger Bands
    bb_upper, bb_middle, bb_lower = _bollinger_bands(out, params.InpBBPeriod, params.InpBBDeviation)
    out["bbUpper"] = bb_upper
    out["bbMiddle"] = bb_middle
    out["bbLower"] = bb_lower

    # ATR + Keltner
    atr = _atr(out, params.InpADXPeriod)
    out["atr"] = atr
    out["keltnerUpper"] = bb_middle + (params.InpKeltnerMult * atr)
    out["keltnerLower"] = bb_middle - (params.InpKeltnerMult * atr)

    # Regras
    out["outOfSqueeze"] = (out["bbUpper"] > out["keltnerUpper"]) & (out["bbLower"] < out["keltnerLower"])
    out["trendIsStrong"] = out["adx"] >= float(params.InpADXMinLevel)

    out["macroAlta"] = (close > out["sma200"]) & (out["sma50"] > out["sma50_anterior"])
    out["macroBaixa"] = (close < out["sma200"]) & (out["sma50"] < out["sma50_anterior"])

    # Sinal
    sinal = np.full(len(out), 2, dtype=int)
    cond_base = out["trendIsStrong"] & out["outOfSqueeze"]

    # ALTA: fastEMA > trendEMA && macroAlta
    cond_alta = cond_base & (out["fastEMA"] > out["trendEMA"]) & out["macroAlta"]
    # BAIXA: fastEMA < trendEMA && macroBaixa
    cond_baixa = cond_base & (out["fastEMA"] < out["trendEMA"]) & out["macroBaixa"]

    sinal[cond_alta.fillna(False).values] = 0  # ALTA
    sinal[cond_baixa.fillna(False).values] = 1  # BAIXA
    out["sinal"] = sinal
    out["sinal_label"] = out["sinal"].map({0: "ALTA", 1: "BAIXA", 2: "LATERAL"})

    return out


def filtrar_ativos_macro_jr(
    df_por_ticker: Dict[str, pd.DataFrame],
    params: Optional[MacroJRParams] = None,
) -> List[Dict[str, Any]]:
    """
    Filtra ativos com sinal ALTA(0) ou BAIXA(1) no último candle
    """
    if params is None:
        params = MacroJRParams()

    resultados: List[Dict[str, Any]] = []
    for ticker, df in df_por_ticker.items():
        try:
            if df is None or len(df) < max(params.InpSMAMacro, params.InpBBPeriod, params.InpADXPeriod) + 5:
                continue
            calc = calcular_macro_jr(df, params)
            if calc.empty:
                continue
            last = calc.iloc[-1]
            sinal = int(last.get("sinal", 2))
            if sinal == 2:
                continue
            resultados.append(
                {
                    "ticker": ticker,
                    "sinal": sinal,  # 0=ALTA, 1=BAIXA
                    "sinal_label": "ALTA" if sinal == 0 else "BAIXA",
                    "preco": round(float(last["close"]), 2) if pd.notna(last["close"]) else None,
                    "adx": round(float(last["adx"]), 2) if pd.notna(last["adx"]) else None,
                    "fastEMA": round(float(last["fastEMA"]), 2) if pd.notna(last["fastEMA"]) else None,
                    "trendEMA": round(float(last["trendEMA"]), 2) if pd.notna(last["trendEMA"]) else None,
                    "sma50": round(float(last["sma50"]), 2) if pd.notna(last["sma50"]) else None,
                    "sma200": round(float(last["sma200"]), 2) if pd.notna(last["sma200"]) else None,
                    "outOfSqueeze": bool(last.get("outOfSqueeze", False)),
                    "trendIsStrong": bool(last.get("trendIsStrong", False)),
                }
            )
        except Exception:
            continue

    # Ordena: primeiro ALTA, depois BAIXA
    resultados.sort(key=lambda x: (x["sinal"], x["ticker"]))
    return resultados


def calcular_macro_jr_detalhado(df: pd.DataFrame, params: Optional[MacroJRParams] = None) -> Dict[str, Any]:
    if params is None:
        params = MacroJRParams()
    if len(df) < max(params.InpSMAMacro, params.InpBBPeriod, params.InpADXPeriod) + 5:
        return {"sucesso": False}
    calc = calcular_macro_jr(df, params)
    if calc.empty:
        return {"sucesso": False}
    last = calc.iloc[-1]
    preco = float(last["close"]) if pd.notna(last["close"]) else 0.0
    atr = float(last.get("atr", preco * 0.02)) if pd.notna(last.get("atr")) else preco * 0.02
    adx = float(last.get("adx", 0)) if pd.notna(last.get("adx")) else 0
    sinal = int(last.get("sinal", 2))
    bias = "BULLISH" if sinal == 0 else ("BEARISH" if sinal == 1 else "NEUTRO")
    
    # Targets
    if sinal == 0:  # ALTA
        entry = preco
        sl = entry - 1.5 * atr
        tp1 = entry + 1.0 * atr
        tp2 = entry + 2.0 * atr
        tp3 = entry + 3.0 * atr
    elif sinal == 1:  # BAIXA
        entry = preco
        sl = entry + 1.5 * atr
        tp1 = entry - 1.0 * atr
        tp2 = entry - 2.0 * atr
        tp3 = entry - 3.0 * atr
    else:
        entry = preco
        sl = entry - 1.0 * atr
        tp1 = entry + 1.0 * atr
        tp2 = entry + 1.5 * atr
        tp3 = entry + 2.0 * atr
    
    return {
        "sucesso": True,
        "sinal": sinal,
        "sinal_label": "ALTA" if sinal == 0 else ("BAIXA" if sinal == 1 else "LATERAL"),
        "bias": bias,
        "preco": round(preco, 2),
        "entry": round(entry, 2),
        "stop_loss": round(sl, 2),
        "take_profit_1": round(tp1, 2),
        "take_profit_2": round(tp2, 2),
        "take_profit_3": round(tp3, 2),
        "adx": round(adx, 2),
        "atr": round(atr, 2),
        "indicadores": {
            "fastEMA": round(float(last["fastEMA"]), 2) if pd.notna(last.get("fastEMA")) else None,
            "trendEMA": round(float(last["trendEMA"]), 2) if pd.notna(last.get("trendEMA")) else None,
            "sma50": round(float(last["sma50"]), 2) if pd.notna(last.get("sma50")) else None,
            "sma200": round(float(last["sma200"]), 2) if pd.notna(last.get("sma200")) else None,
            "bbUpper": round(float(last["bbUpper"]), 2) if pd.notna(last.get("bbUpper")) else None,
            "bbMiddle": round(float(last["bbMiddle"]), 2) if pd.notna(last.get("bbMiddle")) else None,
            "bbLower": round(float(last["bbLower"]), 2) if pd.notna(last.get("bbLower")) else None,
            "keltnerUpper": round(float(last["keltnerUpper"]), 2) if pd.notna(last.get("keltnerUpper")) else None,
            "keltnerLower": round(float(last["keltnerLower"]), 2) if pd.notna(last.get("keltnerLower")) else None,
        },
        "condicoes": {
            "outOfSqueeze": bool(last.get("outOfSqueeze", False)),
            "trendIsStrong": bool(last.get("trendIsStrong", False)),
            "macroAlta": bool(last.get("macroAlta", False)),
            "macroBaixa": bool(last.get("macroBaixa", False)),
        }
    }


def params_from_dict(data: Dict[str, Any]) -> MacroJRParams:
    if not isinstance(data, dict):
        return MacroJRParams()
    p = MacroJRParams()
    for k, v in data.items():
        if hasattr(p, k):
            try:
                if k == "InpADXMinLevel" or k == "InpBBDeviation" or k == "InpKeltnerMult":
                    setattr(p, k, float(v))
                else:
                    setattr(p, k, int(v))
            except Exception:
                pass
    # Forçar regra solicitada
    if p.InpADXMinLevel < 25.0:
        p.InpADXMinLevel = 25.0
    return p


def params_to_dict(p):
    return {
        "InpTrendPeriod": p.InpTrendPeriod,
        "InpFastEMAPeriod": p.InpFastEMAPeriod,
        "InpSMAInstitution": p.InpSMAInstitution,
        "InpSMAMacro": p.InpSMAMacro,
        "InpADXPeriod": p.InpADXPeriod,
        "InpADXMinLevel": p.InpADXMinLevel,
        "InpBBPeriod": p.InpBBPeriod,
        "InpBBDeviation": p.InpBBDeviation,
        "InpKeltnerMult": p.InpKeltnerMult,
    }

