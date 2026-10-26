"""Tests for the trading mode registry (Swing Trade / Day Trade).

``aguia/modes.py`` is the single source of truth: the API, the market data
provider and the rationale generator all read from it. The front-end keeps a
mirror of the same registry in ``static/script.js`` (``MODES``) so the mode bar
can render before the first API response arrives. These tests assert that the
two representations never drift apart and that the mode bar is wired to the
backend contract.
"""

import ast
import re
from pathlib import Path

import pytest

from aguia.modes import (
    ATIVOS_DAY,
    INTERVALOS_DAY,
    MODO_PADRAO,
    MODOS,
    catalogo_modos,
    get_modo,
    normalizar_intervalo,
    normalizar_modo,
    periodo_yahoo,
    rotulo_ativo,
    simbolo_yahoo,
    universo_do_modo,
)

ROOT_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT_DIR / "static"

# Keys that only exist on the front-end (pure presentation).
# `tickers` is also frontend-only: the backend populates it dynamically from
# aguia.config.load_universe() via catalogo_modos(), while the front-end keeps
# a static mirror for rendering before the first API response arrives.
FRONTEND_ONLY_KEYS = {"hint", "rotulo_projecao", "placeholder_busca", "tickers"}

# Keys that exist on the backend but are irrelevant to the front-end.
BACKEND_ONLY_KEYS = {"mercado", "periodo_yahoo", "universo"}


@pytest.fixture(scope="module")
def script_js() -> str:
    return (STATIC_DIR / "script.js").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def index_html() -> str:
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def style_css() -> str:
    return (STATIC_DIR / "style.css").read_text(encoding="utf-8")


def _parse_js_value(raw: str):
    """Evaluate a JavaScript literal that is also a valid Python literal."""
    value = raw.strip().rstrip(",").strip()
    if value == "true":
        return True
    if value == "false":
        return False
    if value == "null":
        return None
    return ast.literal_eval(value)


def _parse_js_modes(source: str) -> dict:
    """Extract the ``MODES`` registry declared in script.js."""
    assert "const MODES = {" in source, "front-end MODES registry not found"

    start = source.index("const MODES = {") + len("const MODES = {")
    depth = 1
    index = start
    while index < len(source) and depth:
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
        index += 1

    # Apenas o corpo do objeto MODES: outros blocos JS do arquivo
    # (fabrica de icones, por exemplo) usam a mesma sintaxe.
    body = source[start : index - 1]
    modes = {}

    for match in re.finditer(r"\n    (\w+): \{\n(.*?)\n    \},", body, re.S):
        mode_id, raw = match.group(1), match.group(2)
        fields = {}
        for key, value in re.findall(r"^\s*(\w+): (.+?),?$", raw, re.M):
            fields[key] = _parse_js_value(value)
        modes[mode_id] = fields

    return modes


def _parse_js_list(source: str, name: str) -> list:
    """Extract a top-level ``const NAME = [...]`` array from script.js."""
    match = re.search(rf"const {name} = (\[.*?\]);", source, re.S)
    assert match is not None, f"{name} not found in script.js"
    return ast.literal_eval(match.group(1))


# --------------------------------------------------------------- backend registry
def test_default_mode_is_swing_trade():
    assert MODO_PADRAO == "swing"
    assert normalizar_modo(None) == "swing"
    assert normalizar_modo("") == "swing"
    assert normalizar_modo("desconhecido") == "swing"


def test_modes_are_normalised():
    assert normalizar_modo("DAY") == "day"
    assert normalizar_modo(" day ") == "day"
    assert normalizar_modo("Swing") == "swing"
    assert get_modo("day")["id"] == "day"
    assert get_modo("inexistente")["id"] == "swing"


def test_interval_is_validated_per_mode():
    assert normalizar_intervalo("swing", "5m") == "1d"
    assert normalizar_intervalo("day", "15m") == "15m"
    assert normalizar_intervalo("day", "1h") == "1h"
    assert normalizar_intervalo("day", "4h") == "5m"
    assert normalizar_intervalo("day", None) == "5m"


def test_yahoo_window_follows_the_interval():
    assert periodo_yahoo("swing", "1d") == "2y"
    assert periodo_yahoo("day", "5m") == "5d"
    assert periodo_yahoo("day", "15m") == "15d"
    assert periodo_yahoo("day", "1h") == "60d"


def test_symbol_resolution_per_market():
    assert simbolo_yahoo("PETR4", "b3") == "PETR4.SA"
    assert simbolo_yahoo("GC=F", "global") == "GC=F"
    assert simbolo_yahoo("BTC-USD", "global") == "BTC-USD"


def test_day_universe_uses_global_assets():
    assert universo_do_modo("day") == ATIVOS_DAY
    assert "SPY" in ATIVOS_DAY
    assert rotulo_ativo("SPY", "day") == "S&P 500"
    assert rotulo_ativo("PETR4", "swing") == "PETR4"


def test_catalogue_is_consumable_by_the_front_end():
    catalogo = catalogo_modos()

    assert catalogo["padrao"] == MODO_PADRAO
    assert catalogo["intervalos_day"] == INTERVALOS_DAY
    assert set(catalogo["modes"]) == set(MODOS)

    for modo_id, definicao in catalogo["modes"].items():
        assert definicao["id"] == modo_id
        assert definicao["contexto"]
        assert definicao["moeda"]
        assert definicao["universo"]
        assert definicao["tickers"]


# ------------------------------------------------------------- front-end mirror
def test_frontend_mirror_declares_every_mode(script_js: str):
    modos = _parse_js_modes(script_js)
    assert set(modos) == set(MODOS)


@pytest.mark.parametrize("modo_id", sorted(MODOS))
def test_frontend_mirror_matches_the_backend(modo_id, script_js: str):
    modos = _parse_js_modes(script_js)
    backend = MODOS[modo_id]
    frontend = modos[modo_id]

    shared = (set(backend) & set(frontend)) - BACKEND_ONLY_KEYS
    for key in shared:
        assert frontend[key] == backend[key], f"{modo_id}.{key} divergiu do backend"

    # Every shared contract key must exist on the front-end as well.
    for key in set(backend) - BACKEND_ONLY_KEYS:
        assert key in frontend, f"chave ausente no front-end: {modo_id}.{key}"

    # Only known presentation-only keys may exist exclusively on the front-end.
    extras = set(frontend) - set(backend)
    assert extras <= FRONTEND_ONLY_KEYS, f"chaves inesperadas no front-end: {sorted(extras)}"


def test_frontend_intervals_match_the_backend(script_js: str):
    assert _parse_js_list(script_js, "INTERVALOS_DAY") == INTERVALOS_DAY


def test_frontend_requests_the_mode_to_the_api(script_js: str):
    """The dashboard must ask the backend for the active mode and interval."""
    assert "/api/dados?" in script_js
    assert "modo: modoRequisicao" in script_js
    assert "intervalo: intervaloRequisicao" in script_js
    assert "const modoRequisicao = currentMode;" in script_js
    assert "/api/acoes?modo=" in script_js


def test_cache_key_isolates_mode_and_interval(script_js: str):
    """The same ticker in two modes must not share a cache entry."""
    match = re.search(r"function cacheKey\(ticker\)\s*\{(.*?)\n\}", script_js, re.S)
    assert match is not None, "cacheKey not found in script.js"
    body = match.group(1)
    assert "currentMode" in body
    assert "currentInterval" in body


def test_fallback_universes_come_from_immutable_lists(script_js: str):
    """The fallback of a mode must never be cloned from the current universe.

    Otherwise a switch back to Swing Trade would keep the intraday tickers.
    """
    assert "const ASSETS_FALLBACK_B3 = [" in script_js
    assert "const ASSETS_FALLBACK_DAY = [" in script_js

    match = re.search(r"function fallbackUniverso\(modoId\)\s*\{(.*?)\n\}", script_js, re.S)
    assert match is not None, "fallbackUniverso not found in script.js"
    body = match.group(1)
    assert "ASSETS_FALLBACK_B3" in body
    assert "ASSETS_FALLBACK_DAY" in body
    assert "ASSETS_UNIVERSE_DAY" not in script_js

    init = re.search(r"let ASSETS_UNIVERSE = (.+?);", script_js)
    assert init is not None
    assert "ASSETS_FALLBACK_B3" in init.group(1)


# ------------------------------------------------------------------- mode bar
def test_mode_bar_markup_exists(index_html: str):
    assert 'id="modeSwitch"' in index_html
    assert 'id="modeIntervals"' in index_html
    assert 'id="modeContextLabel"' in index_html
    assert 'data-mode="swing"' in index_html
    assert 'data-mode="day"' in index_html


def test_mode_bar_offers_every_intraday_interval(index_html: str):
    for intervalo in INTERVALOS_DAY:
        assert f'data-interval="{intervalo}"' in index_html


def test_metric_labels_are_mode_aware(index_html: str):
    for element_id in ("metricTargetLabel", "metricStopLabel", "metricPayoffLabel"):
        assert f'id="{element_id}"' in index_html


def test_mode_context_labels_are_defined(script_js: str):
    modos = _parse_js_modes(script_js)
    for modo_id, definicao in modos.items():
        assert definicao["contexto"]
        assert definicao["rotulo_alvo"]
        assert definicao["rotulo_stop"]
        assert definicao["rotulo_payoff"]
        assert definicao["moeda"] in ("R$", "US$")
        assert definicao["horizonte"] > 0


# ------------------------------------------------------------------- theme
def test_theme_toggle_is_wired(index_html: str, script_js: str):
    assert 'id="themeToggle"' in index_html
    assert "aplicarTema" in script_js
    assert "aguia-tema" in script_js
    assert 'data-theme' in script_js


def test_light_theme_is_token_driven(style_css: str):
    assert ':root[data-theme="light"]' in style_css
    assert "--hairline" in style_css
    assert "--text-on-surface" in style_css
