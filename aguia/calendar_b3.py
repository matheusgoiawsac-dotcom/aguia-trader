"""B3 (Brazil) trading calendar, holidays, and schedule projection."""

from datetime import date, datetime, timedelta, time
from typing import List, Optional, Set
from zoneinfo import ZoneInfo

from aguia.config import load_holidays

B3_TIMEZONE = ZoneInfo("America/Sao_Paulo")

# Regular B3 trading hours in Sao Paulo local time
MARKET_OPEN_TIME = time(10, 0)
MARKET_CLOSE_TIME = time(17, 0)

_HOLIDAYS_SET: Optional[Set[str]] = None


def get_b3_holidays() -> Set[str]:
    """Return the set of B3 holiday dates (YYYY-MM-DD)."""
    global _HOLIDAYS_SET
    if _HOLIDAYS_SET is None:
        _HOLIDAYS_SET = set(load_holidays())
    return _HOLIDAYS_SET


def is_b3_trading_day(d: date) -> bool:
    """Check if a date is a regular B3 trading day (Mon-Fri and not a holiday)."""
    if d.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return False
    d_str = d.strftime("%Y-%m-%d")
    return d_str not in get_b3_holidays()


def next_b3_trading_day(d: date) -> date:
    """Return the next valid B3 trading day after date d."""
    cur = d + timedelta(days=1)
    while not is_b3_trading_day(cur):
        cur += timedelta(days=1)
    return cur


def previous_b3_trading_day(d: date) -> date:
    """Return the previous valid B3 trading day before date d."""
    cur = d - timedelta(days=1)
    while not is_b3_trading_day(cur):
        cur -= timedelta(days=1)
    return cur


def project_future_trading_days(start_date: date, count: int = 14) -> List[date]:
    """Project the next `count` B3 trading days starting strictly after `start_date`."""
    days = []
    cur = start_date
    while len(days) < count:
        cur = next_b3_trading_day(cur)
        days.append(cur)
    return days


def is_b3_market_open(dt: Optional[datetime] = None) -> bool:
    """Check whether the B3 equity market is currently open."""
    if dt is None:
        dt = datetime.now(B3_TIMEZONE)
    elif dt.tzinfo is None:
        dt = dt.replace(tzinfo=B3_TIMEZONE)
    else:
        dt = dt.astimezone(B3_TIMEZONE)

    if not is_b3_trading_day(dt.date()):
        return False

    current_time = dt.time()
    return MARKET_OPEN_TIME <= current_time <= MARKET_CLOSE_TIME
