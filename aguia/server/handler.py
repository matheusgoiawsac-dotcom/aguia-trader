"""Hardened HTTP request handler strictly serving static/ and REST API."""

import http.server
import json
import mimetypes
from pathlib import Path
import sys
from typing import Optional, Set
from urllib.parse import urlparse

from aguia.config import ROOT_DIR, load_config
from aguia.server.routes import handle_api_status

STATIC_DIR = (ROOT_DIR / "static").resolve()

# Supported MIME types
MIME_MAP = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".ico": "image/x-icon",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
}


class AguiaRequestHandler(http.server.BaseHTTPRequestHandler):
    """Hardened HTTP Request Handler."""

    server_version = "AguiaTrader/1.0"

    def _get_allowed_origins(self) -> Set[str]:
        try:
            cfg = load_config()
            return set(cfg.get("server", {}).get("cors_origins", [
                "http://localhost:8000",
                "http://127.0.0.1:8000"
            ]))
        except Exception:
            return {"http://localhost:8000", "http://127.0.0.1:8000"}

    def _apply_cors_headers(self) -> None:
        origin = self.headers.get("Origin")
        allowed = self._get_allowed_origins()
        if origin in allowed:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept")
            self.send_header("Vary", "Origin")

    def _send_json(self, data: dict, status_code: int = 200) -> None:
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._apply_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, message: str, status_code: int = 404) -> None:
        self._send_json({"success": False, "error": message, "code": status_code}, status_code=status_code)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._apply_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        # Handle API routes
        if path.startswith("/api/"):
            if path == "/api/status":
                data = handle_api_status()
                return self._send_json(data, status_code=200)
            else:
                return self._send_error(f"Endpoint não encontrado: {path}", status_code=404)

        # Handle Static files strictly from static/
        if path in ("", "/"):
            relative_path = "index.html"
        else:
            relative_path = path.lstrip("/")

        target_file = (STATIC_DIR / relative_path).resolve()

        # Strict sandbox check: must be inside STATIC_DIR
        try:
            target_file.relative_to(STATIC_DIR)
        except ValueError:
            # Traversal attempt outside static directory
            return self._send_error("Acesso negado: fora do diretório estático", status_code=404)

        if not target_file.is_file():
            return self._send_error(f"Arquivo não encontrado: {path}", status_code=404)

        # Serve static file
        ext = target_file.suffix.lower()
        content_type = MIME_MAP.get(ext, mimetypes.guess_type(str(target_file))[0] or "application/octet-stream")

        try:
            with open(target_file, "rb") as f:
                content = f.read()

            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self._apply_cors_headers()
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self._send_error(f"Erro ao ler arquivo: {str(e)}", status_code=500)


def create_server(host: str = "127.0.0.1", port: int = 8000) -> http.server.ThreadingHTTPServer:
    """Create and configure ThreadingHTTPServer bound to localhost only."""
    server_address = (host, port)
    httpd = http.server.ThreadingHTTPServer(server_address, AguiaRequestHandler)
    httpd.daemon_threads = True
    return httpd


def run_server() -> None:
    """Entrypoint to run the server until interrupted."""
    # Ensure Windows console uses UTF-8
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    config = load_config()
    server_cfg = config.get("server", {})
    host = server_cfg.get("host", "127.0.0.1")
    port = server_cfg.get("port", 8000)

    httpd = create_server(host=host, port=port)
    print("=" * 65)
    print(" [*] [Águia Trader] Servidor Quantitativo Iniciado")
    print(f" [*] Host: http://{host}:{port}")
    print(f" [*] Diretorio Estático: {STATIC_DIR}")
    print(f" [*] Python: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    print(" Pressione Ctrl+C para encerrar.")
    print("=" * 65)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Servidor encerrado pelo usuário.")
    finally:
        httpd.server_close()
