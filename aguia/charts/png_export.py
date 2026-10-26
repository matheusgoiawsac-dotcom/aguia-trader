"""Headless PNG chart export using mplfinance and Agg backend with global thread lock."""

import io
import threading
import time
from typing import Any, Dict, Optional, Tuple

import pandas as pd

from aguia.brand import brand_group
from aguia.config import get_yfinance_period

# Rendered charts are memoised: a PNG is deterministic for a given ticker and
# timeframe, so re-rendering it on every request is pure waste.
CACHE_TTL_SECONDS = 300
_chart_cache: Dict[Tuple[str, str], Tuple[float, bytes]] = {}
_chart_lock = threading.Lock()

# Matplotlib is only imported on the first chart request, keeping the API
# server start-up free of a heavy scientific stack.
_mpl: Dict[str, Any] = {}


def _load_matplotlib() -> None:
    if _mpl:
        return
    import matplotlib

    matplotlib.use("Agg")  # Must be set before importing pyplot
    import matplotlib.pyplot as plt
    import mplfinance as mpf

    # Paleta da marca: a mesma do dashboard (config/brand_palette.json).
    chart = brand_group("chart")
    up = chart["up"]
    down = chart["down"]

    mc = mpf.make_marketcolors(
        up=up,
        down=down,
        edge={"up": up, "down": down},
        wick={"up": up, "down": down},
        ohlc={"up": up, "down": down},
        volume={"up": up, "down": down}
    )
    style = mpf.make_mpf_style(
        base_mpf_style="nightclouds",
        marketcolors=mc,
        facecolor=chart["facecolor"],
        edgecolor=chart["edgecolor"],
        figcolor=chart["figcolor"],
        gridcolor=chart["grid"],
        gridstyle="--",
        y_on_right=False
    )
    # Eixos e rótulos na mesma neutralidade da interface
    style["xtick.color"] = chart["axisText"]
    style["ytick.color"] = chart["axisText"]
    style["axes.labelcolor"] = chart["axisText"]
    style["axes.edgecolor"] = chart["edgecolor"]
    # Borda das barras de volume também na cor da marca (tolerante a
    # versões do mplfinance que não expõem a chave "vcedge").
    try:
        style["marketcolors"]["vcedge"]["up"] = chart["sma200"]
        style["marketcolors"]["vcedge"]["down"] = chart["sma200"]
    except (KeyError, TypeError):
        pass
    _mpl["plt"] = plt
    _mpl["mpf"] = mpf
    _mpl["style"] = style
    _mpl["chart"] = chart


def export_chart_png(
    ticker: str,
    timeframe: str = "1d",
    periodo: Optional[str] = None
) -> bytes:
    """Generate dark-themed candlestick chart PNG image as bytes."""
    from aguia.providers.yfinance_provider import obter_dados_mercado

    key = (ticker.upper(), timeframe.lower())
    now = time.time()

    with _chart_lock:
        cached = _chart_cache.get(key)
        if cached is not None and (now - cached[0]) < CACHE_TTL_SECONDS:
            return cached[1]

        _load_matplotlib()
        plt = _mpl["plt"]
        mpf = _mpl["mpf"]
        style = _mpl["style"]
        chart = _mpl["chart"]

        if periodo is None:
            periodo = get_yfinance_period(timeframe)

        df = obter_dados_mercado(ticker, periodo=periodo, intervalo=timeframe)
        if df.empty:
            raise ValueError(f"Dados não disponíveis para {ticker}")

        # Ensure standard OHLCV columns with DatetimeIndex
        chart_df = df.copy()
        if not isinstance(chart_df.index, pd.DatetimeIndex):
            chart_df.index = pd.to_datetime(chart_df.index)

        # Slice last 65 candles for clear rendering
        chart_df = chart_df.tail(65)

        # Additional plots (SMA200 and WMA30)
        addplots = []
        if "wma30" in chart_df.columns and chart_df["wma30"].notna().any():
            addplots.append(
                mpf.make_addplot(chart_df["wma30"], color=chart["wma30"], width=1.5, panel=0)
            )
        if "sma200" in chart_df.columns and chart_df["sma200"].notna().any():
            addplots.append(
                mpf.make_addplot(chart_df["sma200"], color=chart["sma200"], width=1.5, panel=0)
            )

        buf = io.BytesIO()
        fig, axes = mpf.plot(
            chart_df,
            type="candle",
            style=style,
            addplot=addplots if addplots else None,
            volume=True,
            returnfig=True,
            figsize=(10, 5.5),
            tight_layout=True
        )

        # Add title and watermark
        axes[0].set_title(
            f"Águia Trader — {ticker} ({timeframe.upper()})",
            color=chart["title"],
            fontsize=12,
            fontweight="bold",
            loc="left",
            pad=10
        )
        axes[0].text(
            0.98, 0.04,
            "ÁGUIA TRADER",
            transform=axes[0].transAxes,
            fontsize=16,
            color=chart["watermark"],
            alpha=0.35,
            ha="right",
            va="bottom",
            fontweight="bold"
        )

        fig.savefig(buf, format="png", dpi=100, facecolor=fig.get_facecolor(), edgecolor="none")
        plt.close(fig)
        buf.seek(0)
        payload = buf.getvalue()

        _chart_cache[key] = (time.time(), payload)

    return payload
