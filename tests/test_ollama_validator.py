"""Tests for anti-hallucination number validator and facts hashing."""

import pytest
from aguia.explain.validator import (
    extract_numbers,
    validate_numbers,
    hash_facts
)


def test_extract_numbers_formats():
    text = "O ativo PETR4 cotado a R$ 38,45 com alvo em R$ 42.10 (+9,49%) e stop R$ 36,15."
    nums = extract_numbers(text)
    assert 38.45 in nums
    assert 42.10 in nums
    assert 9.49 in nums
    assert 36.15 in nums


def test_validate_numbers_valid_claim():
    facts = {
        "ticker": "PETR4",
        "preco": 38.45,
        "alvo": 42.10,
        "stop": 36.15,
        "projecao_pct": 9.49,
        "risco_pct": -5.98,
        "payoff": "1.59 : 1",
        "indicadores": {
            "sma200": 34.00,
            "wma30": 36.50,
            "atr14": 1.70
        }
    }
    text = (
        "O ativo PETR4 negociado a R$ 38,45 opera acima da WMA 30 (R$ 36,50) "
        "com alvo projetado em R$ 42,10 (+9,49%) e stop loss em R$ 36,15."
    )
    assert validate_numbers(text, facts) is True


def test_validate_numbers_rejects_hallucination():
    facts = {
        "ticker": "VALE3",
        "preco": 61.20,
        "alvo": 68.00,
        "stop": 58.00
    }
    # Text invents a false target of 95.00
    hallucinated_text = "O ativo VALE3 cotado a R$ 61,20 possui projeção expressiva até R$ 95,00."
    assert validate_numbers(hallucinated_text, facts) is False


def test_validate_numbers_tolerance_window():
    facts = {"preco": 100.0}
    # Within 0.5% (100.3 is +0.3%)
    assert validate_numbers("Preço em R$ 100,30.", facts, tolerance=0.005) is True
    # Outside 0.5% (101.5 is +1.5%)
    assert validate_numbers("Preço em R$ 101,50.", facts, tolerance=0.005) is False


def test_hash_facts_consistency():
    facts1 = {"ticker": "PETR4", "preco": 38.45}
    facts2 = {"preco": 38.45, "ticker": "PETR4"}
    h1 = hash_facts(facts1)
    h2 = hash_facts(facts2)
    assert h1 == h2
    assert len(h1) == 64
