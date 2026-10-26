"""Contract tests for the Cyber/Neon icon factory and the chart interactivity.

The icon factory is split in two halves that must never drift apart:
``aguia/icons.py`` classifies the ticker (categoria + setor) and the
front-end (``static/script.js``) maps the same tickers to vector glyphs.
These tests assert that both sides agree, that the palette comes from
the design tokens, and that the chart exposes crosshair + tooltip.
"""

import ast
import re
from pathlib import Path

import pytest

from aguia.icons import (
    CATEGORIA_B3,
    CATEGORIA_COMMODITY,
    CATEGORIA_CRIPTO,
    CATEGORIA_FOREX,
    CATEGORIA_INDICE,
    CATEGORIAS,
    COMMODITIES,
    CRIPTOMOEDAS,
    FOREX,
    INDICES,
    SETORES_B3,
    categoria_do_ativo,
    descricao_icone,
    glifo_do_ativo,
    setor_do_ativo,
)

ROOT_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT_DIR / "static"


@pytest.fixture(scope="module")
def script_js() -> str:
    return (STATIC_DIR / "script.js").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def index_html() -> str:
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def style_css() -> str:
    return (STATIC_DIR / "style.css").read_text(encoding="utf-8")


def _js_map(source: str, name: str) -> dict:
    """Extract a flat ``const NAME = { "KEY": "value" }`` map from script.js."""
    match = re.search(rf"const {name} = \{{(.*?)\n\}};", source, re.S)
    assert match is not None, f"{name} not found in script.js"
    return {
        key: value
        for key, value in re.findall(r'"([^"]+)":\s*"([^"]+)"', match.group(1))
    }


def _js_sector_map(source: str) -> dict:
    """Extract the ``ICON_B3_SECTORS`` list of ``{ glyph, tickers }`` entries."""
    match = re.search(r"const ICON_B3_SECTORS = \[(.*?)\n\];", source, re.S)
    assert match is not None, "ICON_B3_SECTORS not found in script.js"
    body = match.group(1)
    sectors = {}
    for entry in re.finditer(r'\{\s*glyph:\s*"([^"]+)",\s*tickers:\s*\[(.*?)\]\s*\}', body, re.S):
        glyph, tickers = entry.group(1), entry.group(2)
        tickers = re.findall(r'"([^"]+)"', tickers)
        for ticker in tickers:
            sectors[ticker] = glyph
    return sectors


# --------------------------------------------------------------- backend rules
def test_categories_are_stable():
    assert CATEGORIAS == (
        CATEGORIA_CRIPTO,
        CATEGORIA_FOREX,
        CATEGORIA_COMMODITY,
        CATEGORIA_INDICE,
        CATEGORIA_B3,
    )


@pytest.mark.parametrize(
    "ticker,expected",
    [
        ("BTC-USD", CATEGORIA_CRIPTO),
        ("ETH-USD", CATEGORIA_CRIPTO),
        ("SOL-USD", CATEGORIA_CRIPTO),
        ("USDT-USD", CATEGORIA_CRIPTO),
        ("USDC-USD", CATEGORIA_CRIPTO),
        ("BNB-USD", CATEGORIA_CRIPTO),
        ("XRP-USD", CATEGORIA_CRIPTO),
        ("ADA-USD", CATEGORIA_CRIPTO),
        ("DOGE-USD", CATEGORIA_CRIPTO),
        ("AVAX-USD", CATEGORIA_CRIPTO),
        ("USDBRL=X", CATEGORIA_FOREX),
        ("EURUSD=X", CATEGORIA_FOREX),
        ("GBPUSD=X", CATEGORIA_FOREX),
        ("DXY", CATEGORIA_FOREX),
        ("GC=F", CATEGORIA_COMMODITY),
        ("XAUUSD=X", CATEGORIA_COMMODITY),
        ("SI=F", CATEGORIA_COMMODITY),
        ("HG=F", CATEGORIA_COMMODITY),
        ("CL=F", CATEGORIA_COMMODITY),
        ("BZ=F", CATEGORIA_COMMODITY),
        ("ZC=F", CATEGORIA_COMMODITY),
        ("ZS=F", CATEGORIA_COMMODITY),
        ("^GSPC", CATEGORIA_INDICE),
        ("SPY", CATEGORIA_INDICE),
        ("^DJI", CATEGORIA_INDICE),
        ("DIA", CATEGORIA_INDICE),
        ("^IXIC", CATEGORIA_INDICE),
        ("QQQ", CATEGORIA_INDICE),
        ("^BVSP", CATEGORIA_INDICE),
        ("PETR4", CATEGORIA_B3),
        ("VALE3", CATEGORIA_B3),
        ("ITUB4", CATEGORIA_B3),
    ],
)
def test_ticker_classification(ticker, expected):
    assert categoria_do_ativo(ticker) == expected


def test_b3_sectors_are_recognised():
    assert setor_do_ativo("ITUB4") == "banco"
    assert setor_do_ativo("PETR4") == "energia"
    assert setor_do_ativo("VALE3") == "mineracao"
    assert setor_do_ativo("MGLU3") == "varejo"
    assert setor_do_ativo("RDOR3") == "saude"
    assert setor_do_ativo("WEGE3") is None


def test_description_payload_shape():
    info = descricao_icone("PETR4")
    assert info["categoria"] == CATEGORIA_B3
    assert info["setor"] == "energia"
    assert info["glifo"] == "energy"
    assert descricao_icone("WEGE3")["glifo"] is None


# ------------------------------------------------------------ front-end parity
def test_frontend_crypto_map_matches(script_js: str):
    assert _js_map(script_js, "ICON_CRYPTO_MAP") == CRIPTOMOEDAS


def test_frontend_forex_map_matches(script_js: str):
    assert _js_map(script_js, "ICON_FOREX_MAP") == FOREX


def test_frontend_commodity_map_matches(script_js: str):
    assert _js_map(script_js, "ICON_COMMODITY_MAP") == COMMODITIES


def test_frontend_index_map_matches(script_js: str):
    assert _js_map(script_js, "ICON_INDEX_MAP") == INDICES


def test_frontend_b3_sectors_match(script_js: str):
    """Every B3 ticker of the backend sectors must exist on the front-end."""
    frontend = _js_sector_map(script_js)
    backend = {}
    for setor, tickers in SETORES_B3.items():
        for ticker in tickers:
            backend[ticker] = setor

    assert set(frontend) == set(backend)

    glyph_por_setor = {
        "banco": "bank",
        "energia": "energy",
        "mineracao": "mining",
        "varejo": "retail",
        "saude": "health",
    }
    for ticker, setor in backend.items():
        assert frontend[ticker] == glyph_por_setor[setor], ticker


def test_icon_factory_is_exported(script_js: str):
    assert "function getAssetIconSVG(ticker, categoria)" in script_js
    assert "function detectarCategoriaIcone(ticker)" in script_js
    assert "function fallbackIconSVG(ticker)" in script_js


def test_icon_svg_is_22px_and_decorative(script_js: str):
    assert 'viewBox="0 0 22 22"' in script_js
    assert 'width="22"' in script_js
    assert 'height="22"' in script_js
    assert 'class="asset-icon"' in script_js
    assert 'aria-hidden="true"' in script_js


def test_every_mapped_glyph_exists_in_the_glyph_library(script_js: str):
    """A ticker must never point to a glyph that was not drawn."""
    glyphs = set(re.findall(r"^    ([a-zA-Z][a-zA-Z0-9]*): \{$", script_js, re.M))
    assert glyphs, "glifos nao encontrados"

    mapped = set()
    for name in ("ICON_CRYPTO_MAP", "ICON_FOREX_MAP", "ICON_COMMODITY_MAP", "ICON_INDEX_MAP"):
        mapped |= set(_js_map(script_js, name).values())
    mapped |= set(_js_sector_map(script_js).values())

    assert mapped <= glyphs, sorted(mapped - glyphs)


def test_every_glyph_colour_is_a_declared_token(script_js: str, style_css: str):
    """Glyph colours must resolve to a token that the stylesheet declares."""
    declared = set(re.findall(r"(--icon-[a-z-]+)\s*:", style_css))
    used = set(re.findall(r"var\((--icon-[a-z-]+)\)", script_js))
    assert used, "nenhum token de icone usado"
    assert used <= declared, sorted(used - declared)


def test_light_theme_has_readable_icon_variants(style_css: str):
    """No neon puro sobrevive sobre fundo branco."""
    light = re.search(r":root\[data-theme=\"light\"\] \{(.*?)\n\}", style_css, re.S).group(1)
    for token in ("--icon-cyan", "--icon-green", "--icon-gold", "--icon-purple"):
        assert token in light, token
    assert "--lt-icon-cyan" in style_css


def test_fallback_uses_two_letters_in_mono(script_js: str):
    assert "JetBrains Mono" in script_js
    assert "var(--icon-fallback-bg)" in script_js
    assert "var(--icon-cyan)" in script_js


def test_icons_use_tokens_not_literal_colours(script_js: str):
    """The icon palette must come from the CSS tokens, never from literals."""
    for token in (
        "var(--icon-cyan)",
        "var(--icon-green)",
        "var(--icon-gold)",
        "var(--icon-orange)",
        "var(--icon-purple)",
        "var(--icon-silver)",
    ):
        assert token in script_js, token


def test_icons_are_used_in_the_sidebar_and_title(script_js: str):
    assert "getAssetIconSVG(asset.ticker, asset.categoria)" in script_js
    assert "getAssetIconSVG(ticker, categoria)" in script_js
    assert 'id="chartHeadlineIcon"' in script_js or "chartHeadlineIcon" in script_js


def test_neon_glow_token(style_css: str):
    assert "--icon-glow: 0 0 5px rgba(0, 240, 255, 0.4);" in style_css
    assert "filter: drop-shadow(var(--icon-glow));" in style_css
    assert ".asset-icon" in style_css


# --------------------------------------------------------- chart interactivity
def test_crosshair_and_tooltip_are_implemented(script_js: str):
    assert "function drawCrosshair(g)" in script_js
    assert "function updateChartTooltip(index, g, cursorX, cursorY)" in script_js
    assert "function onChartPointerMove(event)" in script_js
    assert "function onChartPointerLeave()" in script_js
    assert "pointermove" in script_js
    assert "pointerleave" in script_js


def test_tooltip_markup_contains_ohlcv(index_html: str):
    assert 'id="chartTooltip"' in index_html
    for element_id in (
        "chartTooltipDate",
        "chartTooltipOpen",
        "chartTooltipHigh",
        "chartTooltipLow",
        "chartTooltipClose",
        "chartTooltipChange",
        "chartTooltipVolume",
    ):
        assert f'id="{element_id}"' in index_html, element_id


def test_tooltip_is_glassmorphism(style_css: str):
    assert ".chart-tooltip" in style_css
    block = re.search(r"\.chart-tooltip \{([^}]*)\}", style_css).group(1)
    assert "backdrop-filter: blur(" in block
    assert "position: absolute" in block


# ------------------------------------------------------------ header and tips
def test_status_text_is_server_online(index_html: str, script_js: str):
    assert "Servidor Online" in index_html
    assert 'connText.textContent = "Servidor Online";' in script_js


def test_theme_toggle_keeps_moon_and_sun(index_html: str):
    assert "🌙" in index_html
    assert "☀️" in index_html
    assert "aguia-tema" in index_html


def test_tips_card_has_no_disclaimer_inside(index_html: str):
    """The tips card is clean: the disclaimer lives outside of it."""
    card = index_html[index_html.index('id="reasoningPanel"') :]
    card = card[: card.index("</section>")]
    assert "compliance-disclaimer" not in card
    assert "Análise experimental" not in card


def test_compliance_line_still_on_the_page(index_html: str):
    """The pt-BR compliance notice remains visible, outside the tips card."""
    assert 'id="complianceDisclaimer"' in index_html
    assert "Não constitui recomendação de investimento" in index_html
    assert index_html.index('id="complianceDisclaimer"') > index_html.index('id="reasoningPanel"')


# ------------------------------------------------------------------ typography
def test_fonts_are_imported_with_the_expected_weights(index_html: str):
    match = re.search(r"fonts\.googleapis\.com/css2\?([^'\"]+)", index_html)
    assert match is not None
    query = match.group(1)
    assert "Inter:wght@400;500;600;700" in query
    assert "JetBrains+Mono:wght@500;700" in query


def test_global_font_is_inter(style_css: str):
    assert "--font-sans: 'Inter'" in style_css
    body = re.search(r"\nbody \{(.*?)\n\}", style_css, re.S).group(1)
    assert "font-family: var(--font-sans);" in body
    assert "button," in style_css and "font-family: inherit;" in style_css


def test_numeric_data_uses_mono(style_css: str):
    """Precos, variacoes e valores de card usam JetBrains Mono."""
    selectors = set()
    for match in re.finditer(r"([^{}]+)\{([^}]*)\}", style_css):
        if "font-family: var(--font-mono);" not in match.group(2):
            continue
        for selector in match.group(1).split(","):
            selector = " ".join(selector.split())
            if selector and not selector.startswith("/*"):
                selectors.add(selector)

    for required in (
        ".quant-card-val",
        ".quant-card-sub",
        ".stock-price",
        ".stock-return",
        ".target-floating-badge",
        ".chart-tooltip__value",
    ):
        assert required in selectors, required


def test_every_imported_weight_is_available(script_js: str):
    """No CSS may request a weight that the Google Fonts import lacks."""
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    css = (STATIC_DIR / "style.css").read_text(encoding="utf-8")

    inter = set(re.search(r"Inter:wght@([0-9;]+)", html).group(1).split(";"))
    mono = set(re.search(r"JetBrains\+Mono:wght@([0-9;]+)", html).group(1).split(";"))

    def _rule_families():
        for match in re.finditer(r"([^{}]+)\{([^}]*)\}", css):
            body = match.group(2)
            weight = re.search(r"font-weight:\s*(\d+)", body)
            if not weight:
                continue
            family = "mono" if "--font-mono" in body else "inter"
            yield family, weight.group(1)

    for family, weight in _rule_families():
        available = mono if family == "mono" else inter
        assert weight in available, f"peso {weight} indisponivel em {family}"


def test_module_is_importable():
    """The classification module must stay importable from the package."""
    module = ast.parse((ROOT_DIR / "aguia" / "icons.py").read_text(encoding="utf-8"))
    assert any(isinstance(node, ast.FunctionDef) for node in module.body)
