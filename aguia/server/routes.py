"""REST API routing and handlers."""

from datetime import datetime, timezone
import json
import sys
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse

from aguia.config import load_config, load_universe
from aguia.db import get_connection, get_meta, init_db


def handle_api_status() -> Dict[str, Any]:
    """Handle GET /api/status."""
    config = load_config()

    refresh_status = {}
    try:
        init_db()
        conn = get_connection()
        try:
            for tf in config.get("timeframes", {}).get("available", ["1d", "15m", "5m"]):
                refresh_status[tf] = get_meta(conn, f"last_refresh_{tf}")
        finally:
            conn.close()
    except Exception:
        pass

    return {
        "status": "online",
        "brand": "Águia Trader",
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "server_time": datetime.now(timezone.utc).isoformat(),
        "kronos": {
            "loaded": False,
            "model": config.get("forecast", {}).get("model_id", "NeoQuasar/Kronos-small"),
            "device": "cpu"
        },
        "ollama": {
            "available": False,
            "model": config.get("ollama", {}).get("model", "auto")
        },
        "refresh": refresh_status,
        "disclaimer": config.get("compliance", {}).get(
            "disclaimer",
            "Análise experimental gerada por modelo estatístico. Não constitui recomendação de investimento. Sem backtest validado."
        )
    }
