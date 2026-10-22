"""Integração com Ollama Local e Fallback Estatístico Determinístico."""

import json
from typing import Any, Dict, Optional, Tuple
import urllib.request
import urllib.error

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_TIMEOUT_SECONDS = 3.0  # Timeout curto para não travar a interface web


def verificar_status_ollama() -> Dict[str, Any]:
    """Verifica se o daemon do Ollama está rodando e retorna o primeiro modelo disponível."""
    url = f"{OLLAMA_BASE_URL}/api/tags"
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=1.2) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                models = data.get("models", [])
                modelo_nome = models[0]["name"] if models else "auto"
                return {
                    "online": True,
                    "modelo": modelo_nome,
                    "modelos_disponiveis": [m.get("name") for m in models],
                    "url": OLLAMA_BASE_URL
                }
    except Exception:
        pass

    return {
        "online": False,
        "modelo": None,
        "modelos_disponiveis": [],
        "url": OLLAMA_BASE_URL
    }


def gerar_racional_deterministico(setup: Dict[str, Any]) -> str:
    """
    Gera análise estatística determinística em português com base nos indicadores
    SMA 200, WMA 30 e ATR 14. Garante que a interface nunca fique sem resposta.
    """
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

    if tendencia == "ALTA":
        return (
            f"O ativo {ticker} demonstrou rompimento sustentado acima da WMA 30 (R$ {wma30:.2f}) "
            f"com alinhamento altista frente à SMA 200 (R$ {sma200:.2f}). A volatilidade recente "
            f"delimitada pelo ATR 14 em R$ {atr14:.2f} projeta continuidade de movimento com alvo em "
            f"R$ {alvo:.2f} ({ret_pct:+.2f}%) e stop loss estatístico sugerido em R$ {stop:.2f} "
            f"({risco_pct:.2f}%), estabelecendo uma relação risco x retorno de {payoff}."
        )
    elif tendencia == "BAIXA":
        return (
            f"O ativo {ticker} opera sob pressão vendedora institucional, negociando abaixo da "
            f"WMA 30 (R$ {wma30:.2f}) e divergente da SMA 200 (R$ {sma200:.2f}). O modelo estatístico "
            f"aponta recuo tático até os níveis de suporte projetados em R$ {alvo:.2f} ({ret_pct:+.2f}%) "
            f"com stop loss sugerido em R$ {stop:.2f} ({risco_pct:.2f}%) e relação risco x retorno "
            f"de {payoff}, baseado na dispersão do ATR 14 (R$ {atr14:.2f})."
        )
    else:
        return (
            f"O ativo {ticker} cotado a R$ {preco:.2f} encontra-se em fase de consolidação e compressão "
            f"de volatilidade entre a WMA 30 (R$ {wma30:.2f}) e a SMA 200 (R$ {sma200:.2f}). O ATR 14 de "
            f"R$ {atr14:.2f} indica equilíbrio temporário de forças. Alvo de referência fixado em "
            f"R$ {alvo:.2f} e stop loss em R$ {stop:.2f} com relação risco x retorno de {payoff}."
        )


def gerar_racional_ia(setup: Dict[str, Any]) -> Tuple[str, str]:
    """
    Solicita ao Ollama a redação do racional estatístico.
    Em caso de falha, timeout ou ausência do Ollama, aciona o fallback determinístico.
    Retorna uma tupla (texto_racional, fonte).
    """
    status = verificar_status_ollama()
    if not status["online"] or not status["modelo"]:
        return gerar_racional_deterministico(setup), "deterministico"

    ticker = setup.get("ticker", "ATIVO")
    preco = setup.get("preco", 0.0)
    alvo = setup.get("alvo", 0.0)
    stop = setup.get("stop", 0.0)
    payoff = setup.get("payoff", "1.00 : 1")
    ret_pct = setup.get("projecao_pct", 0.0)
    risco_pct = setup.get("risco_pct", 0.0)
    tendencia = setup.get("tendencia", "NEUTRO")
    indicadores = setup.get("indicadores", {})
    sma200 = indicadores.get("sma200", 0.0)
    wma30 = indicadores.get("wma30", 0.0)
    atr14 = indicadores.get("atr14", 0.0)

    prompt_sistema = (
        "Você é o assistente quantitativo sênior do Águia Trader, plataforma da B3 (Brasil). "
        "Sua tarefa é redigir um racional estatístico em português do Brasil (3 a 4 frases). "
        "Use apenas os dados fornecidos: ticker, preço, WMA 30, SMA 200, ATR 14, alvo e stop loss. "
        "Não invente números nem recomende explicitamente compra ou venda."
    )

    prompt_usuario = (
        f"Ativo: {ticker}\n"
        f"Preço Atual: R$ {preco:.2f}\n"
        f"Tendência: {tendencia}\n"
        f"WMA 30: R$ {wma30:.2f}\n"
        f"SMA 200: R$ {sma200:.2f}\n"
        f"ATR 14: R$ {atr14:.2f}\n"
        f"Alvo Projetado (14D): R$ {alvo:.2f} ({ret_pct:+.2f}%)\n"
        f"Stop Loss: R$ {stop:.2f} ({risco_pct:.2f}%)\n"
        f"Relação Risco x Retorno: {payoff}\n"
        "Redija a análise estatística técnica sucinta:"
    )

    payload = json.dumps({
        "model": status["modelo"],
        "messages": [
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": prompt_usuario}
        ],
        "stream": False,
        "options": {
            "temperature": 0.2
        }
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            f"{OLLAMA_BASE_URL}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT_SECONDS) as response:
            if response.status == 200:
                result = json.loads(response.read().decode("utf-8"))
                content = result.get("message", {}).get("content", "").strip()
                if content and len(content) > 30:
                    from aguia.explain.validator import validate_numbers
                    if validate_numbers(content, setup):
                        return content, "ollama"
    except Exception:
        pass

    # Fallback seguro
    return gerar_racional_deterministico(setup), "deterministico"
