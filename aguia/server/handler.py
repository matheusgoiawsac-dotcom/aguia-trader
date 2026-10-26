"""Hardened HTTP request handler strictly serving static/ and REST API."""

import gzip
import http.server
import json
import mimetypes
import os
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional, Set
from urllib.parse import parse_qs, urlparse

from aguia.config import ROOT_DIR, load_config
from aguia.explain.ollama import verificar_status_ollama
from aguia.server.routes import (
    handle_api_status,
    handle_api_status_ollama,
    handle_api_acoes,
    handle_api_analise,
    handle_api_dados,
    handle_api_modos,
    handle_api_estrategia_macro_jr,
)

STATIC_DIR = (ROOT_DIR / "static").resolve()

STRATEGY_PARAMS = {}
STRATEGY_REGISTRY = {"media_tendencia_macro_jr": {}}
ACTIVE_STRATEGY = {"id": None, "params": {}}

# Supported MIME types
MIME_MAP = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".ico": "image/x-icon",
    ".svg": "image/svg+xml",
    ".woff2": "font/woff2",
}

COMPRESSIBLE_TYPES = (
    "text/",
    "application/javascript",
    "application/json",
    "image/svg+xml",
)

GZIP_MIN_SIZE = 512
STATIC_MAX_AGE = 300
DEFAULT_CORS_ORIGINS = ("http://localhost:8000", "http://127.0.0.1:8000")

try:
    _server_config = load_config().get("server", {})
except Exception:
    _server_config = {}

ALLOWED_ORIGINS: Set[str] = set(
    _server_config.get("cors_origins", list(DEFAULT_CORS_ORIGINS))
)
LOG_REQUESTS: bool = bool(_server_config.get("log_requests", True))
COMPRESS_RESPONSES: bool = bool(_server_config.get("compress_responses", True))


class _StaticFile:
    """Cached representation of a file on disk."""

    __slots__ = ("body", "gzip_body", "etag", "content_type", "mtime_ns", "size")

    def __init__(self, body: bytes, content_type: str, mtime_ns: int) -> None:
        self.body = body
        self.content_type = content_type
        self.mtime_ns = mtime_ns
        self.size = len(body)
        self.etag = f'"{mtime_ns:x}-{self.size:x}"'
        self.gzip_body: Optional[bytes] = None
        if COMPRESS_RESPONSES and self.size >= GZIP_MIN_SIZE and _is_compressible(content_type):
            self.gzip_body = gzip.compress(body, compresslevel=6, mtime=0)


_static_cache: Dict[str, _StaticFile] = {}
_static_lock = threading.Lock()


def _is_compressible(content_type: str) -> bool:
    return any(content_type.startswith(prefix) for prefix in COMPRESSIBLE_TYPES)


def _load_static_file(target: Path) -> Optional[_StaticFile]:
    """Return the cached representation of a static file, reloading on change."""
    try:
        stat = target.stat()
    except OSError:
        return None

    key = str(target)
    with _static_lock:
        cached = _static_cache.get(key)
        if cached is not None and cached.mtime_ns == stat.st_mtime_ns and cached.size == stat.st_size:
            return cached

    try:
        body = target.read_bytes()
    except OSError:
        return None

    ext = target.suffix.lower()
    content_type = MIME_MAP.get(ext) or mimetypes.guess_type(str(target))[0] or "application/octet-stream"

    entry = _StaticFile(body, content_type, stat.st_mtime_ns)
    with _static_lock:
        _static_cache[key] = entry
    return entry


class AguiaRequestHandler(http.server.BaseHTTPRequestHandler):
    """Hardened HTTP Request Handler."""

    server_version = "AguiaTrader/1.0"
    # Keep-alive support: every response carries an accurate Content-Length.
    protocol_version = "HTTP/1.1"
    # Drop idle keep-alive connections instead of pinning a worker thread forever.
    timeout = 30

    def _apply_cors_headers(self) -> None:
        origin = self.headers.get("Origin")
        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept")
            self.send_header("Vary", "Origin")

    def _accepts_gzip(self) -> bool:
        return "gzip" in (self.headers.get("Accept-Encoding") or "").lower()

    def _send_bytes(
        self,
        body: bytes,
        content_type: str,
        status_code: int = 200,
        extra_headers: Optional[Dict[str, str]] = None
    ) -> None:
        headers = dict(extra_headers or {})
        if (
            COMPRESS_RESPONSES
            and len(body) >= GZIP_MIN_SIZE
            and _is_compressible(content_type)
            and self._accepts_gzip()
        ):
            body = gzip.compress(body, compresslevel=6, mtime=0)
            headers["Content-Encoding"] = "gzip"
            headers["Vary"] = "Accept-Encoding"

        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        for key, value in headers.items():
            self.send_header(key, value)
        self._apply_cors_headers()
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _send_json(self, data: dict, status_code: int = 200) -> None:
        body = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self._send_bytes(
            body,
            "application/json; charset=utf-8",
            status_code=status_code,
            extra_headers={"Cache-Control": "no-cache"},
        )

    def _send_error(self, message: str, status_code: int = 404) -> None:
        self._send_json({
            "sucesso": False,
            "success": False,
            "dados": None,
            "erro": message,
            "error": message,
            "code": status_code
        }, status_code=status_code)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Content-Length", "0")
        self._apply_cors_headers()
        self.end_headers()

    def do_HEAD(self) -> None:
        self._route()

    def do_GET(self) -> None:
        self._route()

    def do_POST(self) -> None:
        self._route_post()

    def _route(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/"):
            try:
                if path == "/api/status":
                    return self._send_json(handle_api_status(), status_code=200)
                if path == "/api/status_ollama":
                    return self._send_json(handle_api_status_ollama(), status_code=200)
                if path == "/api/modos":
                    return self._send_json(handle_api_modos(), status_code=200)
                if path in ("/api/acoes", "/api/assets", "/api/universe"):
                    query_params = parse_qs(parsed.query)
                    modo = query_params.get("modo", [None])[0]
                    return self._send_json(handle_api_acoes(modo), status_code=200)
                if path in ("/api/dados", "/api/data"):
                    query_params = parse_qs(parsed.query)
                    ticker = query_params.get("ticker", ["PETR4"])[0].upper()
                    modo = query_params.get("modo", [None])[0]
                    intervalo = query_params.get("intervalo", [None])[0]
                    data = handle_api_dados(ticker, modo=modo, intervalo=intervalo)
                    status_code = 200 if data.get("sucesso", True) else 400
                    return self._send_json(data, status_code=status_code)
                if path in ("/api/analise", "/api/analysis", "/api/asset"):
                    query_params = parse_qs(parsed.query)
                    ticker = query_params.get("ticker", ["PETR4"])[0].upper()
                    data = handle_api_analise(ticker)
                    status_code = 200 if data.get("sucesso", True) else 400
                    return self._send_json(data, status_code=status_code)
                if path == "/api/chart.png":
                    query_params = parse_qs(parsed.query)
                    ticker = query_params.get("ticker", ["PETR4"])[0].upper()
                    tf = query_params.get("tf", ["1d"])[0].lower()
                    # matplotlib is heavy: import it only when a chart is requested.
                    from aguia.charts.png_export import export_chart_png

                    png_bytes = export_chart_png(ticker, timeframe=tf)
                    return self._send_bytes(
                        png_bytes,
                        "image/png",
                        status_code=200,
                        extra_headers={"Cache-Control": "public, max-age=60"},
                    )
                return self._send_error(f"Endpoint nao encontrado: {path}", status_code=404)
            except Exception as e:
                import traceback
                traceback.print_exc()
                return self._send_json({
                    "sucesso": False,
                    "dados": None,
                    "erro": f"Erro interno ao processar requisicao: {str(e)}"
                }, status_code=500)

        self._serve_static(path)

    def _route_post(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/"):
            try:
                if path == "/api/update-strategy":
                    content_length = int(self.headers.get("Content-Length", "0"))
                    raw = self.rfile.read(content_length) if content_length > 0 else b"{}"
                    try:
                        payload = json.loads(raw.decode("utf-8"))
                    except Exception:
                        payload = {}
                    sid = payload.get("strategy_id", "media_tendencia_macro_jr")
                    params = payload.get("params", payload)
                    if sid not in STRATEGY_REGISTRY:
                        return self._send_error("Estrategia desconhecida", status_code=400)
                    STRATEGY_REGISTRY[sid] = params
                    ACTIVE_STRATEGY["id"] = sid
                    ACTIVE_STRATEGY["params"] = params
                    return self._send_json({"status": "success"}, status_code=200)
                if path == "/api/estrategia":
                    content_length = int(self.headers.get("Content-Length", "0"))
                    raw = self.rfile.read(content_length) if content_length > 0 else b"{}"
                    try:
                        payload = json.loads(raw.decode("utf-8"))
                    except Exception:
                        payload = {}
                    data = handle_api_estrategia_macro_jr(payload)
                    status_code = 200 if data.get("sucesso", True) else 400
                    return self._send_json(data, status_code=status_code)
                return self._send_error(f"Endpoint nao encontrado: {path}", status_code=404)
            except Exception as e:
                import traceback
                traceback.print_exc()
                return self._send_json({
                    "sucesso": False,
                    "dados": None,
                    "erro": f"Erro interno ao processar requisicao: {str(e)}"
                }, status_code=500)

        self.send_response(405)
        self.send_header("Allow", "GET, HEAD, OPTIONS")
        self._apply_cors_headers()
        self.end_headers()

    def _serve_static(self, path: str) -> None:
        relative_path = "index.html" if path in ("", "/") else path.lstrip("/")
        target_file = (STATIC_DIR / relative_path).resolve()

        # Strict sandbox check: must be inside STATIC_DIR
        try:
            target_file.relative_to(STATIC_DIR)
        except ValueError:
            return self._send_error("Acesso negado: fora do diretorio estatico", status_code=404)

        entry = _load_static_file(target_file)
        if entry is None:
            return self._send_error(f"Arquivo nao encontrado: {path}", status_code=404)

        etag = entry.etag
        if self.headers.get("If-None-Match") == etag:
            self.send_response(304)
            self.send_header("ETag", etag)
            self.send_header("Content-Length", "0")
            self.send_header("Cache-Control", f"public, max-age={STATIC_MAX_AGE}")
            self._apply_cors_headers()
            self.end_headers()
            return

        headers = {
            "ETag": etag,
            "Last-Modified": self.date_time_string(int(entry.mtime_ns / 1_000_000_000)),
            "Cache-Control": (
                "no-cache" if entry.content_type.startswith("text/html")
                else f"public, max-age={STATIC_MAX_AGE}"
            ),
        }

        if self._accepts_gzip() and entry.gzip_body is not None:
            body = entry.gzip_body
            headers["Content-Encoding"] = "gzip"
            headers["Vary"] = "Accept-Encoding"
        else:
            body = entry.body

        self.send_response(200)
        self.send_header("Content-Type", entry.content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        for key, value in headers.items():
            self.send_header(key, value)
        self._apply_cors_headers()
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def log_request(self, code: Any = "-", size: Any = "-") -> None:
        if not LOG_REQUESTS:
            return
        elapsed = getattr(self, "_t0", None)
        duration = f" {(time.perf_counter() - elapsed) * 1000:.1f}ms" if elapsed else ""
        sys.stderr.write(
            f"[aguia] {self.client_address[0]} {self.command} {self.path} {code}{duration}\n"
        )

    def log_message(self, format: str, *args: Any) -> None:
        if not LOG_REQUESTS:
            return
        sys.stderr.write(f"[aguia] {format % args}\n")

    def handle_one_request(self) -> None:
        self._t0 = time.perf_counter()
        super().handle_one_request()


def warm_up() -> None:
    """
    Pre-warm external dependencies in the background.

    Probing the local LLM daemon can take a full socket timeout when it is
    offline; doing it while the server is already accepting requests keeps the
    first user request free of that delay.
    """

    def _worker() -> None:
        try:
            verificar_status_ollama()
        except Exception:
            pass

    threading.Thread(target=_worker, name="aguia-warmup", daemon=True).start()


def create_server(host: str = "127.0.0.1", port: int = 8000) -> http.server.ThreadingHTTPServer:
    """Create and configure ThreadingHTTPServer bound to localhost only."""
    server_address = (host, port)
    httpd = http.server.ThreadingHTTPServer(server_address, AguiaRequestHandler)
    httpd.daemon_threads = True
    return httpd


def run_server(host: Optional[str] = None, port: Optional[int] = None) -> None:
    """Entrypoint to run the server until interrupted."""
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    config = load_config()
    server_cfg = config.get("server", {})
    host = host or server_cfg.get("host", "127.0.0.1")
    port = int(port or server_cfg.get("port", 8000))

    httpd = create_server(host=host, port=port)
    warm_up()
    print("=" * 65)
    print(" [*] [Aguia Trader] Servidor Quantitativo Iniciado")
    print(f" [*] Host: http://{host}:{port}")
    print(f" [*] Diretorio Estatico: {STATIC_DIR}")
    print(f" [*] Python: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    print(" [*] Status: Servidor Ativo e Online")
    print(" Pressione Ctrl+C para encerrar.")
    print("=" * 65)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Servidor encerrado pelo usuario.")
    finally:
        httpd.server_close()
