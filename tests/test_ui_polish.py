"""Contract tests for the "elite terminal" visual polish of the dashboard.

The refinements are pure CSS/JS: glassmorphism cards with gradient borders,
smooth transitions, a fluid fade between assets, a live status pulse, thin
scrollbars and tabular numerals. These tests lock the behaviour so a later
refactor cannot silently drop one of them.
"""

import re
from pathlib import Path

import pytest

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@pytest.fixture(scope="module")
def style_css() -> str:
    return (STATIC_DIR / "style.css").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def index_html() -> str:
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def script_js() -> str:
    return (STATIC_DIR / "script.js").read_text(encoding="utf-8")


def _block(css: str, selector: str) -> str:
    """Return the declaration block of the first rule matching ``selector``."""
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


# --------------------------------------------------------------- glassmorphism
def test_metric_cards_use_glassmorphism(style_css: str):
    block = _block(style_css, ".quant-card")
    assert "backdrop-filter: blur(" in block
    assert "saturate(" in block
    # Gradiente de preenchimento em padding-box + borda em border-box
    assert "padding-box" in block
    assert "border-box" in block
    assert "var(--glass-border) border-box" in block


def test_reasoning_card_uses_the_same_glass_treatment(style_css: str):
    block = _block(style_css, ".reasoning-card")
    assert "backdrop-filter: blur(" in block
    assert "var(--glass-border) border-box" in block


def test_hover_glow_is_cyan_and_token_driven(style_css: str):
    block = _block(style_css, ".quant-card:hover")
    assert "--glow-cyan-hover" in block
    # The token itself must be derived from the brand cyan, never hardcoded.
    token = _block(style_css, ":root")
    assert "--glow-cyan-hover: color-mix(in srgb, var(--brand-cyan) 15%, transparent);" in token


def test_cards_expose_a_top_light_on_hover(style_css: str):
    assert ".quant-card::before" in style_css
    assert ".reasoning-card::before" in style_css
    pseudo = _block(style_css, ".quant-card::before")
    assert "opacity: 0" in pseudo
    # The light must stay below the text (no repaint of the content).
    assert "z-index: -1" in pseudo


# ----------------------------------------------------------------- transitions
def test_sidebar_cards_have_smooth_transitions(style_css: str):
    block = _block(style_css, ".stock-card-item")
    assert "transition: all 0.25s ease-in-out;" in block


def test_filter_buttons_have_smooth_transitions(style_css: str):
    block = _block(style_css, ".filter-pill")
    assert "transition: all 0.25s ease-in-out;" in block


def test_selected_card_keeps_a_stable_border_width(style_css: str):
    """`transition: all` would animate the border width and cause reflow."""
    block = _block(style_css, ".stock-card-item.selected")
    assert "border:" not in block
    assert "border-color:" in block


# ----------------------------------------------------------------- data swap
def test_swap_fade_styles_exist(style_css: str):
    out_block = _block(style_css, ".data-swap-out")
    assert "opacity" in out_block
    assert "transform" in out_block
    in_block = _block(style_css, ".data-swap-in")
    assert "animation: dataSwapFade" in in_block

    keyframes = re.search(r"@keyframes\s+dataSwapFade\s*\{(.*?)\n\}", style_css, re.S)
    assert keyframes is not None
    body = keyframes.group(1)
    assert "opacity" in body
    assert "transform" in body
    assert "filter" not in body


def test_javascript_drives_the_swap_fade(script_js: str):
    assert "aplicarDadosComFade" in script_js
    assert 'classList.add("data-swap-out")' in script_js
    assert 'classList.add("data-swap-in")' in script_js
    assert 'classList.remove("data-swap-in")' in script_js


def test_swap_targets_exist_in_the_markup(index_html: str, script_js: str):
    """Every id used by the swap selector must exist in the dashboard."""
    match = re.search(r'SWAP_TARGET_SELECTOR\s*=\s*"([^"]+)"', script_js)
    assert match is not None
    selector = match.group(1)
    ids = set(re.findall(r"#([A-Za-z0-9_-]+)", selector))
    assert ids
    for element_id in ids:
        assert f'id="{element_id}"' in index_html, element_id


def test_swap_is_skipped_with_reduced_motion(script_js: str):
    assert 'window.matchMedia("(prefers-reduced-motion: reduce)")' in script_js
    assert "prefersReducedMotion.matches" in script_js


# --------------------------------------------------------------- status pulse
def test_online_status_pulses(style_css: str):
    block = _block(style_css, ".connection-indicator.online .conn-dot::after")
    assert "animation: connPing" in block
    keyframes = re.search(r"@keyframes\s+connPing\s*\{(.*?)\n\}", style_css, re.S)
    assert keyframes is not None
    body = keyframes.group(1)
    assert "opacity" in body
    assert "transform" in body
    assert "box-shadow" not in body


def test_offline_status_does_not_pulse(style_css: str):
    offline = _block(style_css, ".connection-indicator.offline .conn-dot")
    assert "animation" not in offline
    assert "::after" not in offline


# ------------------------------------------------------------------ scrollbar
def test_page_scrollbar_is_thin_and_dark(style_css: str):
    root = _block(style_css, ":root")
    assert "--scrollbar-size: 6px;" in root
    assert "--scrollbar-track: var(--bg-deep);" in root
    assert "--scrollbar-thumb: color-mix(in srgb, var(--brand-blue) 30%, var(--bg-elevated));" in root

    reset = _block(style_css, "*")
    assert "scrollbar-width: thin;" in reset
    assert "scrollbar-color:" in reset

    assert "::-webkit-scrollbar {" in style_css
    assert "::-webkit-scrollbar-thumb {" in style_css
    assert "border-radius: 999px;" in style_css


def test_sidebar_list_uses_the_page_scrollbar(style_css: str):
    """The inner list must not keep its own thick scrollbar."""
    block = _block(style_css, ".stock-list-container::-webkit-scrollbar")
    assert "width: 5px" in block or "var(--scrollbar-size)" in block


# ------------------------------------------------------------ tabular numbers
def test_numeric_elements_use_tabular_figures(style_css: str):
    block = _block(style_css, ".quant-card-val")
    assert "font-variant-numeric" not in block  # declared in the shared rule
    rule = re.search(
        r"\.quant-card-val,\s*\.quant-card-sub,(.*?)\{([^}]*)\}", style_css, re.S
    )
    assert rule is not None
    assert "font-variant-numeric: tabular-nums;" in rule.group(2)
    for selector in (
        ".quant-card-val",
        ".quant-card-sub",
        ".stock-price",
        ".stock-return",
        ".snapshot-date",
        ".asset-headline",
        ".target-floating-badge",
    ):
        assert selector in rule.group(1) or selector in rule.group(0), selector


def test_body_enables_tabular_figures(style_css: str):
    body = _block(style_css, "body")
    assert "font-variant-numeric: tabular-nums;" in body


# ------------------------------------------------------------ reduced motion
def test_reduced_motion_disables_pulse_and_swap(style_css: str):
    match = re.search(r"@media \(prefers-reduced-motion: reduce\) \{(.*)\Z", style_css, re.S)
    assert match is not None
    block = match.group(1)
    assert ".connection-indicator.online .conn-dot::after" in block
    assert ".data-swap-out" in block
    assert ".data-swap-in" in block
