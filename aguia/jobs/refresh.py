"""CLI market data refresh job for Águia Trader."""

import argparse
from datetime import datetime, timezone
import sys
import time
from typing import Any, Dict, List, Optional

import pandas as pd

from aguia.config import get_yfinance_period, load_universe
from aguia.db import init_db, pooled_db, prune_history, set_meta, upsert_candles, upsert_setup
from aguia.forecast.signals import build_setup
from aguia.providers.yfinance_provider import obter_dados_mercado


def _candle_rows(ticker: str, timeframe: str, df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Serialise a DataFrame into candle rows without row-by-row pandas access."""
    dates = [
        ts.strftime("%Y-%m-%d") if hasattr(ts, "strftime") else str(ts)[:10]
        for ts in df.index
    ]
    columns = {
        name: df[name].to_numpy(dtype=float)
        for name in ("open", "high", "low", "close", "volume")
    }

    rows: List[Dict[str, Any]] = []
    for i, ts in enumerate(dates):
        rows.append({
            "ticker": ticker,
            "timeframe": timeframe,
            "ts": ts,
            "open": round(float(columns["open"][i]), 2),
            "high": round(float(columns["high"][i]), 2),
            "low": round(float(columns["low"][i]), 2),
            "close": round(float(columns["close"][i]), 2),
            "volume": round(float(columns["volume"][i]), 2),
            "source": "yfinance",
            "adjusted": 1
        })
    return rows


def refresh_tickers(
    tickers: List[str],
    timeframe: str = "1d",
    periodo: Optional[str] = None,
    verbose: bool = True
) -> dict:
    """Refresh candles and setups for the specified tickers."""
    init_db()
    results: Dict[str, List[str]] = {"success": [], "failed": []}
    now_iso = datetime.now(timezone.utc).isoformat()

    if periodo is None:
        periodo = get_yfinance_period(timeframe)

    if verbose:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Iniciando refresh ({timeframe}) para {len(tickers)} ativos...")

    for i, ticker in enumerate(tickers, 1):
        try:
            if verbose:
                print(f"  [{i:02d}/{len(tickers):02d}] {ticker}...", end=" ", flush=True)

            df = obter_dados_mercado(ticker, periodo=periodo, intervalo=timeframe)
            if df.empty or len(df) < 5:
                if verbose:
                    print("VAZIO!")
                results["failed"].append(ticker)
                continue

            last_row = df.iloc[-1]
            preco = round(float(last_row["close"]), 2)

            setup = build_setup(
                preco=preco,
                sma200=float(last_row["sma200"]) if pd.notna(last_row["sma200"]) else None,
                wma30=float(last_row["wma30"]) if pd.notna(last_row["wma30"]) else None,
                atr14=float(last_row["atr14"]) if pd.notna(last_row["atr14"]) else None,
            )
            tendencia = setup["tendencia"]

            candles_data = _candle_rows(ticker, timeframe, df)

            with pooled_db() as conn:
                upsert_candles(conn, candles_data)
                upsert_setup(conn, {
                    "ticker": ticker,
                    "timeframe": timeframe,
                    "asof": now_iso,
                    "signal": tendencia,
                    "entry": setup["preco"],
                    "target": setup["alvo"],
                    "stop": setup["stop"],
                    "payoff": setup["payoff_num"],
                    "ret": setup["projecao_pct"] / 100.0,
                    "atr_pct": setup["indicadores"]["atr14"] / setup["preco"] if setup["preco"] else 0.0,
                    "p_up": 0.65 if tendencia == "ALTA" else (0.35 if tendencia == "BAIXA" else 0.50)
                })
                set_meta(conn, f"last_refresh_{ticker}_{timeframe}", now_iso)
                prune_history(conn, ticker, timeframe)

            results["success"].append(ticker)
            if verbose:
                print(f"OK (R$ {preco:.2f} | {tendencia} | {len(candles_data)} candles)")

        except Exception as e:
            if verbose:
                print(f"ERRO: {e}")
            results["failed"].append(ticker)

        time.sleep(0.3)  # Respect rate limit <= 2 req/s

    with pooled_db() as conn:
        set_meta(conn, f"last_refresh_{timeframe}", now_iso)

    if verbose:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Refresh concluído: {len(results['success'])} sucesso(s), {len(results['failed'])} falha(s).")

    return results


def main() -> None:
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="Águia Trader - Atualizador de dados B3")
    parser.add_argument("--tf", default="1d", choices=["1d", "15m", "5m"], help="Timeframe (padrão: 1d)")
    parser.add_argument("--tickers", default=None, help="Lista de tickers separados por vírgula (ex: PETR4,VALE3)")
    args = parser.parse_args()

    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    else:
        try:
            tickers = load_universe()
        except Exception:
            tickers = ["PETR4", "VALE3", "ITUB4", "BBDC4", "ASAI3"]

    refresh_tickers(tickers, timeframe=args.tf)


if __name__ == "__main__":
    main()
