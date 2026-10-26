"""Contract tests for the reusable ``logo-hero`` component.

The component overlays neon/electric layers (CSS + inline SVG) on top of the
brand logo. These tests guard four things:

1. the splash and the canonical fragment never drift apart;
2. every animation is restricted to compositor friendly properties;
3. the component stays isolated from the rest of the page;
4. the colours used come from the brand palette.

They are static contract checks: they read the shipped assets, they never
render a browser.
"""

import re
from pathlib import Path

import pytest

from aguia.brand import load_brand_palette

ROOT_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT_DIR / "static"
COMPONENTS_DIR = STATIC_DIR / "components"

CSS_PATH = COMPONENTS_DIR / "logo-hero.css"
FRAGMENT_PATH = COMPONENTS_DIR / "logo-hero.fragment.html"
PREVIEW_PATH = COMPONENTS_DIR / "logo-hero.html"

# Properties that can be animated without triggering layout or paint.
ALLOWED_ANIMATED_PROPERTIES = {"opacity", "transform", "stroke-dashoffset"}

# Properties that must never appear inside a ``@keyframes`` block.
FORBIDDEN_KEYFRAME_PROPERTIES = {
    "filter",
    "box-shadow",
    "width",
    "height",
    "top",
    "left",
    "right",
    "bottom",
    "margin",
    "padding",
    "background",
    "d",
    "r",
    "cx",
    "cy",
}


@pytest.fixture(scope="module")
def component_css() -> str:
    return CSS_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def fragment_html() -> str:
    return FRAGMENT_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def preview_html() -> str:
    return PREVIEW_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def index_html() -> str:
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def palette() -> dict:
    return load_brand_palette()


def _extract_element(html: str, tag: str, class_name: str) -> str:
    """Return the markup of ``<tag class="class_name">`` and its subtree."""
    marker = f'<{tag} class="{class_name}"'
    start = html.index(marker)
    depth = 0
    index = start
    while index < len(html):
        if html.startswith(f"<{tag}", index) and (
            index == 0 or not (html[index - 1].isalnum() or html[index - 1] in "-_")
        ):
            depth += 1
        elif html.startswith(f"</{tag}>", index):
            depth -= 1
            if depth == 0:
                return html[start : index + len(f"</{tag}>")]
        index += 1
    raise AssertionError(f"unterminated <{tag} class=\"{class_name}\"> block")


def _normalize(markup: str) -> str:
    """Normalise markup so two copies can be compared literally."""
    text = re.sub(r"<!--.*?-->", "", markup, flags=re.S)
    text = re.sub(r"\s+", " ", text).strip()
    # Strip presentation attributes that the splash legitimately adds for
    # accessibility (id, role, aria-*) but the canonical fragment omits.
    text = re.sub(r'\s(?:id|role|aria-[a-z]+)="[^"]*"', "", text)
    text = text.replace(
        'class="logo-hero__base splash-logo-img"', 'class="logo-hero__base"'
    )
    return text


def _keyframes(css: str) -> dict:
    """Map keyframe name -> body, with nested braces handled."""
    blocks = {}
    for match in re.finditer(r"@keyframes\s+([A-Za-z0-9_-]+)\s*\{", css):
        depth = 1
        index = match.end()
        while index < len(css) and depth:
            if css[index] == "{":
                depth += 1
            elif css[index] == "}":
                depth -= 1
            index += 1
        blocks[match.group(1)] = css[match.end() : index - 1]
    return blocks


def _css_block(css: str, selector: str) -> str:
    """Return the declaration block of the first rule with ``selector``."""
    match = re.search(re.escape(selector) + r"\s*\{", css)
    assert match is not None, f"selector not found: {selector}"
    depth = 1
    index = match.end()
    while index < len(css) and depth:
        if css[index] == "{":
            depth += 1
        elif css[index] == "}":
            depth -= 1
        index += 1
    return css[match.end() : index - 1]


def test_component_assets_exist():
    assert CSS_PATH.is_file()
    assert FRAGMENT_PATH.is_file()
    assert PREVIEW_PATH.is_file()


def test_splash_embeds_the_canonical_markup(index_html: str, fragment_html: str):
    """The splash copy and the canonical fragment must be identical."""
    splash = _extract_element(index_html, "div", "logo-hero")
    fragment = _extract_element(fragment_html, "div", "logo-hero")
    assert _normalize(splash) == _normalize(fragment)


def test_splash_links_the_component_stylesheet(index_html: str):
    assert 'href="components/logo-hero.css' in index_html


def test_preview_page_is_self_contained(preview_html: str):
    assert 'href="logo-hero.css"' in preview_html
    assert "logo-hero.fragment.html" in preview_html
    # The preview must not depend on the dashboard stylesheet.
    assert 'href="../style.css"' not in preview_html
    assert 'href="style.css"' not in preview_html


def test_component_has_no_external_assets(component_css: str, fragment_html: str):
    """No CDN, no remote font, no third party script."""
    for asset in (component_css, fragment_html):
        assert re.search(r'(?:src|href)\s*=\s*["\']https?://', asset) is None
        assert "url(http" not in asset


def test_component_layers_are_stacked_in_order(component_css: str):
    """base (1) -> aura (2) -> fx overlay (3)."""
    base = _css_block(component_css, ".logo-hero__base")
    aura = _css_block(component_css, ".logo-hero__aura")
    fx = _css_block(component_css, ".logo-hero__fx")
    assert "z-index: 1" in base
    assert "z-index: 2" in aura
    assert "z-index: 3" in fx


def test_component_isolates_its_own_paint(component_css: str):
    root = _css_block(component_css, ".logo-hero")
    assert "isolation: isolate" in root
    assert "contain: layout style" in root


def test_only_compositor_properties_are_animated(component_css: str):
    for name, body in _keyframes(component_css).items():
        properties = set(re.findall(r"([a-z-]+)\s*:", body))
        forbidden = properties & FORBIDDEN_KEYFRAME_PROPERTIES
        assert forbidden == set(), f"{name} animates forbidden properties: {forbidden}"
        unexpected = properties - ALLOWED_ANIMATED_PROPERTIES
        assert unexpected == set(), f"{name} animates unexpected properties: {unexpected}"


def test_filters_are_static(component_css: str):
    """Filters must never be animated: that would re-rasterize every frame."""
    for name, body in _keyframes(component_css).items():
        assert "filter" not in body, name
    # The glow that follows the moving arc is drawn with a duplicated stroke.
    assert ".logo-hero__ring-glow" in component_css
    assert ".logo-hero__ring-arc" in component_css


def test_animated_layers_promote_themselves(component_css: str):
    """Only compositable properties are promoted to their own layer."""
    for selector in (
        ".logo-hero__aura",
        ".logo-hero__ring-travel",
        ".logo-hero__eye",
        ".logo-hero__candle",
        ".logo-hero__spark",
    ):
        block = _css_block(component_css, selector)
        assert "will-change" in block, selector

    # stroke-dashoffset is not compositable: promoting it would waste memory.
    circuits = _css_block(component_css, ".logo-hero__circuit-track")
    assert "will-change" not in circuits
    assert "stroke-dasharray" in circuits


def test_reduced_motion_disables_the_effects(component_css: str):
    match = re.search(r"@media \(prefers-reduced-motion: reduce\) \{(.*)\Z", component_css, re.S)
    assert match is not None
    block = match.group(1)
    assert "animation: none" in block
    for selector in (
        ".logo-hero__aura",
        ".logo-hero__ring-travel",
        ".logo-hero__circuit-track",
        ".logo-hero__eye",
        ".logo-hero__candle",
        ".logo-hero__spark",
    ):
        assert selector in block, selector


def test_svg_geometry_matches_the_artwork(fragment_html: str):
    """Ring and eye coordinates were measured on the real 256x256 artwork."""
    assert 'cx="126" cy="117" r="91"' in fragment_html
    assert 'cx="150" cy="62"' in fragment_html
    assert 'viewBox="0 0 256 256"' in fragment_html
    assert fragment_html.count('pathLength="360"') == 3


def test_circuits_are_defined_once_and_reused(fragment_html: str):
    """``<use>`` keeps the glow stroke and the core stroke in sync."""
    for index in (1, 2, 3):
        path_id = f'id="aguia-hero-circuit-{index}"'
        assert path_id in fragment_html
        assert fragment_html.count(f'href="#aguia-hero-circuit-{index}"') == 2


def test_component_uses_only_palette_colours(component_css: str, fragment_html: str, palette: dict):
    known = set()
    for group, values in palette.items():
        if isinstance(values, dict):
            for value in values.values():
                for hex_value in re.findall(r"#[0-9A-Fa-f]{6}\b", value):
                    known.add(hex_value.upper())

    for asset in (component_css, fragment_html):
        used = {value.upper() for value in re.findall(r"#[0-9A-Fa-f]{6}\b", asset)}
        unknown = used - known
        assert unknown == set(), f"colours outside the palette: {sorted(unknown)}"


def test_component_tokens_are_customizable(component_css: str):
    root = _css_block(component_css, ".logo-hero")
    for token in (
        "--hero-size",
        "--hero-radius",
        "--hero-glow",
        "--hero-neon-cyan",
        "--hero-neon-blue",
        "--hero-neon-green",
    ):
        assert f"{token}:" in root, token


def test_no_dead_keyframes_or_tokens(component_css: str):
    """Every declared animation and every token must actually be used."""
    keyframes = set(_keyframes(component_css))
    referenced = set()
    for declaration in re.findall(r"animation:\s*([^;]+);", component_css):
        for item in declaration.split(","):
            referenced.add(item.strip().split()[0])
    assert keyframes <= referenced, f"unused keyframes: {sorted(keyframes - referenced)}"

    tokens = set(re.findall(r"(--hero-[a-z-]+)\s*:", component_css))
    body = re.sub(r"--hero-[a-z-]+\s*:", "", component_css)
    unused = {token for token in tokens if token not in body}
    assert unused == set(), f"unused custom properties: {sorted(unused)}"


def test_every_component_class_is_styled(component_css: str, fragment_html: str):
    """No orphan selectors and no unstyled hooks: markup and CSS agree."""
    markup_classes = set()
    for match in re.finditer(r'class="([^"]+)"', fragment_html):
        markup_classes.update(match.group(1).split())

    css_classes = set(re.findall(r"\.((?:logo-hero)[\w-]*)", component_css))

    assert css_classes - markup_classes == set(), "selectors without markup"
    assert markup_classes - css_classes == set(), "markup without styles"


def test_splash_keeps_the_brand_logo_sources(index_html: str):
    """The splash must still load the real logo assets."""
    assert 'src="logo.png"' in index_html
    assert 'srcset="logo.webp"' in index_html
    assert 'class="logo-hero__base splash-logo-img"' in index_html
