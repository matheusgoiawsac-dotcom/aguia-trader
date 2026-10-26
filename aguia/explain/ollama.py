"""Ollama local integration with a deterministic statistical fallback.

The dashboard must never block on a missing LLM daemon. Every network call
here is therefore bounded by a short timeout, memoised for a few seconds and
protected by a circuit breaker that keeps the daemon out of the hot path once
it is known to be down.
"""

import http.client
import json
import threading
import time
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

from aguia.explain.validator import validate_numbers

DEFAULT_OLLAMA_URL = "http://localhost:11434"

# Socket timeout for the health probe. A dead daemon on Windows can keep the
# TCP stack in SYN-retry for seconds, so the probe budget has to stay tight.
PROBE_TIMEOUT_SECONDS = 0.25
# Budget for an actual completion request.
CHAT_TIMEOUT_SECONDS = 3.0
# How long a successful/forgotten status is reused.
STATUS_TTL_SECONDS = 5.0
# How long the daemon is considered unreachable after a failed probe.
FAILURE_COOLDOWN_SECONDS = 30.0

_OFFLINE: Dict[str, Any] = {
    "online": False,
    "modelo": None,
    "modelos_disponiveis": [],
    "url": DEFAULT_OLLAMA_URL,
}

_state_lock = threading.Lock()
_probe_lock = threading.Lock()
_status_cache: Optional[Tuple[float, Dict[str, Any]]] = None
_retry_after: float = 0.0


def _ollama_url() -> str:
    """Resolve the configured Ollama URL, falling back to the local default."""
    try:
        from aguia.config import load_config

        url = load_config().get("ollama", {}).get("url")
        if isinstance(url, str) and url.strip():
            return url.strip()
    except Exception:
        pass
    return DEFAULT_OLLAMA_URL


def _split_url(url: str) -> Tuple[str, int]:
    """Split an Ollama URL into a connectable host and port."""
    parsed = urlparse(url)
    host = parsed.hostname or "127.0.0.1"
    # "localhost" resolves to ::1 first on Windows, and the IPv6 loopback
    # handshake can stall for seconds when nothing is listening.
    if host in ("localhost", "::1", "0.0.0.0"):
        host = "127.0.0.1"
    port = parsed.port or 11434
    return host, port


def _request(
    method: str,
    path: str,
    payload: Optional[bytes] = None,
    timeout: float = PROBE_TIMEOUT_SECONDS,
) -> Optional[Dict[str, Any]]:
    """Perform a single bounded HTTP request against the local Ollama daemon."""
    host, port = _split_url(_ollama_url())
    headers = {"Accept": "application/json"}
    if payload is not None:
        headers["Content-Type"] = "application/json"

    conn = http.client.HTTPConnection(host, port, timeout=timeout)
    try:
        conn.request(method, path, body=payload, headers=headers)
        response = conn.getresponse()
        if response.status != 200:
            return None
        return json.loads(response.read().decode("utf-8"))
    except Exception:
        return None
    finally:
        try:
            conn.close()
        except Exception:
            pass


def verificar_status_ollama(force: bool = False) -> Dict[str, Any]:
    """Return the Ollama daemon status, using the cached result when possible."""
    global _status_cache, _retry_after

    url = _ollama_url()
    now = time.monotonic()

    with _state_lock:
        cached = _status_cache
        if not force and cached is not None and (now - cached[0]) < STATUS_TTL_SECONDS:
            return dict(cached[1])
        if now < _retry_after:
            return {**_OFFLINE, "url": url}

    # Only one probe in flight: concurrent callers wait and reuse its result.
    with _probe_lock:
        with _state_lock:
            cached = _status_cache
            if not force and cached is not None and (time.monotonic() - cached[0]) < STATUS_TTL_SECONDS:
                return dict(cached[1])

        data = _request("GET", "/api/tags", timeout=PROBE_TIMEOUT_SECONDS)

        if data is None:
            offline = {**_OFFLINE, "url": url}
            with _state_lock:
                _retry_after = time.monotonic() + FAILURE_COOLDOWN_SECONDS
                _status_cache = (time.monotonic(), offline)
            return dict(offline)

        models = data.get("models", []) or []
        status = {
            "online": True,
            "modelo": models[0].get("name") if models else "auto",
            "modelos_disponiveis": [m.get("name") for m in models],
            "url": url,
        }
        with _state_lock:
            _status_cache = (time.monotonic(), status)
        return dict(status)


def _br(valor: float) -> str:
    """Format a number in the Brazilian decimal convention."""
    return f"{valor:.2f}".replace(".", ",")


def _pct_br(valor: float, sinal: bool = False) -> str:
    """Format a percentage in the Brazilian decimal convention."""
    modelo = "+.2f" if sinal else ".2f"
    return f"{valor:{modelo}}".replace(".", ",")


def _preco_br(simbolo: str, valor: float) -> str:
    """Format a price with its currency symbol."""
    return f"{simbolo} {_br(valor)}"


def _contexto_dicas(setup: Dict[str, Any]) -> Dict[str, Any]:
    """Extract the facts shared by both trading modes."""
    ticker = setup.get("ticker", "ATIVO")
    preco = setup.get("preco", 0.0)
    alvo = setup.get("alvo", 0.0)
    stop = setup.get("stop", 0.0)
    payoff = setup.get("payoff", "1.00 : 1")
    ret_pct = setup.get("projecao_pct", 0.0)
    risco_pct = setup.get("risco_pct", 0.0)
    tendencia = setup.get("tendencia", "NEUTRO")
    indicadores = setup.get("indicadores", {})
    sma200 = indicadores.get("sma200", preco * 0.95)
    wma30 = indicadores.get("wma30", preco * 0.98)
    atr14 = indicadores.get("atr14", preco * 0.03)

    return {
        "ticker": ticker,
        "preco": preco,
        "alvo": alvo,
        "stop": stop,
        "payoff": payoff,
        "ret_pct": ret_pct,
        "risco_pct": risco_pct,
        "tendencia": tendencia,
        "sma200": sma200,
        "wma30": wma30,
        "atr14": atr14,
    }


def gerar_racional_deterministico(setup: Dict[str, Any], modo: str = "swing") -> str:
    """
    Gera as dicas operacionais em português com base nos indicadores
    SMA 200, WMA 30 e ATR 14. Garante que a interface nunca fique sem resposta.

    O texto é observacional (nunca imperativo de compra ou venda) e traz um
    ponto de ação concreto para a mesa: gatilho de entrada, stop e alvo.
    """
    if modo == "day":
        return _dicas_deterministicas_day(setup)

    ctx = _contexto_dicas(setup)
    ticker = ctx["ticker"]
    preco = ctx["preco"]
    alvo = ctx["alvo"]
    stop = ctx["stop"]
    payoff = ctx["payoff"]
    ret_pct = ctx["ret_pct"]
    risco_pct = ctx["risco_pct"]
    tendencia = ctx["tendencia"]
    sma200 = ctx["sma200"]
    wma30 = ctx["wma30"]
    atr14 = ctx["atr14"]
    simbolo = setup.get("moeda", "R$")

    if tendencia == "ALTA":
        return (
            f"Dica Operacional: observar a confirmação de volume acima de {_preco_br(simbolo, wma30)} "
            f"(WMA 30) como gatilho de entrada, com stop de {_preco_br(simbolo, stop)} "
            f"({_br(risco_pct)}%) e alvo em {_preco_br(simbolo, alvo)} ({_pct_br(ret_pct, sinal=True)}%). "
            f"O ativo {ticker} demonstrou rompimento sustentado acima da WMA 30 "
            f"({_preco_br(simbolo, wma30)}) com alinhamento altista frente à SMA 200 "
            f"({_preco_br(simbolo, sma200)}). A volatilidade recente delimitada pelo ATR 14 em "
            f"{_preco_br(simbolo, atr14)} projeta continuidade de movimento, estabelecendo uma "
            f"relação risco x retorno de {payoff}."
        )
    elif tendencia == "BAIXA":
        return (
            f"Dica Operacional: observar a reação na faixa de {_preco_br(simbolo, stop)} como "
            f"nível de invalidação do cenário de pressão vendedora, com alvo de recomposição em "
            f"{_preco_br(simbolo, alvo)} ({_pct_br(ret_pct, sinal=True)}%) e risco de {_preco_br(simbolo, stop)} "
            f"({_br(risco_pct)}%). O ativo {ticker} opera sob pressão vendedora institucional, "
            f"negociando abaixo da WMA 30 ({_preco_br(simbolo, wma30)}) e divergente da SMA 200 "
            f"({_preco_br(simbolo, sma200)}). O modelo estatístico aponta recuo tático até os "
            f"níveis de suporte projetados, com relação risco x retorno de {payoff}, baseado na "
            f"dispersão do ATR 14 ({_preco_br(simbolo, atr14)})."
        )
    else:
        return (
            f"Dica Operacional: observar a compressão de volatilidade entre "
            f"{_preco_br(simbolo, wma30)} e {_preco_br(simbolo, sma200)} antes de definir o "
            f"gatilho; alvo de referência em {_preco_br(simbolo, alvo)} e stop em "
            f"{_preco_br(simbolo, stop)} ({_br(risco_pct)}%), com relação risco x retorno de "
            f"{payoff}. O ativo {ticker} cotado a {_preco_br(simbolo, preco)} encontra-se em fase "
            f"de consolidação. O ATR 14 de {_preco_br(simbolo, atr14)} indica equilíbrio "
            f"temporário de forças."
        )


def _dicas_deterministicas_day(setup: Dict[str, Any]) -> str:
    """Dicas operacionais de curtíssimo prazo (rompimentos e volatilidade)."""
    ctx = _contexto_dicas(setup)
    ticker = ctx["ticker"]
    preco = ctx["preco"]
    alvo = ctx["alvo"]
    stop = ctx["stop"]
    payoff = ctx["payoff"]
    ret_pct = ctx["ret_pct"]
    risco_pct = ctx["risco_pct"]
    tendencia = ctx["tendencia"]
    sma200 = ctx["sma200"]
    wma30 = ctx["wma30"]
    atr14 = ctx["atr14"]
    simbolo = setup.get("moeda", "US$")
    intervalo = setup.get("intervalo", "5m")
    vela = setup.get("vela_anterior") or {}
    maxima_anterior = vela.get("maxima", preco)

    direcao = (
        "rompimento de alta"
        if tendencia == "ALTA"
        else ("rompimento de baixa" if tendencia == "BAIXA" else "rompimento dos extremos da vela")
    )

    return (
        f"Dica Operacional: na vela de {intervalo}, o gatilho de entrada é o {direcao} acima de "
        f"{_preco_br(simbolo, maxima_anterior)} com volume acima da média; a reação define a "
        f"execução, com stop em {_preco_br(simbolo, stop)} ({_br(risco_pct)}%) e alvo em "
        f"{_preco_br(simbolo, alvo)} ({_pct_br(ret_pct, sinal=True)}%) e relação risco x retorno de {payoff}. "
        f"O ativo {ticker} opera a {_preco_br(simbolo, preco)}, com ATR 14 de "
        f"{_preco_br(simbolo, atr14)} dimensionando a volatilidade da sessão, WMA 30 em "
        f"{_preco_br(simbolo, wma30)} como referência de preço e SMA 200 em "
        f"{_preco_br(simbolo, sma200)} como piso do cenário."
    )


def _prompt_sistema(modo: str) -> str:
    """System prompt for the operational tips, tuned per trading mode."""
    if modo == "day":
        return (
            "Você é o assistente quantitativo sênior do Águia Trader, especializado em "
            "operações intradiárias. Escreva em português do Brasil 3 a 4 frases de dicas "
            "operacionais práticas para a mesa: gatilho de entrada por rompimento, confirmação "
            "de volume, nível de stop e alvo da vela. Use apenas os números fornecidos, sem "
            "inventar nenhum. Use linguagem observacional e condicional ('observar', 'aguardar "
            "confirmação de volume', 'atenção ao gatilho'), nunca imperativos de compra ou venda."
        )

    return (
        "Você é o assistente quantitativo sênior do Águia Trader. Escreva em português do "
        "Brasil 3 a 4 frases de dicas operacionais práticas para a mesa: pontos de observação, "
        "gatilho de entrada, nível de stop e alvo de 14 dias. Use apenas os números fornecidos, "
        "sem inventar nenhum. Use linguagem observacional e condicional ('observar', 'aguardar "
        "confirmação de volume', 'atenção ao gatilho'), nunca imperativos de compra ou venda."
    )


def _prompt_usuario(setup: Dict[str, Any], modo: str) -> str:
    """User prompt carrying the facts the model is allowed to cite."""
    ctx = _contexto_dicas(setup)
    simbolo = setup.get("moeda", "R$")
    intervalo = setup.get("intervalo", "1d")
    horizonte = setup.get("horizonte", 14)
    vela = setup.get("vela_anterior") or {}

    linhas = [
        f"Ativo: {ctx['ticker']}",
        f"Preço Atual: {_preco_br(simbolo, ctx['preco'])}",
        f"Tendência: {ctx['tendencia']}",
        f"WMA 30: {_preco_br(simbolo, ctx['wma30'])}",
        f"SMA 200: {_preco_br(simbolo, ctx['sma200'])}",
        f"ATR 14: {_preco_br(simbolo, ctx['atr14'])}",
    ]

    if modo == "day":
        linhas += [
            f"Vela: {intervalo}",
            f"Máxima da vela anterior: {_preco_br(simbolo, vela.get('maxima', ctx['preco']))}",
            f"Mínima da vela anterior: {_preco_br(simbolo, vela.get('minima', ctx['preco']))}",
            f"Alvo da vela: {_preco_br(simbolo, ctx['alvo'])} ({_pct_br(ctx['ret_pct'], sinal=True)}%)",
            f"Stop da vela: {_preco_br(simbolo, ctx['stop'])} ({_br(ctx['risco_pct'])}%)",
            f"Relação Risco x Retorno: {ctx['payoff']}",
        ]
    else:
        linhas += [
            f"Alvo Projetado ({horizonte}D): {_preco_br(simbolo, ctx['alvo'])} ({_pct_br(ctx['ret_pct'], sinal=True)}%)",
            f"Stop Loss: {_preco_br(simbolo, ctx['stop'])} ({_br(ctx['risco_pct'])}%)",
            f"Relação Risco x Retorno: {ctx['payoff']}",
        ]

    linhas.append(
        "Redija as dicas operacionais:" if modo == "day" else "Redija as dicas operacionais:"
    )
    return "\n".join(linhas)


def gerar_racional_ia(setup: Dict[str, Any], modo: str = "swing") -> Tuple[str, str]:
    """
    Solicita ao Ollama a redação das dicas operacionais.
    Em caso de falha, timeout ou ausência do Ollama, aciona o fallback determinístico.
    Retorna uma tupla (texto_racional, fonte).
    """
    status = verificar_status_ollama()
    if not status["online"] or not status["modelo"]:
        return gerar_racional_deterministico(setup, modo), "deterministico"

    payload = json.dumps({
        "model": status["modelo"],
        "messages": [
            {"role": "system", "content": _prompt_sistema(modo)},
            {"role": "user", "content": _prompt_usuario(setup, modo)}
        ],
        "stream": False,
        "options": {
            "temperature": 0.2
        }
    }).encode("utf-8")

    result = _request(
        "POST",
        "/api/chat",
        payload=payload,
        timeout=CHAT_TIMEOUT_SECONDS,
    )

    if result is not None:
        content = result.get("message", {}).get("content", "").strip()
        if content and len(content) > 30 and validate_numbers(content, setup):
            return content, "ollama"

    # Fallback seguro
    return gerar_racional_deterministico(setup, modo), "deterministico"
