"""Tests for configuration loader and SQLite WAL database layer."""

from pathlib import Path

from aguia.config import load_config, load_universe, load_holidays
from aguia.db import (
    init_db,
    get_connection,
    get_pooled_connection,
    pooled_db,
    prune_history,
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


def test_db_upsert_setup_forecasts_and_explanations(tmp_path: Path):
    db_file = tmp_path / "test.db"
    init_db(db_file)

    conn = get_connection(db_file)
    try:
        upsert_setup(conn, {
            "ticker": "PETR4",
            "timeframe": "1d",
            "asof": "2026-10-21T18:00:00Z",
            "signal": "ALTA",
            "entry": 38.45,
            "target": 40.10,
            "stop": 37.18,
            "payoff": 1.30,
            "ret": 0.043,
            "atr_pct": 0.022,
            "p_up": 0.65,
        })
        upsert_forecasts(conn, [{
            "ticker": "PETR4",
            "timeframe": "1d",
            "asof": "2026-10-21T18:00:00Z",
            "step": 1,
            "horizon": 14,
            "ts_target": "2026-11-04",
            "p10": 36.10,
            "median": 38.90,
            "p90": 41.80,
            "p_up": 0.65,
            "n_samples": 10,
            "model": "FakePredictor",
        }])
        upsert_explanation(conn, {
            "ticker": "PETR4",
            "timeframe": "1d",
            "asof": "2026-10-21T18:00:00Z",
            "rationale": "Racional determinístico de teste.",
            "source": "deterministico",
            "model": "deterministico",
            "facts_hash": "abc123",
        })
        conn.commit()

        row = conn.execute("SELECT * FROM setups WHERE ticker = 'PETR4'").fetchone()
        assert row["signal"] == "ALTA"
        assert row["payoff"] == 1.30

        fc = conn.execute("SELECT * FROM forecasts WHERE ticker = 'PETR4'").fetchone()
        assert fc["median"] == 38.90
        assert fc["n_samples"] == 10

        ex = conn.execute("SELECT * FROM explanations WHERE ticker = 'PETR4'").fetchone()
        assert ex["source"] == "deterministico"
        assert ex["facts_hash"] == "abc123"

        # Re-running the upserts must not duplicate rows
        upsert_setup(conn, {
            "ticker": "PETR4",
            "timeframe": "1d",
            "asof": "2026-10-21T18:00:00Z",
            "signal": "NEUTRO",
            "entry": 38.45,
            "target": 40.10,
            "stop": 37.18,
            "payoff": 1.30,
            "ret": 0.043,
            "atr_pct": 0.022,
            "p_up": 0.50,
        })
        conn.commit()
        assert conn.execute("SELECT COUNT(1) FROM setups").fetchone()[0] == 1
    finally:
        conn.close()


def test_db_pooled_connection_is_reused_per_thread(tmp_path: Path):
    db_file = tmp_path / "test.db"
    init_db(db_file)

    with pooled_db(db_file) as conn:
        conn.execute("SELECT 1").fetchone()

    with pooled_db(db_file) as conn:
        conn.execute("SELECT 1").fetchone()

    assert get_pooled_connection(db_file) is get_pooled_connection(db_file)


def test_db_prune_history_keeps_latest_rows(tmp_path: Path):
    db_file = tmp_path / "test.db"
    init_db(db_file)

    conn = get_connection(db_file)
    try:
        for i in range(30):
            asof = f"2026-10-{i + 1:02d}T00:00:00Z"
            upsert_setup(conn, {
                "ticker": "PETR4", "timeframe": "1d", "asof": asof,
                "signal": "ALTA", "entry": 38.0, "target": 40.0, "stop": 37.0,
                "payoff": 1.2, "ret": 0.05, "atr_pct": 0.02, "p_up": 0.65,
            })
            upsert_explanation(conn, {
                "ticker": "PETR4", "timeframe": "1d", "asof": asof,
                "rationale": "r", "source": "deterministico",
                "model": "deterministico", "facts_hash": f"h{i}",
            })
        conn.commit()

        prune_history(conn, "PETR4", "1d", keep=20)

        assert conn.execute("SELECT COUNT(1) FROM setups").fetchone()[0] == 20
        assert conn.execute("SELECT COUNT(1) FROM explanations").fetchone()[0] == 20

        # The newest snapshot must survive the pruning
        latest = conn.execute(
            "SELECT asof FROM setups ORDER BY asof DESC LIMIT 1"
        ).fetchone()[0]
        assert latest == "2026-10-30T00:00:00Z"
    finally:
        conn.close()
