"""Águia Trader - Thin Application Entrypoint.

The whole application lives in ``aguia/``; this file only wires the
command line to the HTTP server. Usage:

    python app.py                 # host/port from config/config.toml
    python app.py --port 8080     # overrides the configured port
"""

import argparse
import sys

from aguia.server.handler import run_server


def _parse_args(argv: list) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="aguia-trader",
        description="Águia Trader - dashboard quantitativo B3 (servidor local).",
    )
    parser.add_argument(
        "--host",
        default=None,
        help="Interface de escuta (padrao: config/config.toml, 127.0.0.1).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Porta HTTP (padrao: config/config.toml, 8000).",
    )
    return parser.parse_args(argv)


def main(argv: list = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    run_server(host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
