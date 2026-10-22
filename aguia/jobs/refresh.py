"""CLI market data refresh job for Águia Trader."""

import argparse
from datetime import datetime, timezone
import sys
import time
from typing import List, Optional

import pandas as pd

from aguia.config import load_universe
from aguia.db import get_connection, init_db, set_meta, upsert_candles, upsert_setup
from aguia.providers.yfinance_provider import obter_dados_mercado
from integracao_ollama import gerar_racional_ia


def refresh_tickers(
    tickers: List[str],
    timeframe: str = "1d",
    periodo: str = "2y",
    verbose: bool = True
) -> dict:
    """Refresh candles and setups for the specified tickers."""
    init_db()
    results = {"success": [], "failed": []}
    now_iso = datetime.now(timezone.utc).isoformat()

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
            sma200 = round(float(last_row["sma200"]), 2) if pd.notna(last_row["sma200"]) else None
            wma30 = round(float(last_row["wma30"]), 2) if pd.notna(last_row["wma30"]) else None
            atr14 = round(float(last_row["atr14"]), 2) if pd.notna(last_row["atr14"]) else round(preco * 0.025, 2)

            is_alta = (wma30 is not None and preco > wma30) and (sma200 is None or preco > sma200)
            is_baixa = (wma30 is not None and preco < wma30) and (sma200 is None or preco < sma200)

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
            projecao_pct = round(((alvo - preco) / preco) * 100, 2)

            candles_data = []
            for idx, row in df.iterrows():
                dt_str = idx.strftime("%Y-%m-%d") if isinstance(idx, (pd.Timestamp, datetime)) else str(idx)[:10]
                candles_data.append({
                    "ticker": ticker,
                    "timeframe": timeframe,
                    "ts": dt_str,
                    "open": round(float(row["open"]), 2),
                    "high": round(float(row["high"]), 2),
                    "low": round(float(row["low"]), 2),
                    "close": round(float(row["close"]), 2),
                    "volume": round(float(row["volume"]), 2),
                    "source": "yfinance",
                    "adjusted": 1
                })

            with get_connection() as conn:
                upsert_candles(conn, candles_data)
                upsert_setup(conn, {
                    "ticker": ticker,
                    "timeframe": timeframe,
                    "asof": now_iso,
                    "signal": tendencia,
                    "entry": preco,
                    "target": alvo,
                    "stop": stop,
                    "payoff": payoff_num,
                    "ret": projecao_pct / 100.0,
                    "atr_pct": atr14 / preco if preco else 0.0,
                    "p_up": 0.65 if tendencia == "ALTA" else (0.35 if tendencia == "BAIXA" else 0.50)
                })
                set_meta(conn, f"last_refresh_{ticker}_{timeframe}", now_iso)
                conn.commit()

            results["success"].append(ticker)
            if verbose:
                print(f"OK (R$ {preco:.2f} | {tendencia} | {len(candles_data)} candles)")

        except Exception as e:
            if verbose:
                print(f"ERRO: {e}")
            results["failed"].append(ticker)

        time.sleep(0.3)  # Respect rate limit <= 2 req/s

    with get_connection() as conn:
        set_meta(conn, f"last_refresh_{timeframe}", now_iso)
        conn.commit()

    if verbose:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Refresh concluído: {len(results['success'])} sucesso(s), {len(results['failed'])} falha(s).")

    return results


def main() -> None:
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
