"""Headless PNG chart export using mplfinance and Agg backend with global thread lock."""

import io
import threading
from typing import Optional

import matplotlib
matplotlib.use("Agg")  # Must be set before importing pyplot
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd

from aguia.providers.yfinance_provider import obter_dados_mercado

_CHART_LOCK = threading.Lock()


def export_chart_png(
    ticker: str,
    timeframe: str = "1d",
    periodo: str = "6m"
) -> bytes:
    """Generate dark-themed candlestick chart PNG image as bytes."""
    with _CHART_LOCK:
        df = obter_dados_mercado(ticker, periodo=periodo, intervalo=timeframe)
        if df.empty:
            raise ValueError(f"Dados não disponíveis para {ticker}")

        # Ensure standard OHLCV columns with DatetimeIndex
        chart_df = df.copy()
        if not isinstance(chart_df.index, pd.DatetimeIndex):
            chart_df.index = pd.to_datetime(chart_df.index)

        # Slice last 65 candles for clear rendering
        chart_df = chart_df.tail(65)

        # Define dark custom style
        mc = mpf.make_marketcolors(
            up="#22c55e",
            down="#ef4444",
            edge={"up": "#22c55e", "down": "#ef4444"},
            wick={"up": "#22c55e", "down": "#ef4444"},
            volume={"up": "#22c55e", "down": "#ef4444"}
        )
        s = mpf.make_mpf_style(
            base_mpf_style="nightclouds",
            marketcolors=mc,
            facecolor="#060911",
            edgecolor="#1e293b",
            figcolor="#0a0e17",
            gridcolor="#161f30",
            gridstyle="--",
            y_on_right=False
        )

        # Additional plots (SMA200 and WMA30)
        addplots = []
        if "wma30" in chart_df.columns and chart_df["wma30"].notna().any():
            addplots.append(
                mpf.make_addplot(chart_df["wma30"], color="#facc15", width=1.5, panel=0)
            )
        if "sma200" in chart_df.columns and chart_df["sma200"].notna().any():
            addplots.append(
                mpf.make_addplot(chart_df["sma200"], color="#3b82f6", width=1.5, panel=0)
            )

        buf = io.BytesIO()
        fig, axes = mpf.plot(
            chart_df,
            type="candle",
            style=s,
            addplot=addplots if addplots else None,
            volume=True,
            returnfig=True,
            figsize=(10, 5.5),
            tight_layout=True
        )

        # Add title and watermark
        axes[0].set_title(
            f"Águia Trader — {ticker} ({timeframe.upper()})",
            color="#f1f5f9",
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
            color="#334155",
            alpha=0.35,
            ha="right",
            va="bottom",
            fontweight="bold"
        )

        fig.savefig(buf, format="png", dpi=100, facecolor=fig.get_facecolor(), edgecolor="none")
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()
