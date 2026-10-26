"""Tests for the labelled demo fixture (SIMULADO) shipped with the project."""

import json
import math
from pathlib import Path

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "demo_analysis.json"


def test_demo_fixture_is_valid_json(demo_analysis):
    assert isinstance(demo_analysis, dict)
    assert "meta" in demo_analysis
    assert "candles" in demo_analysis
    assert "setup" in demo_analysis


def test_demo_fixture_is_labelled_as_simulated(demo_analysis):
    meta = demo_analysis["meta"]
    assert meta["source"] == "SIMULADO"
    assert meta["is_simulated"] is True
    assert meta["ribbon"] == "SIMULADO"
    assert "SIMULADO" in json.dumps(demo_analysis, ensure_ascii=False)


def test_demo_fixture_keeps_disclaimer(demo_analysis):
    disclaimer = demo_analysis["meta"]["disclaimer"]
    assert "Não constitui recomendação de investimento" in disclaimer
    assert demo_analysis["disclaimer"] == disclaimer


def test_demo_fixture_has_no_invalid_numbers(demo_analysis):
    def walk(node):
        if isinstance(node, dict):
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
        elif isinstance(node, float):
            assert math.isfinite(node)

    walk(demo_analysis)


def test_demo_fixture_setup_is_internally_consistent(demo_analysis):
    setup = demo_analysis["setup"]
    assert setup["signal"] in ("ALTA", "BAIXA", "NEUTRO")
    assert setup["entry"] > 0
    assert setup["target"] > 0
    assert setup["stop"] > 0
    assert setup["payoff"] >= 1.0
    assert len(demo_analysis["candles"]) == len(demo_analysis["forecast"]["median"])
