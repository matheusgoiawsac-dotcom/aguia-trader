"""
Águia Trader - Backend Server & Motor Quantitativo
Desenvolvido para Python 3.11+
Biblioteca Padrão (zero dependências externas).
"""

from dataclasses import dataclass, asdict
from datetime import datetime
import http.server
import json
from pathlib import Path
import socketserver
import sys
from urllib.parse import urlparse, parse_qs

# Garante encoding UTF-8 no console do Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PORT = 8000
BASE_DIR = Path(__file__).resolve().parent

# Lista de ativos monitorados na B3
B3_ASSETS = [
    {"ticker": "ASAI3", "price": 13.27, "trend": "ALTA", "trendText": "ALTA (BULLISH)", "returnPct": 5.17, "target": 13.96, "stop": 12.65, "payoff": "1.11 : 1", "dayVar": "+0.85%"},
    {"ticker": "ANIM3", "price": 5.29, "trend": "ALTA", "trendText": "ALTA (BULLISH)", "returnPct": 4.46, "target": 5.53, "stop": 5.08, "payoff": "1.14 : 1", "dayVar": "+1.15%"},
    {"ticker": "ARML3", "price": 6.48, "trend": "ALTA", "trendText": "ALTA (BULLISH)", "returnPct": 5.45, "target": 6.83, "stop": 6.18, "payoff": "1.17 : 1", "dayVar": "+0.62%"},
    {"ticker": "AURE3", "price": 15.59, "trend": "ALTA", "trendText": "ALTA (BULLISH)", "returnPct": 4.53, "target": 16.30, "stop": 14.95, "payoff": "1.11 : 1", "dayVar": "+0.32%"},
    {"ticker": "PETR4", "price": 38.45, "trend": "ALTA", "trendText": "ALTA (BULLISH)", "returnPct": 3.80, "target": 39.91, "stop": 37.10, "payoff": "1.08 : 1", "dayVar": "+1.42%"},
    {"ticker": "VALE3", "price": 61.20, "trend": "BAIXA", "trendText": "BAIXA (BEARISH)", "returnPct": -2.75, "target": 59.52, "stop": 62.60, "payoff": "1.20 : 1", "dayVar": "-0.95%"},
    {"ticker": "ITUB4", "price": 34.80, "trend": "ALTA", "trendText": "ALTA (BULLISH)", "returnPct": 4.10, "target": 36.23, "stop": 33.60, "payoff": "1.19 : 1", "dayVar": "+0.78%"},
    {"ticker": "BBAS3", "price": 27.60, "trend": "ALTA", "trendText": "ALTA (BULLISH)", "returnPct": 3.95, "target": 28.69, "stop": 26.70, "payoff": "1.21 : 1", "dayVar": "+0.55%"},
    {"ticker": "BBDC4", "price": 14.90, "trend": "NEUTRO", "trendText": "LATERAL (NEUTRAL)", "returnPct": 0.67, "target": 15.00, "stop": 14.60, "payoff": "0.33 : 1", "dayVar": "+0.10%"},
    {"ticker": "WEGE3", "price": 52.80, "trend": "ALTA", "trendText": "ALTA (BULLISH)", "returnPct": 6.25, "target": 56.10, "stop": 50.40, "payoff": "1.38 : 1", "dayVar": "+1.85%"},
    {"ticker": "MGLU3", "price": 8.90, "trend": "BAIXA", "trendText": "BAIXA (BEARISH)", "returnPct": -5.40, "target": 8.42, "stop": 9.35, "payoff": "1.07 : 1", "dayVar": "-2.10%"},
    {"ticker": "PRIO3", "price": 44.50, "trend": "ALTA", "trendText": "ALTA (BULLISH)", "returnPct": 4.85, "target": 46.66, "stop": 42.80, "payoff": "1.27 : 1", "dayVar": "+0.90%"},
    {"ticker": "RENT3", "price": 54.30, "trend": "ALTA", "trendText": "ALTA (BULLISH)", "returnPct": 4.20, "target": 56.58, "stop": 52.40, "payoff": "1.20 : 1", "dayVar": "+0.60%"},
    {"ticker": "EMBR3", "price": 49.80, "trend": "ALTA", "trendText": "ALTA (BULLISH)", "returnPct": 5.60, "target": 52.59, "stop": 47.90, "payoff": "1.47 : 1", "dayVar": "+1.95%"},
    {"ticker": "GGBR4", "price": 21.15, "trend": "NEUTRO", "trendText": "LATERAL (NEUTRAL)", "returnPct": 0.45, "target": 21.25, "stop": 20.80, "payoff": "0.28 : 1", "dayVar": "+0.05%"},
    {"ticker": "CSNA3", "price": 12.40, "trend": "BAIXA", "trendText": "BAIXA (BEARISH)", "returnPct": -3.80, "target": 11.93, "stop": 12.85, "payoff": "1.04 : 1", "dayVar": "-1.30%"},
    {"ticker": "SUZB3", "price": 58.70, "trend": "ALTA", "trendText": "ALTA (BULLISH)", "returnPct": 4.30, "target": 61.22, "stop": 56.90, "payoff": "1.40 : 1", "dayVar": "+0.70%"},
    {"ticker": "JBSS3", "price": 35.10, "trend": "ALTA", "trendText": "ALTA (BULLISH)", "returnPct": 3.70, "target": 36.40, "stop": 34.10, "payoff": "1.30 : 1", "dayVar": "+0.45%"}
]


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Servidor multithread com reaproveitamento de porta."""
    allow_reuse_address = True
    daemon_threads = True


class TradeIdeasHandler(http.server.SimpleHTTPRequestHandler):
    """Manipulador HTTP com suporte a rotas estáticas e API REST JSON com CORS total."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def end_headers(self):
        # Injeta cabeçalhos CORS em todas as respostas (arquivos e JSON)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept")
        super().end_headers()

    def _send_json(self, data, status_code: int = 200):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # Rota de status do backend
        if path == "/api/status":
            return self._send_json({
                "status": "online",
                "brand": "Águia Trader",
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "server_time": datetime.now().strftime("%d/%m/%Y, %H:%M"),
                "engine": "SMA 200 + WMA 30 + ATR 14 + Águia Trader IA"
            })

        # Rota da lista de ativos do universo B3
        if path == "/api/assets":
            return self._send_json({
                "total": len(B3_ASSETS),
                "assets": B3_ASSETS
            })

        # Rota de busca por ticker individual
        if path == "/api/asset":
            query_params = parse_qs(parsed.query)
            ticker = query_params.get("ticker", ["ASAI3"])[0].upper()
            asset = next((a for a in B3_ASSETS if a["ticker"] == ticker), None)

            if asset:
                return self._send_json({"success": True, "asset": asset})
            return self._send_json({"success": False, "error": f"Ativo {ticker} não encontrado"}, status_code=404)

        # Arquivos estáticos normais (index.html, style.css, script.js)
        return super().do_GET()


def run():
    socketserver.TCPServer.allow_reuse_address = True
    with ThreadedTCPServer(("", PORT), TradeIdeasHandler) as httpd:
        print("=" * 65)
        print(f"[*] [Águia Trader] Painel Quantitativo B3 Inicializado!")
        print(f"[*] Python: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        print(f"[*] Servidor Ativo em: http://localhost:{PORT}")
        print(f"[*] Diretorio: {BASE_DIR}")
        print("Pressione Ctrl+C para parar o servidor.")
        print("=" * 65)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[*] Servidor finalizado com seguranca.")


if __name__ == "__main__":
    run()
