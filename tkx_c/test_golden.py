"""Testy regresji TKX-C: golden sequences i cechy wariantów."""
from __future__ import annotations

import json
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLD = os.path.join(ROOT, "tkx_c", "golden")
VARIANTS = ["V0-32k", "V1-32k", "V2-32k", "V2-24k", "V2-16k",
            "V2-base-32k", "V2-base-24k", "V2-base-16k",
            "V2b-32k", "V2b-24k", "V2b-16k",
            "V3-32k", "V3-24k", "V3-16k"]


def _load(name):
    from tokenizers import Tokenizer
    path = os.path.join(ROOT, "hf", "variants", name, "tokenizer.json")
    if not os.path.exists(path):
        pytest.skip(f"brak {name}")
    return Tokenizer.from_file(path), path


@pytest.mark.parametrize("name", VARIANTS)
def test_golden_sequences(name):
    path = os.path.join(GOLD, name + ".json")
    if not os.path.exists(path):
        pytest.skip(f"brak golden {name}")
    data = json.load(open(os.path.join(GOLD, "dataset.json"), encoding="utf-8"))
    gold = json.load(open(path, encoding="utf-8"))
    tok, tok_path = _load(name)
    assert len(gold["sequences"]) == len(data["sentences"])
    for sent, ids in zip(data["sentences"], gold["sequences"]):
        now = tok.encode(sent, add_special_tokens=False).ids
        assert now == ids, (name, sent[:80])
        assert tok.decode(now, skip_special_tokens=False) == sent, (name, sent[:80])


@pytest.mark.parametrize("name", [v for v in VARIANTS if v.startswith(("V1", "V2"))])
def test_no_multidigit_tokens(name):
    tok, _ = _load(name)
    vocab = tok.get_vocab()
    for token in vocab:
        digits = [c for c in token if c.isdigit()]
        if digits:
            # tokeny byte-level mogą mieć cyfry jako fragment; sprawdzamy ciągi cyfr
            import re
            assert all(len(x) == 1 for x in re.findall(r"\d+", token)), (name, token)


def test_calendar_is_flat_in_v1_v2_v2b_v3():
    for name in ("V1-32k", "V2-32k", "V2-24k", "V2-16k",
                 "V2b-32k", "V2b-24k", "V2b-16k",
                 "V3-32k", "V3-24k", "V3-16k"):
        tok, _ = _load(name)
        counts = set()
        for y in range(2015, 2036):
            counts.add(len(tok.encode(f"w roku {y} r. zadanie", add_special_tokens=False).ids))
        assert len(counts) == 1, (name, counts)


def test_v3_has_all_forced_digit_groups():
    tok, _ = _load("V3-32k")
    vocab = set(tok.get_vocab())
    missing = []
    for n in range(100):
        if f"{n:02d}" not in vocab:
            missing.append(f"{n:02d}")
    for n in range(1000):
        if f"{n:03d}" not in vocab:
            missing.append(f"{n:03d}")
    assert not missing, missing[:20]


def test_v2b_has_space_digit_tokens_without_trailing_space_superwords():
    tok, _ = _load("V2b-32k")
    vocab = set(tok.get_vocab())
    for d in "0123456789":
        assert "Ġ" + d in vocab, d
    assert not any(len(t) > 1 and t.endswith("Ġ") for t in vocab), "superword z końcową spacją"
