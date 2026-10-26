"""Tests for the splash screen and the splash -> app reveal choreography.

These are static contract checks: they guard the timing tokens shared
between CSS and JavaScript, the state classes applied to <html>, and the
guarantee that the reveal only animates compositor-friendly properties.
"""

import re
from pathlib import Path

import pytest

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

TIMING_TOKENS = (
    "--splash-hold",
    "--splash-exit",
    "--reveal-delay",
    "--reveal-duration",
    "--reveal-fade",
    "--reveal-scale",
)

# Tokens whose value the JavaScript must read to stay in sync with CSS.
JS_DRIVEN_TOKENS = (
    "--splash-hold",
    "--splash-exit",
    "--reveal-delay",
    "--reveal-duration",
    "--reveal-fade",
)


@pytest.fixture(scope="module")
def index_html() -> str:
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def style_css() -> str:
    return (STATIC_DIR / "style.css").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def script_js() -> str:
    return (STATIC_DIR / "script.js").read_text(encoding="utf-8")


def test_html_starts_in_booting_state(index_html: str):
    """The app starts hidden behind the splash, with the dark theme as default."""
    assert '<html lang="pt-BR"' in index_html
    assert 'class="app-booting"' in index_html
    assert 'data-theme="dark"' in index_html


def test_splash_markup_present(index_html: str):
    assert 'id="splashScreen"' in index_html
    assert 'class="splash-screen"' in index_html
    assert 'class="splash-progress-fill"' in index_html
    assert 'class="splash-dots"' in index_html


def test_noscript_fallback_reveals_app(index_html: str):
    """Without JS the dashboard must not stay invisible."""
    assert "<noscript>" in index_html
    assert ".app-booting .dashboard-wrapper{opacity:1!important" in index_html


def test_eagle_sprite_is_shared(index_html: str):
    """The eagle emblem is defined once as a sprite and reused via <use>."""
    assert '<symbol id="eagle-mark"' in index_html
    assert index_html.count('<use href="#eagle-mark">') >= 1


def test_splash_shows_the_primary_logo(index_html: str):
    """The splash must display the real brand logo, not the eagle emblem."""
    assert 'class="splash-logo"' in index_html
    # The logo image is the base layer of the reusable logo-hero component.
    assert "splash-logo-img" in index_html
    assert 'class="logo-hero__base splash-logo-img"' in index_html
    assert 'src="logo.png"' in index_html
    assert 'srcset="logo.webp"' in index_html
    # The flying-eagle markup is gone from the splash.
    assert "splash-eagle" not in index_html


def test_cybernetic_eagle_uses_the_brand_palette(index_html: str):
    """The emblem must adopt the logo's palette, not the emoji browns."""
    start = index_html.index('<svg class="svg-sprite"')
    sprite = index_html[start:index_html.index("</svg>", start)]
    for legacy in ("#5D4037", "#795548", "#8D6E63", "#F59E0B", "#D97706", "#4E342E"):
        assert legacy not in sprite, legacy
    for brand in ("#02AAFF", "#09FFFF", "#00FFA6", "#0590FF"):
        assert brand in sprite, brand


def test_logo_pulse_is_an_opacity_oscillation(style_css: str):
    """The logo pulse must animate opacity only (compositor friendly)."""
    keyframes = re.search(
        r"@keyframes\s+splashLogoPulse\s*\{(.*?)\n\}", style_css, re.S
    )
    assert keyframes is not None
    body = keyframes.group(1)
    assert body.count("opacity") >= 2
    assert "transform" not in body
    assert "filter" not in body


def test_logo_pulse_is_applied_to_the_logo(style_css: str):
    assert ".splash-logo-img" in style_css
    block = re.search(
        r"\.splash-logo-img\s*\{(.*?)\}", style_css, re.S
    )
    assert block is not None
    assert "splashLogoPulse" in block.group(1)


def test_brand_tokens_are_defined(style_css: str):
    for token in (
        "--brand-blue",
        "--brand-cyan",
        "--brand-teal",
        "--brand-navy",
        "--brand-ink",
    ):
        assert re.search(re.escape(token) + r"\s*:", style_css), token


def test_logo_uses_responsive_sizing(style_css: str):
    """The logo must scale with the viewport without overflowing."""
    block = re.search(r"\.splash-logo\s*\{(.*?)\}", style_css, re.S)
    assert block is not None
    body = block.group(1)
    assert "vmin" in body or "vw" in body
    assert "aspect-ratio" in body


def test_timing_tokens_defined_in_css(style_css: str):
    for token in TIMING_TOKENS:
        assert re.search(re.escape(token) + r"\s*:", style_css), token


def test_reveal_rules_use_timing_tokens(style_css: str):
    assert ".app-booting .dashboard-wrapper" in style_css
    assert ".app-revealing .dashboard-wrapper" in style_css
    assert "var(--reveal-duration)" in style_css
    assert "var(--reveal-fade)" in style_css
    assert "var(--reveal-scale)" in style_css


def _split_top_level(declaration: str) -> list:
    """Split a CSS declaration list on commas that are not inside parens."""
    parts = []
    current = []
    depth = 0
    for char in declaration:
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        if char == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(char)
    parts.append("".join(current))
    return parts


def test_reveal_only_animates_compositor_properties(style_css: str):
    """The reveal must not trigger layout or paint on every frame."""
    block = re.search(
        r"\.app-revealing \.dashboard-wrapper\s*\{(.*?)\}", style_css, re.S
    )
    assert block is not None
    body = block.group(1)
    assert "transition:" in body
    animated = re.findall(r"transition:\s*([^;]+);", body)
    assert animated
    for declaration in animated:
        for item in _split_top_level(declaration):
            name = item.strip().split()[0]
            assert name in ("transform", "opacity"), name


def test_splash_exit_keyframes_scale_and_fade(style_css: str):
    keyframes = re.search(
        r"@keyframes\s+splashExit\s*\{(.*?)\n\}", style_css, re.S
    )
    assert keyframes is not None
    body = keyframes.group(1)
    assert "opacity" in body
    assert "scale(" in body
    assert "visibility: hidden" in body


def test_reduced_motion_disables_scaling(style_css: str):
    block = re.search(
        r"@media \(prefers-reduced-motion: reduce\) \{(.*)$", style_css, re.S
    )
    assert block is not None
    assert "--reveal-scale: 1" in block.group(1)


def test_javascript_reads_the_same_timing_tokens(script_js: str):
    """CSS and JS must share one source of truth for the choreography."""
    for token in JS_DRIVEN_TOKENS:
        assert token in script_js, token


def test_javascript_toggles_the_state_classes(script_js: str):
    assert 'classList.remove("app-booting")' in script_js
    assert 'classList.add("app-revealing")' in script_js
    assert 'classList.remove("app-revealing")' in script_js


def test_javascript_targets_the_viewport_center(script_js: str):
    """The scale origin must be the viewport center, not the wrapper center."""
    assert "window.innerHeight / 2" in script_js
    assert "transformOrigin" in script_js


def test_javascript_has_failsafe_paths(script_js: str):
    """The app must never stay hidden if a timer or animation is dropped."""
    assert "animationend" in script_js
    assert "setTimeout" in script_js
