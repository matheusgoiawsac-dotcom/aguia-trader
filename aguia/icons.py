"""Asset classification for the Cyber/Neon icon factory.

The dashboard draws a 22x22 vector icon for every asset. The icon is
chosen by category (crypto, forex, commodity, index) and, for B3
stocks, by sector (banking, energy, mining, retail, health).

This module is the single source of truth for that classification: the
API publishes ``categoria`` and ``setor`` with every asset so the
front-end never has to guess. ``static/script.js`` keeps a mirrored
registry (``ICON_CRYPTO_MAP``, ``ICON_B3_SECTORS``, ...) and
``tests/test_icons.py`` asserts the two never drift apart.
"""

from typing import Any, Dict, Optional

CATEGORIA_CRIPTO = "cripto"
CATEGORIA_FOREX = "forex"
CATEGORIA_COMMODITY = "commodity"
CATEGORIA_INDICE = "indice"
CATEGORIA_B3 = "b3"

CATEGORIAS = (
    CATEGORIA_CRIPTO,
    CATEGORIA_FOREX,
    CATEGORIA_COMMODITY,
    CATEGORIA_INDICE,
    CATEGORIA_B3,
)

# Setores reconhecidos dentro da B3 (o restante usa o icone universal).
SETOR_BANCO = "banco"
SETOR_ENERGIA = "energia"
SETOR_MINERACAO = "mineracao"
SETOR_VAREJO = "varejo"
SETOR_SAUDE = "saude"

# Criptomoedas -> glifo do icone
CRIPTOMOEDAS: Dict[str, str] = {
    "BTC-USD": "btc",
    "ETH-USD": "eth",
    "SOL-USD": "sol",
    "USDT-USD": "usdt",
    "USDC-USD": "usdc",
    "BNB-USD": "bnb",
    "XRP-USD": "xrp",
    "ADA-USD": "ada",
    "DOGE-USD": "doge",
    "AVAX-USD": "avax",
}

# Pares de cambio e indicadores em dolar
FOREX: Dict[str, str] = {
    "USDBRL=X": "usd",
    "BRL=X": "brl",
    "DXY": "usd",
    "USD=X": "usd",
    "EURUSD=X": "eur",
    "GBPUSD=X": "gbp",
    "USDJPY=X": "usd",
    "USDCAD=X": "usd",
}

# Commodities -> glifo do icone
COMMODITIES: Dict[str, str] = {
    "GC=F": "gold",
    "XAUUSD=X": "gold",
    "SI=F": "silver",
    "XAGUSD=X": "silver",
    "HG=F": "copper",
    "CL=F": "oil",
    "BZ=F": "oil",
    "ZC=F": "corn",
    "ZS=F": "soy",
}

# Indices -> glifo do icone
INDICES: Dict[str, str] = {
    "^GSPC": "indexChart",
    "SPY": "indexChart",
    "^DJI": "indexBars",
    "DIA": "indexBars",
    "^IXIC": "indexArrow",
    "QQQ": "indexArrow",
    "^BVSP": "indexIbovespa",
}

# Setores da B3: banco, energia, mineracao, varejo/alimentacao e
# saude/educacao. Todo o resto cai no icone universal.
SETORES_B3: Dict[str, tuple] = {
    SETOR_BANCO: (
        "ITUB4", "BBDC4", "BBAS3", "BPSA3", "BRSR6", "ITSA4", "SANB11",
        "B3SA3", "CMIG4", "BBTC", "BPAC11", "BANC11", "BRBI11", "PSBB11",
        "BMEB3",
    ),
    SETOR_ENERGIA: (
        "PETR4", "PETR3", "PRIO3", "RPRL3", "VBBR3", "EQTL3", "OSBR3",
        "CSAN3", "LOGG3", "DMMO3",
    ),
    SETOR_MINERACAO: (
        "VALE3", "GGBR4", "MMX3", "BRAD3", "BRAP4", "AGL3", "CSNA3",
        "VAMO3", "USIM5", "PARIM3",
    ),
    SETOR_VAREJO: (
        "MGLU3", "LREN3", "ABEV3", "MRVE3", "JBSS3", "SUZB3", "CASH3",
        "PETZ3", "BHIA3", "SOMA3", "RADL3", "AZUL3", "KLBN3", "ASAI3",
        "AURE3", "RENT3",
    ),
    SETOR_SAUDE: (
        "RDOR3", "FLRY3", "HSML3", "PSSA3", "COGN3", "YDUQ3", "VERO3",
        "CURA3", "APIM3", "OPM3", "PFGC3", "ANIM3",
    ),
}


def _normalizar(ticker: str) -> str:
    return str(ticker or "").strip().upper()


# Flat inverted index: ticker -> setor. Built once at import time so that
# ``setor_do_ativo`` is O(1) instead of iterating every sector tuple on each call.
_SETOR_INDEX: Dict[str, str] = {}
for _setor, _tickers in SETORES_B3.items():
    for _ticker in _tickers:
        _SETOR_INDEX[_ticker] = _setor


def setor_do_ativo(ticker: str) -> Optional[str]:
    """Return the B3 sector of a ticker, or ``None`` when it has no sector."""
    return _SETOR_INDEX.get(_normalizar(ticker))


def categoria_do_ativo(ticker: str) -> str:
    """Classify a ticker into one of the icon categories."""
    t = _normalizar(ticker)

    if t in CRIPTOMOEDAS:
        return CATEGORIA_CRIPTO
    if t in COMMODITIES:
        return CATEGORIA_COMMODITY
    if t in FOREX or (t.endswith("=X") and "USD" in t):
        return CATEGORIA_FOREX
    if t in INDICES or t.startswith("^"):
        return CATEGORIA_INDICE
    return CATEGORIA_B3


def glifo_do_ativo(ticker: str) -> Optional[str]:
    """Return the icon glyph key for a ticker (``None`` = universal fallback)."""
    t = _normalizar(ticker)
    categoria = categoria_do_ativo(t)

    if categoria == CATEGORIA_CRIPTO:
        return CRIPTOMOEDAS.get(t)
    if categoria == CATEGORIA_FOREX:
        return FOREX.get(t, "usd")
    if categoria == CATEGORIA_COMMODITY:
        return COMMODITIES.get(t)
    if categoria == CATEGORIA_INDICE:
        return INDICES.get(t, "indexChart")

    setor = setor_do_ativo(t)
    return {
        SETOR_BANCO: "bank",
        SETOR_ENERGIA: "energy",
        SETOR_MINERACAO: "mining",
        SETOR_VAREJO: "retail",
        SETOR_SAUDE: "health",
    }.get(setor)


def simbolo_ativo(ticker: str, categoria: Optional[str] = None) -> str:
    """Retorna o simbolo miniatura do ativo para o emblema da UI.

    Cripto/BTC exibe o glifo "₿"; acoes da B3 exibem as duas primeiras
    letras do ticker; o restante exibe o simbolo monetario minimalista "$".
    """
    cat = categoria or categoria_do_ativo(ticker)
    t = _normalizar(ticker)
    if cat == CATEGORIA_CRIPTO or "BTC" in t:
        return "\u20bf"
    if cat == CATEGORIA_B3:
        return t[:2]
    return "$"


def descricao_icone(ticker: str) -> Dict[str, Any]:
    """Return the icon metadata published with every asset payload."""
    t = _normalizar(ticker)
    return {
        "categoria": categoria_do_ativo(t),
        "setor": setor_do_ativo(t),
        "glifo": glifo_do_ativo(t),
    }
