"""Tests for the brand design system.

The palette lives in ``config/brand_palette.json`` and is mirrored by the
``:root`` block of ``static/style.css``, the SVG emblem in
``static/index.html`` and the Python chart exporter. These tests assert
that the four representations never drift apart, and that no hardcoded
colour survives outside the token definitions.
"""

import json
import re
from pathlib import Path

import pytest

from aguia.brand import brand_color, brand_group, load_brand_palette

ROOT_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT_DIR / "static"
PALETTE_PATH = ROOT_DIR / "config" / "brand_palette.json"

# JSON path -> CSS custom property name
CSS_TOKEN_MAP = {
    ("surfaces", "bgMain"): "--bg-main",
    ("surfaces", "bgSurface"): "--bg-surface",
    ("surfaces", "bgCard"): "--bg-card",
    ("surfaces", "bgElevated"): "--bg-elevated",
    ("surfaces", "bgInset"): "--bg-inset",
    ("surfaces", "bgPanel"): "--bg-panel",
    ("surfaces", "bgDeep"): "--bg-deep",
    ("surfaces", "gridLine"): "--grid-line",
    ("borders", "borderSubtle"): "--border-subtle",
    ("borders", "borderCard"): "--border-card",
    ("borders", "borderStrong"): "--border-strong",
    ("borders", "borderMuted"): "--border-muted",
    ("borders", "borderActive"): "--border-active",
    ("brand", "blue"): "--brand-blue",
    ("brand", "blueDeep"): "--brand-blue-deep",
    ("brand", "cyan"): "--brand-cyan",
    ("brand", "cyanSoft"): "--brand-cyan-soft",
    ("brand", "teal"): "--brand-teal",
    ("brand", "tealDeep"): "--brand-teal-deep",
    ("brand", "navy"): "--brand-navy",
    ("brand", "ink"): "--brand-ink",
    ("semantic", "green"): "--color-green",
    ("semantic", "greenLight"): "--color-green-light",
    ("semantic", "greenBg"): "--color-green-bg",
    ("semantic", "greenBorder"): "--color-green-border",
    ("semantic", "red"): "--color-red",
    ("semantic", "redLight"): "--color-red-light",
    ("semantic", "redBg"): "--color-red-bg",
    ("semantic", "redBorder"): "--color-red-border",
    ("semantic", "yellow"): "--color-yellow",
    ("semantic", "blue"): "--color-blue",
    ("semantic", "blueLight"): "--color-blue-light",
    ("semantic", "blueDeep"): "--color-blue-deep",
    ("semantic", "cyan"): "--color-cyan",
    ("semantic", "white"): "--color-white",
    ("text", "primary"): "--text-primary",
    ("text", "secondary"): "--text-secondary",
    ("text", "muted"): "--text-muted",
    ("text", "dim"): "--text-dim",
    ("text", "bright"): "--text-bright",
    ("icons", "cyan"): "--icon-cyan",
    ("icons", "green"): "--icon-green",
    ("icons", "gold"): "--icon-gold",
    ("icons", "orange"): "--icon-orange",
    ("icons", "purple"): "--icon-purple",
    ("icons", "silver"): "--icon-silver",
    ("icons", "fallbackBg"): "--icon-fallback-bg",
}


@pytest.fixture(scope="module")
def palette() -> dict:
    return load_brand_palette()


@pytest.fixture(scope="module")
def style_css() -> str:
    return (STATIC_DIR / "style.css").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def index_html() -> str:
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


def _css_root_block(style_css: str) -> str:
    start = style_css.index(":root {")
    end = style_css.index("\n}", start)
    return style_css[start:end]


def _css_token_map(root_block: str) -> dict:
    return {
        match.group(1): match.group(2).strip()
        for match in re.finditer(r"(--[a-z0-9-]+)\s*:\s*([^;]+);", root_block)
    }


def _resolve_token(tokens: dict, name: str, seen=None) -> str:
    """Resolve a custom property, following var() aliases."""
    seen = seen or set()
    if name in seen:
        raise AssertionError(f"circular CSS token reference: {name}")
    seen.add(name)

    value = tokens[name]
    match = re.fullmatch(r"var\(\s*(--[a-z0-9-]+)\s*\)", value)
    if match:
        return _resolve_token(tokens, match.group(1), seen)
    return value


def _css_token_value(tokens: dict, token: str) -> str:
    assert token in tokens, f"CSS token not found: {token}"
    return _resolve_token(tokens, token)


def test_palette_file_is_valid_json(palette: dict):
    assert "brand" in palette
    assert "semantic" in palette
    assert "chart" in palette


def test_brand_module_reads_the_same_file(palette: dict):
    assert brand_color("brand", "blue") == palette["brand"]["blue"]
    assert brand_group("chart")["up"] == palette["chart"]["up"]
    with pytest.raises(KeyError):
        brand_color("brand", "does-not-exist")


@pytest.mark.parametrize("json_path,css_token", sorted(CSS_TOKEN_MAP.items()))
def test_css_tokens_match_the_palette(json_path, css_token, palette, style_css):
    group, key = json_path
    expected = palette[group][key]
    tokens = _css_token_map(_css_root_block(style_css))
    actual = _css_token_value(tokens, css_token)
    assert actual.lower() == expected.lower(), f"{css_token}: css={actual} json={expected}"


def test_css_tokens_have_no_circular_references(style_css):
    tokens = _css_token_map(_css_root_block(style_css))
    for name in tokens:
        _resolve_token(tokens, name)


def test_no_hardcoded_colours_outside_the_token_block(style_css):
    """Every colour in the stylesheet must come from a design token."""
    root = _css_root_block(style_css)
    body = style_css.replace(root, "")
    leftovers = re.findall(r"#[0-9A-Fa-f]{3,8}\b", body)
    assert leftovers == [], f"hardcoded colours outside :root: {sorted(set(leftovers))}"
    leftovers_rgba = re.findall(r"rgba\([^)]*\)", body)
    assert leftovers_rgba == [], f"hardcoded rgba outside :root: {sorted(set(leftovers_rgba))}"


def test_no_hardcoded_colours_in_javascript():
    source = (STATIC_DIR / "script.js").read_text(encoding="utf-8")
    # The only literals allowed are the alpha helper templates.
    literals = re.findall(r"#[0-9A-Fa-f]{3,8}\b", source)
    assert literals == [], f"hardcoded colours in script.js: {sorted(set(literals))}"


def test_javascript_reads_palette_from_css():
    source = (STATIC_DIR / "script.js").read_text(encoding="utf-8")
    assert "getComputedStyle(document.documentElement)" in source
    assert "--color-green" in source
    assert "--color-red" in source
    assert "--brand-blue" in source


def test_svg_emblem_only_uses_palette_colours(index_html, palette):
    """Every colour of the emblem must exist in the brand palette."""
    start = index_html.index('<svg class="svg-sprite"')
    sprite = index_html[start:index_html.index("</svg>", start)]
    used = set(re.findall(r"#[0-9A-Fa-f]{6}\b", sprite))

    known = set()
    for group, values in palette.items():
        if isinstance(values, dict):
            for value in values.values():
                for hex_value in re.findall(r"#[0-9A-Fa-f]{6}\b", value):
                    known.add(hex_value.upper())

    unknown = {c.upper() for c in used} - known
    assert unknown == set(), f"emblem uses colours outside the palette: {sorted(unknown)}"


def test_chart_palette_is_brand_aligned(palette):
    chart = palette["chart"]
    assert chart["up"] == palette["semantic"]["green"]
    assert chart["down"] == palette["semantic"]["red"]
    assert chart["sma200"] == palette["semantic"]["blue"]


def test_chart_export_reads_the_palette():
    source = (ROOT_DIR / "aguia" / "charts" / "png_export.py").read_text(encoding="utf-8")
    assert "brand_group" in source
    assert "from aguia.brand import" in source
    leftovers = re.findall(r"#[0-9A-Fa-f]{6}\b", source)
    assert leftovers == [], f"hardcoded colours in png_export.py: {sorted(set(leftovers))}"


def test_palette_json_is_tracked_in_config():
    assert PALETTE_PATH.is_file()
    data = json.loads(PALETTE_PATH.read_text(encoding="utf-8"))
    assert data["version"]
