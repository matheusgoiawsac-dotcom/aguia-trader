"""Configuration loader using stdlib tomllib."""

from pathlib import Path
import json
import tomllib
from typing import Any, Dict, List, Optional

ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT_DIR / "config"

_CONFIG_CACHE: Optional[Dict[str, Any]] = None
_UNIVERSE_CACHE: Optional[List[str]] = None
_HOLIDAYS_CACHE: Optional[List[str]] = None


def get_config_path() -> Path:
    return CONFIG_DIR / "config.toml"


def get_universe_path() -> Path:
    return CONFIG_DIR / "universe.json"


def get_holidays_path() -> Path:
    return CONFIG_DIR / "b3_holidays.json"


def load_config(reload: bool = False) -> Dict[str, Any]:
    """Load config.toml using standard library tomllib."""
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None and not reload:
        return _CONFIG_CACHE

    path = get_config_path()
    if not path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    with open(path, "rb") as f:
        _CONFIG_CACHE = tomllib.load(f)

    return _CONFIG_CACHE


def load_universe(reload: bool = False) -> List[str]:
    """Load monitored tickers list from universe.json."""
    global _UNIVERSE_CACHE
    if _UNIVERSE_CACHE is not None and not reload:
        return _UNIVERSE_CACHE

    path = get_universe_path()
    if not path.is_file():
        raise FileNotFoundError(f"Universe file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        _UNIVERSE_CACHE = json.load(f)

    return _UNIVERSE_CACHE


def load_holidays(reload: bool = False) -> List[str]:
    """Load B3 holiday dates from b3_holidays.json."""
    global _HOLIDAYS_CACHE
    if _HOLIDAYS_CACHE is not None and not reload:
        return _HOLIDAYS_CACHE

    path = get_holidays_path()
    if not path.is_file():
        return []

    with open(path, "r", encoding="utf-8") as f:
        _HOLIDAYS_CACHE = json.load(f)

    return _HOLIDAYS_CACHE


def get_timeframe_config(timeframe: str) -> Dict[str, Any]:
    """Return the configuration block for a timeframe with safe defaults."""
    timeframes = load_config().get("timeframes", {})
    entry = timeframes.get(timeframe)
    if not isinstance(entry, dict):
        entry = {}

    default_interval = "1d" if timeframe == "1d" else timeframe
    return {
        "timeframe": timeframe,
        "name": entry.get("name", timeframe),
        "interval": entry.get("interval", default_interval),
        "horizon": int(entry.get("horizon", 14)),
        "yfinance_period": entry.get("yfinance_period", "2y"),
    }


def get_yfinance_period(timeframe: str = "1d") -> str:
    """Return the Yahoo Finance history window configured for a timeframe."""
    return get_timeframe_config(timeframe)["yfinance_period"]
