"""Anti-hallucination number validator for LLM-generated market rationales."""

import hashlib
import json
import re
from typing import Any, Dict, List

_COMMA_DECIMAL_RE = re.compile(r"(\d+),(\d+)")
_NUMBER_RE = re.compile(r"[-+]?\d*\.?\d+")

# Period lengths and calendar constants that are never price claims.
_IGNORED_CONSTANTS = frozenset({14.0, 30.0, 200.0, 2024.0, 2025.0, 2026.0, 1.0, 2.0})


def extract_numbers(text: str) -> List[float]:
    """
    Extract numbers from text (supporting both 13.27 and 13,27 formats).
    Excludes known standard constants (14 periods, SMA 200, WMA 30, current years).
    """
    cleaned = _COMMA_DECIMAL_RE.sub(r"\1.\2", text)
    tokens = _NUMBER_RE.findall(cleaned)
    numbers = []

    for t in tokens:
        try:
            val = float(t)
            if val in _IGNORED_CONSTANTS:
                continue
            numbers.append(val)
        except ValueError:
            continue
    return numbers


def extract_fact_numbers(facts: Dict[str, Any]) -> List[float]:
    """Recursively extract all numeric values from facts dictionary."""
    allowed: List[float] = []

    def _collect(obj):
        if isinstance(obj, (int, float)):
            allowed.append(float(obj))
        elif isinstance(obj, dict):
            for v in obj.values():
                _collect(v)
        elif isinstance(obj, (list, tuple)):
            for v in obj:
                _collect(v)
        elif isinstance(obj, str):
            nums = extract_numbers(obj)
            allowed.extend(nums)

    _collect(facts)
    return allowed


def validate_numbers(
    generated_text: str,
    facts: Dict[str, Any],
    tolerance: float = 0.005
) -> bool:
    """
    Verify that every numeric claim in generated_text matches facts within 0.5% tolerance.
    Returns True if verified; False if hallucinated.
    """
    text_numbers = extract_numbers(generated_text)
    if not text_numbers:
        return True

    fact_numbers = extract_fact_numbers(facts)
    if not fact_numbers:
        return False

    for num in text_numbers:
        matched = False
        for fact_num in fact_numbers:
            abs_diff = abs(num - fact_num)
            base = max(abs(fact_num), 0.0001)
            if (abs_diff / base) <= tolerance:
                matched = True
                break
        if not matched:
            return False

    return True


def hash_facts(facts: Dict[str, Any]) -> str:
    """Compute deterministic SHA-256 hash of facts dictionary."""
    dumped = json.dumps(facts, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(dumped.encode("utf-8")).hexdigest()
