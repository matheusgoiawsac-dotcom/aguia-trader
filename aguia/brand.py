"""Brand design tokens.

Single source of truth: ``config/brand_palette.json``. The values were
extracted from the AGUIA TRADER Cibernetica logo (electric blue + cyan +
neon teal on near-black) and are mirrored by the ``:root`` block of
``static/style.css``.

Keeping the palette in one JSON file lets the Python side (matplotlib
chart export) and the front-end (CSS custom properties) share exactly the
same colours; ``tests/test_brand_palette.py`` asserts the two never
drift apart.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

ROOT_DIR = Path(__file__).resolve().parent.parent
BRAND_PALETTE_PATH = ROOT_DIR / "config" / "brand_palette.json"


@lru_cache(maxsize=1)
def load_brand_palette() -> Dict[str, Any]:
    """Return the cached brand palette."""
    with open(BRAND_PALETTE_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


def brand_group(group: str) -> Dict[str, str]:
    """Return one group of the palette (e.g. ``brand``, ``chart``)."""
    palette = load_brand_palette()
    if group not in palette:
        raise KeyError(f"Unknown brand palette group: {group}")
    return palette[group]


def brand_color(group: str, name: str) -> str:
    """Return a single token, e.g. ``brand_color("chart", "up")``."""
    values = brand_group(group)
    if name not in values:
        raise KeyError(f"Unknown brand token: {group}.{name}")
    return values[name]
