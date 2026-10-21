"""Tests for configuration loader and SQLite WAL database layer."""

from pathlib import Path
import sqlite3
import pytest

from aguia.config import load_config, load_universe, load_holidays
from aguia.db import (
    init_db,
    get_connection,
    upsert_candles,
    upsert_setup,
    upsert_forecasts,
    upsert_explanation,
    set_meta,
    get_meta,
)


def test_load_config():
    cfg = load_config(reload=True)
    assert "server" in cfg
    assert cfg["server"]["host"] == "127.0.0.1"
    assert cfg["server"]["port"] == 8000
    assert "PETR4" == cfg["market"]["default_ticker"]
    assert cfg["indicators"]["sma_period"] == 200
    assert cfg["indicators"]["wma_period"] == 30
    assert cfg["indicators"]["atr_period"] == 14


def test_load_universe():
    universe = load_universe(reload=True)
    assert len(universe) == 18
    assert "PETR4" in universe
    assert "VALE3" in universe
    assert "ASAI3" in universe


def test_load_holidays():
    holidays = load_holidays(reload=True)
    assert isinstance(holidays, list)
    assert len(holidays) > 0
    assert "2026-01-01" in holidays


def test_db_init_and_wal(tmp_path: Path):
    db_file = tmp_path / "test.db"
    init_db(db_file)

    conn = get_connection(db_file)
    try:
        # Check WAL mode
        cur = conn.execute("PRAGMA journal_mode;")
        journal_mode = cur.fetchone()[0]
        assert journal_mode.lower() == "wal"

        # Check tables exist
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row[0] for row in cur.fetchall()}
        assert {"candles", "forecasts", "setups", "explanations", "meta"}.issubset(tables)
    finally:
        conn.close()


def test_db_upsert_candles_idempotent(tmp_path: Path):
    db_file = tmp_path / "test.db"
    init_db(db_file)

    candles_v1 = [
        {
            "ticker": "PETR4",
            "timeframe": "1d",
            "ts": "2026-10-20T10:00:00",
            "open": 38.0,
            "high": 39.0,
            "low": 37.5,
            "close": 38.5,
            "volume": 1000.0,
            "source": "yfinance",
            "adjusted": 1,
        }
    ]

    conn = get_connection(db_file)
    try:
        upsert_candles(conn, candles_v1)
        conn.commit()

        # Update close price
        candles_v2 = [
            {
                "ticker": "PETR4",
                "timeframe": "1d",
                "ts": "2026-10-20T10:00:00",
                "open": 38.0,
                "high": 39.0,
                "low": 37.5,
                "close": 38.9,  # updated
                "volume": 1200.0,
                "source": "yfinance",
                "adjusted": 1,
            }
        ]
        upsert_candles(conn, candles_v2)
        conn.commit()

        cur = conn.execute(
            "SELECT close, volume FROM candles WHERE ticker='PETR4' AND ts='2026-10-20T10:00:00'"
        )
        row = cur.fetchone()
        assert row["close"] == 38.9
        assert row["volume"] == 1200.0

        # Count must remain 1
        cur = conn.execute("SELECT COUNT(*) FROM candles")
        assert cur.fetchone()[0] == 1
    finally:
        conn.close()


def test_db_meta_helpers(tmp_path: Path):
    db_file = tmp_path / "test.db"
    init_db(db_file)

    conn = get_connection(db_file)
    try:
        set_meta(conn, "last_refresh_1d", "2026-10-21T18:00:00Z")
        conn.commit()

        val = get_meta(conn, "last_refresh_1d")
        assert val == "2026-10-21T18:00:00Z"

        # Update
        set_meta(conn, "last_refresh_1d", "2026-10-21T19:00:00Z")
        conn.commit()
        assert get_meta(conn, "last_refresh_1d") == "2026-10-21T19:00:00Z"
    finally:
        conn.close()
