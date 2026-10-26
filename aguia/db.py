"""SQLite database layer with WAL mode, thread-local pooling and idempotent upserts."""

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import threading
from typing import Any, Dict, Generator, Optional, Sequence

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
    """,
    # Composite indexes that the snapshot query relies on:
    #   setups(ticker, timeframe, asof)  -> already the PRIMARY KEY
    #   candles(ticker, timeframe, ts)   -> already the PRIMARY KEY
    #   setups(timeframe)                -> speeds up timeframe-scoped snapshots
    #   candles(timeframe)               -> speeds up timeframe-scoped snapshots
    #   explanations(ticker, timeframe, asof) -> already the PRIMARY KEY
    """
    CREATE INDEX IF NOT EXISTS idx_setups_timeframe
        ON setups(timeframe);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_candles_timeframe
        ON candles(timeframe);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_candles_ticker_ts
        ON candles(ticker, ts);
    """,
]

# The candles primary key (ticker, timeframe, ts) already materialises an implicit
# index on the exact same column order. The legacy explicit index duplicated it and
# doubled the write cost of every candle upsert, so it is dropped on init.
LEGACY_INDEX_CLEANUP = [
    "DROP INDEX IF EXISTS idx_candles_ticker_tf_ts;"
]

_INITIALIZED_PATHS: set[str] = set()
_RESOLVED_PATHS: Dict[str, str] = {}
_INIT_LOCK = threading.Lock()
_LOCAL = threading.local()


def ensure_data_dir() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR


def _resolve_path(db_path: Optional[Path] = None) -> str:
    """Resolve a database path to an absolute string (cached: it hits the disk)."""
    target = db_path or DEFAULT_DB_PATH
    key = str(target)
    resolved = _RESOLVED_PATHS.get(key)
    if resolved is None:
        resolved = str(Path(target).resolve())
        _RESOLVED_PATHS[key] = resolved
    return resolved


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Create a new SQLite connection configured with WAL mode."""
    ensure_data_dir()
    path = db_path or DEFAULT_DB_PATH
    conn = sqlite3.connect(str(path), timeout=30.0)
    conn.row_factory = sqlite3.Row

    # WAL is persisted in the database header: re-issuing the statement on an
    # already-WAL file costs a lock round-trip, so it is only set when needed.
    mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
    if str(mode).lower() != "wal":
        conn.execute("PRAGMA journal_mode=WAL;")

    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("PRAGMA cache_size=-4000;")
    conn.execute("PRAGMA temp_store=MEMORY;")
    return conn


@contextmanager
def get_db(db_path: Optional[Path] = None) -> Generator[sqlite3.Connection, None, None]:
    """Context manager for a short-lived connection that is always closed."""
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_pooled_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """
    Return a long-lived connection owned by the calling thread.

    SQLite handles are not safe to share between threads, so the pool is
    thread-local: every worker thread keeps a single handle instead of opening
    (and re-pragma-ing) a new one on each request.
    """
    key = _resolve_path(db_path)
    pool: Dict[str, sqlite3.Connection] = getattr(_LOCAL, "pool", None) or {}
    if not hasattr(_LOCAL, "pool"):
        _LOCAL.pool = pool

    conn = pool.get(key)
    if conn is None:
        conn = get_connection(db_path)
        pool[key] = conn
    return conn


@contextmanager
def pooled_db(db_path: Optional[Path] = None) -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager around the thread-local connection.

    Commits on success, rolls back on error, and leaves the handle open for
    reuse by the next request served by the same thread.
    """
    conn = get_pooled_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def init_db(db_path: Optional[Path] = None) -> None:
    """Initialize database tables and indexes. Runs the DDL only once per path."""
    key = _resolve_path(db_path)
    with _INIT_LOCK:
        if key in _INITIALIZED_PATHS:
            return

        with get_db(db_path) as conn:
            for stmt in SCHEMA_STATEMENTS:
                conn.execute(stmt)
            for stmt in LEGACY_INDEX_CLEANUP:
                conn.execute(stmt)

        _INITIALIZED_PATHS.add(key)


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


def prune_history(
    conn: sqlite3.Connection,
    ticker: str,
    timeframe: str = "1d",
    keep: int = 20
) -> None:
    """
    Keep only the most recent history rows of a ticker.

    Every analysis writes a new snapshot; without a retention policy the
    history tables grow without bound. Uses ROW_NUMBER() so the "keep
    newest" semantics are guaranteed even when asof values collide.
    """
    for table in ("setups", "explanations"):
        conn.execute(
            """
            DELETE FROM {table}
            WHERE ticker = ? AND timeframe = ?
              AND rowid NOT IN (
                  SELECT rowid FROM (
                      SELECT rowid,
                             ROW_NUMBER() OVER (ORDER BY asof DESC, rowid DESC) AS rn
                      FROM {table}
                      WHERE ticker = ? AND timeframe = ?
                  )
                  WHERE rn <= ?
              )
            """.format(table=table),
            (ticker, timeframe, ticker, timeframe, keep),
        )


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


def count_candles(conn: sqlite3.Connection, ticker: str, timeframe: str) -> int:
    """Count stored candles for a ticker/timeframe pair."""
    cur = conn.execute(
        "SELECT COUNT(*) FROM candles WHERE ticker = ? AND timeframe = ?",
        (ticker, timeframe),
    )
    return int(cur.fetchone()[0])


def trim_candles(
    conn: sqlite3.Connection,
    ticker: str,
    timeframe: str,
    keep: int = 500,
) -> int:
    """
    Keep only the most recent ``keep`` candles for a ticker/timeframe pair.

    Without a retention policy the candles table grows without bound. The
    function deletes rows whose ``ts`` is not among the newest ``keep`` rows
    (ordered by the primary key). Returns the number of deleted rows.
    """
    if keep <= 0:
        return 0
    cur = conn.execute(
        """
        DELETE FROM candles
        WHERE ticker = ? AND timeframe = ?
          AND rowid NOT IN (
              SELECT rowid FROM (
                  SELECT rowid,
                         ROW_NUMBER() OVER (ORDER BY ts DESC, rowid DESC) AS rn
                  FROM candles
                  WHERE ticker = ? AND timeframe = ?
              )
              WHERE rn <= ?
          )
        """,
        (ticker, timeframe, ticker, timeframe, keep),
    )
    return cur.rowcount or 0


def vacuum_if_needed(conn: sqlite3.Connection, min_pages: int = 1000) -> bool:
    """
    Run ``VACUUM`` only when the database has grown past ``min_pages``.

    VACUUM is expensive (it rewrites the whole file), so it is gated behind a
    page-count check to avoid running it on every startup.
    """
    cur = conn.execute("PRAGMA page_count;")
    pages = int(cur.fetchone()[0])
    if pages < min_pages:
        return False
    conn.execute("VACUUM;")
    return True
