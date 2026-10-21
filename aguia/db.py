"""SQLite database layer with WAL mode and idempotent upserts."""

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Any, Dict, Generator, List, Optional, Sequence

from aguia.config import ROOT_DIR

DATA_DIR = ROOT_DIR / "data"
DEFAULT_DB_PATH = DATA_DIR / "aguia.db"

SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS candles (
        ticker TEXT NOT NULL,
        timeframe TEXT NOT NULL,
        ts TEXT NOT NULL,
        open REAL NOT NULL,
        high REAL NOT NULL,
        low REAL NOT NULL,
        close REAL NOT NULL,
        volume REAL NOT NULL,
        source TEXT NOT NULL,
        adjusted INTEGER NOT NULL DEFAULT 1,
        PRIMARY KEY (ticker, timeframe, ts)
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_candles_ticker_tf_ts 
    ON candles(ticker, timeframe, ts);
    """,
    """
    CREATE TABLE IF NOT EXISTS forecasts (
        ticker TEXT NOT NULL,
        timeframe TEXT NOT NULL,
        asof TEXT NOT NULL,
        step INTEGER NOT NULL,
        horizon INTEGER NOT NULL,
        ts_target TEXT NOT NULL,
        p10 REAL NOT NULL,
        median REAL NOT NULL,
        p90 REAL NOT NULL,
        p_up REAL NOT NULL,
        n_samples INTEGER NOT NULL,
        model TEXT NOT NULL,
        PRIMARY KEY (ticker, timeframe, asof, step)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS setups (
        ticker TEXT NOT NULL,
        timeframe TEXT NOT NULL,
        asof TEXT NOT NULL,
        signal TEXT NOT NULL,
        entry REAL NOT NULL,
        target REAL,
        stop REAL,
        payoff REAL,
        ret REAL,
        atr_pct REAL,
        p_up REAL,
        PRIMARY KEY (ticker, timeframe, asof)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS explanations (
        ticker TEXT NOT NULL,
        timeframe TEXT NOT NULL,
        asof TEXT NOT NULL,
        rationale TEXT NOT NULL,
        source TEXT NOT NULL,
        model TEXT NOT NULL,
        facts_hash TEXT NOT NULL,
        PRIMARY KEY (ticker, timeframe, asof)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS meta (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """
]


def ensure_data_dir() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Create a new SQLite connection configured with WAL mode."""
    ensure_data_dir()
    path = db_path or DEFAULT_DB_PATH
    conn = sqlite3.connect(str(path), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


@contextmanager
def get_db(db_path: Optional[Path] = None) -> Generator[sqlite3.Connection, None, None]:
    """Context manager for thread-safe database connection."""
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: Optional[Path] = None) -> None:
    """Initialize database tables and indexes."""
    with get_db(db_path) as conn:
        for stmt in SCHEMA_STATEMENTS:
            conn.execute(stmt)


def upsert_candles(conn: sqlite3.Connection, rows: Sequence[Dict[str, Any]]) -> int:
    """Idempotently insert or replace candle records."""
    if not rows:
        return 0

    sql = """
    INSERT INTO candles (ticker, timeframe, ts, open, high, low, close, volume, source, adjusted)
    VALUES (:ticker, :timeframe, :ts, :open, :high, :low, :close, :volume, :source, :adjusted)
    ON CONFLICT(ticker, timeframe, ts) DO UPDATE SET
        open = excluded.open,
        high = excluded.high,
        low = excluded.low,
        close = excluded.close,
        volume = excluded.volume,
        source = excluded.source,
        adjusted = excluded.adjusted;
    """
    conn.executemany(sql, rows)
    return len(rows)


def upsert_forecasts(conn: sqlite3.Connection, rows: Sequence[Dict[str, Any]]) -> int:
    """Idempotently insert or update forecast steps."""
    if not rows:
        return 0

    sql = """
    INSERT INTO forecasts (ticker, timeframe, asof, step, horizon, ts_target, p10, median, p90, p_up, n_samples, model)
    VALUES (:ticker, :timeframe, :asof, :step, :horizon, :ts_target, :p10, :median, :p90, :p_up, :n_samples, :model)
    ON CONFLICT(ticker, timeframe, asof, step) DO UPDATE SET
        horizon = excluded.horizon,
        ts_target = excluded.ts_target,
        p10 = excluded.p10,
        median = excluded.median,
        p90 = excluded.p90,
        p_up = excluded.p_up,
        n_samples = excluded.n_samples,
        model = excluded.model;
    """
    conn.executemany(sql, rows)
    return len(rows)


def upsert_setup(conn: sqlite3.Connection, row: Dict[str, Any]) -> None:
    """Idempotently insert or update setup."""
    sql = """
    INSERT INTO setups (ticker, timeframe, asof, signal, entry, target, stop, payoff, ret, atr_pct, p_up)
    VALUES (:ticker, :timeframe, :asof, :signal, :entry, :target, :stop, :payoff, :ret, :atr_pct, :p_up)
    ON CONFLICT(ticker, timeframe, asof) DO UPDATE SET
        signal = excluded.signal,
        entry = excluded.entry,
        target = excluded.target,
        stop = excluded.stop,
        payoff = excluded.payoff,
        ret = excluded.ret,
        atr_pct = excluded.atr_pct,
        p_up = excluded.p_up;
    """
    conn.execute(sql, row)


def upsert_explanation(conn: sqlite3.Connection, row: Dict[str, Any]) -> None:
    """Idempotently insert or update rationale explanation."""
    sql = """
    INSERT INTO explanations (ticker, timeframe, asof, rationale, source, model, facts_hash)
    VALUES (:ticker, :timeframe, :asof, :rationale, :source, :model, :facts_hash)
    ON CONFLICT(ticker, timeframe, asof) DO UPDATE SET
        rationale = excluded.rationale,
        source = excluded.source,
        model = excluded.model,
        facts_hash = excluded.facts_hash;
    """
    conn.execute(sql, row)


def set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    """Set or update metadata key/value."""
    now = datetime.now(timezone.utc).isoformat()
    sql = """
    INSERT INTO meta (key, value, updated_at)
    VALUES (?, ?, ?)
    ON CONFLICT(key) DO UPDATE SET
        value = excluded.value,
        updated_at = excluded.updated_at;
    """
    conn.execute(sql, (key, value, now))


def get_meta(conn: sqlite3.Connection, key: str) -> Optional[str]:
    """Retrieve metadata value."""
    cur = conn.execute("SELECT value FROM meta WHERE key = ?", (key,))
    row = cur.fetchone()
    return row["value"] if row else None
