"""Trading mode registry: Swing Trade (daily) and Day Trade (intraday).

Single source of truth shared by the API layer, the market data provider and
the rationale generator, so the front-end, the indicators and the text can
never disagree about which market horizon is active.

The registry is intentionally declarative: adding a third mode only requires
a new entry here plus the front-end mirror kept in ``static/script.js``
(``MODES``) — ``tests/test_modes.py`` asserts both stay in sync.
"""

from typing import Any, Dict, List, Optional

# High liquidity global assets used by the intraday (Day Trade) environment.
ATIVOS_DAY: List[str] = ["SPY", "DIA", "GC=F", "BTC-USD"]

# Human readable labels for the intraday assets (shown in the sidebar).
ROTULOS_ATIVOS_DAY: Dict[str, str] = {
    "SPY": "S&P 500",
    "DIA": "Dow Jones",
    "GC=F": "Ouro",
    "BTC-USD": "Bitcoin",
}

# Intraday intervals offered by the Day Trade workspace.
INTERVALOS_DAY: List[str] = ["5m", "15m", "1h"]

# Yahoo Finance history window per intraday interval (Yahoo truncates fast).
PERIODOS_Yahoo_DAY: Dict[str, str] = {
    "5m": "5d",
    "15m": "15d",
    "1h": "60d",
}

MODOS: Dict[str, Dict[str, Any]] = {
    "swing": {
        "id": "swing",
        "label": "Swing Trade",
        "contexto": "Modo Swing Trade • Gráfico Diário 14D",
        "mercado": "b3",
        "timeframe": "1d",
        "intervalo": "1d",
        "periodo_yahoo": "2y",
        "horizonte": 14,
        "moeda": "R$",
        "rotulo_alvo": "Alvo Projetado (14D)",
        "rotulo_stop": "Stop Loss Sugerido",
        "rotulo_payoff": "Relação Risco x Retorno",
        "rotulo_sub_alvo": "de projeção",
        "rotulo_sub_stop": "de risco",
        "indicadores": ["SMA 200", "WMA 30", "ATR 14"],
        "foco": "continuidade de tendência de médio prazo",
        "universo": "b3",
    },
    "day": {
        "id": "day",
        "label": "Day Trade",
        "contexto": "Modo Day Trade • Velas Intradiárias",
        "mercado": "global",
        "timeframe": "5m",
        "intervalo": "5m",
        "periodo_yahoo": "5d",
        "horizonte": 12,
        "moeda": "US$",
        "rotulo_alvo": "Alvo Intradia",
        "rotulo_stop": "Stop Intradia",
        "rotulo_payoff": "Risco x Retorno da Sessão",
        "rotulo_sub_alvo": "de projeção intradiária",
        "rotulo_sub_stop": "de risco na sessão",
        "indicadores": ["Rompimentos", "ATR 14", "Volume"],
        "foco": "rompimentos e volatilidade imediata",
        "universo": "global",
    },
}

MODO_PADRAO = "swing"


def get_modo(modo: Optional[str]) -> Dict[str, Any]:
    """Return the definition of a mode, falling back to Swing Trade."""
    key = (modo or "").strip().lower()
    if key not in MODOS:
        key = MODO_PADRAO
    return MODOS[key]


def normalizar_modo(modo: Optional[str]) -> str:
    """Return the canonical mode id ('swing' or 'day')."""
    return get_modo(modo)["id"]


def normalizar_intervalo(modo: Optional[str], intervalo: Optional[str]) -> str:
    """Return a valid interval for the given mode."""
    definicao = get_modo(modo)
    if definicao["id"] == "swing":
        return definicao["intervalo"]

    candidato = (intervalo or "").strip().lower()
    if candidato in INTERVALOS_DAY:
        return candidato
    return definicao["intervalo"]


def periodo_yahoo(modo: Optional[str], intervalo: Optional[str]) -> str:
    """Return the Yahoo Finance history window for a mode/interval pair."""
    definicao = get_modo(modo)
    if definicao["id"] == "swing":
        return definicao["periodo_yahoo"]

    return PERIODOS_Yahoo_DAY.get(
        normalizar_intervalo(modo, intervalo),
        definicao["periodo_yahoo"],
    )


def simbolo_yahoo(ticker: str, mercado: str) -> str:
    """Resolve the Yahoo Finance symbol of a ticker for a given market."""
    clean = ticker.upper().strip()
    if mercado == "global":
        # Global tickers already carry their Yahoo suffix (GC=F, BTC-USD).
        return clean
    return f"{clean.replace('.SA', '')}.SA"


def universo_do_modo(modo: Optional[str]) -> List[str]:
    """Return the ticker list monitored by a mode."""
    definicao = get_modo(modo)
    if definicao["universo"] == "global":
        return list(ATIVOS_DAY)

    from aguia.config import load_universe

    return list(load_universe())


def rotulo_ativo(ticker: str, modo: Optional[str]) -> str:
    """Return the display label of a ticker inside a mode."""
    definicao = get_modo(modo)
    if definicao["universo"] == "global":
        return ROTULOS_ATIVOS_DAY.get(ticker.upper(), ticker.upper())
    return ticker.upper()


def catalogo_modos() -> Dict[str, Any]:
    """Return the public catalogue consumed by the front-end."""
    catalogo: Dict[str, Any] = {}
    for modo_id, definicao in MODOS.items():
        catalogo[modo_id] = {
            "id": definicao["id"],
            "label": definicao["label"],
            "contexto": definicao["contexto"],
            "timeframe": definicao["timeframe"],
            "intervalo": definicao["intervalo"],
            "horizonte": definicao["horizonte"],
            "moeda": definicao["moeda"],
            "rotulo_alvo": definicao["rotulo_alvo"],
            "rotulo_stop": definicao["rotulo_stop"],
            "rotulo_payoff": definicao["rotulo_payoff"],
            "rotulo_sub_alvo": definicao["rotulo_sub_alvo"],
            "rotulo_sub_stop": definicao["rotulo_sub_stop"],
            "indicadores": list(definicao["indicadores"]),
            "foco": definicao["foco"],
            "universo": [rotulo_ativo(t, modo_id) for t in universo_do_modo(modo_id)],
            "tickers": list(universo_do_modo(modo_id)),
        }

    return {
        "padrao": MODO_PADRAO,
        "intervalos_day": list(INTERVALOS_DAY),
        "modes": catalogo,
    }
