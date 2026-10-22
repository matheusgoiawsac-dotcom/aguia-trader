"""Tests for B3 trading calendar and refresh job."""

from datetime import date, datetime
import pytest

from aguia.calendar_b3 import (
    is_b3_trading_day,
    next_b3_trading_day,
    previous_b3_trading_day,
    project_future_trading_days,
    is_b3_market_open
)
from aguia.jobs.refresh import refresh_tickers
from aguia.db import get_connection, get_meta


def test_is_b3_trading_day_weekends():
    # 2026-10-24 is Saturday, 2026-10-25 is Sunday
    assert not is_b3_trading_day(date(2026, 10, 24))
    assert not is_b3_trading_day(date(2026, 10, 25))


def test_is_b3_trading_day_holidays():
    # 2026-01-01 is Confraternização Universal (holiday)
    assert not is_b3_trading_day(date(2026, 1, 1))
    # 2026-04-21 is Tiradentes (holiday)
    assert not is_b3_trading_day(date(2026, 4, 21))
    # 2026-05-01 is Dia do Trabalho (holiday)
    assert not is_b3_trading_day(date(2026, 5, 1))


def test_is_b3_trading_day_regular_day():
    # 2026-10-21 is Wednesday (trading day)
    assert is_b3_trading_day(date(2026, 10, 21))


def test_next_and_previous_b3_trading_day():
    # Friday 2026-10-23 -> next is Monday 2026-10-26
    next_day = next_b3_trading_day(date(2026, 10, 23))
    assert next_day == date(2026, 10, 26)

    # Monday 2026-10-26 -> previous is Friday 2026-10-23
    prev_day = previous_b3_trading_day(date(2026, 10, 26))
    assert prev_day == date(2026, 10, 23)


def test_project_future_trading_days():
    days = project_future_trading_days(date(2026, 10, 23), count=14)
    assert len(days) == 14
    for d in days:
        assert is_b3_trading_day(d)
        assert d > date(2026, 10, 23)


def test_refresh_tickers_job():
    res = refresh_tickers(["PETR4"], timeframe="1d", verbose=False)
    assert "PETR4" in res["success"]
    with get_connection() as conn:
        meta_1d = get_meta(conn, "last_refresh_1d")
        assert meta_1d is not None
        c_count = conn.execute("SELECT COUNT(1) FROM candles WHERE ticker = 'PETR4'").fetchone()[0]
        assert c_count >= 100
