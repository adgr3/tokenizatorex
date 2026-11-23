"""Testy TKX-V21-JSON: generator, przeciek, §, round-trip, tokeny specjalne."""
from __future__ import annotations

import hashlib
import json
import os
import sys

import pytest
from tokenizers import Tokenizer as HFTokenizer

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from tkx_v21.generuj_json import generuj  # noqa: E402

DATA = os.path.join(REPO, "tkx_v21", "dane")
RESULTS = os.path.join(REPO, "results")


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _load_tok(name):
    p = os.path.join(REPO, "hf", "variants", name, "tokenizer.json")
    if not os.path.isfile(p):
        pytest.skip(f"brak tokenizera {name}")
    return HFTokenizer.from_file(p)


def _load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def test_generator_deterministic(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    generuj(str(a), 500)
    generuj(str(b), 500)
    for name in ("json_train.txt", "json_generic_heldout_dev.jsonl",
                 "json_generic_heldout_test.jsonl", "json_generic_manifest.json"):
        assert _sha(os.path.join(a, name)) == _sha(os.path.join(b, name)), name


def test_heldout_niezalezny_od_liczby_przykladow(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    generuj(str(a), 100)
    generuj(str(b), 900)
    for name in ("json_generic_heldout_dev.jsonl", "json_generic_heldout_test.jsonl"):
        assert _sha(os.path.join(a, name)) == _sha(os.path.join(b, name)), name


def test_generator_narzedzia_rozdzielone(tmp_path):
    m = generuj(str(tmp_path), 200)
    assert len(m["train_tools"]) == 40
    assert len(m["heldout_tools"]) == 10
    assert not set(m["train_tools"]) & set(m["heldout_tools"])
    assert m["heldout_dev"] == 100 and m["heldout_test"] == 100


def test_brak_przecieku():
    p = os.path.join(RESULTS, "tkx_v21_leak.json")
    if not os.path.isfile(p):
        pytest.skip("brak results/tkx_v21_leak.json")
    leak = _load_json(p)
    assert leak["summary"]["status"] == "OK"
    for s, row in leak["test_docs"].items():
        assert row["exact_matches"] == 0, s
        assert row["docs_over_50pct"] == 0, s


def test_sekcja_jeden_token_w_wybranym():
    sel_p = os.path.join(RESULTS, "tkx_v21_selection.json")
    if not os.path.isfile(sel_p):
        pytest.skip("brak selection.json")
    sel = _load_json(sel_p)
    names = [sel["base"]]
    if sel.get("winner"):
        names.append(sel["winner"])
    for name in names:
        tok = _load_tok(name)
        assert len(tok.encode("§", add_special_tokens=False).ids) == 1, name


def test_roundtrip_i_nfd():
    sel_p = os.path.join(RESULTS, "tkx_v21_selection.json")
    names = ["V0R-32k", "V0J5S-32k"]
    if os.path.isfile(sel_p) and _load_json(sel_p).get("winner"):
        names.append(_load_json(sel_p)["winner"])
    samples = [
        "Zażółć gęślą jaźń. § 362(a) Kodeksu postępowania administracyjnego.",
        "1 234 567,89 zł · 25 września 2026 r. · KIO 1234/26",
        "<tool_call>{\"name\":\"pobierz_pogode\",\"arguments\":{\"miasto\":\"Kraków\"}}</tool_call>",
        "e\u0301",  # NFD (e + combining acute)
    ]
    for name in dict.fromkeys(names):
        tok = _load_tok(name)
        for text in samples:
            ids = tok.encode(text, add_special_tokens=False).ids
            assert tok.decode(ids) == text, (name, text)


def test_tokeny_specjalne_v0j5s():
    tok = _load_tok("V0J5S-32k")
    for name in ["<|system|>", "<|uzytkownik|>", "<|asystent|>", "<|narzedzie|>",
                 "<tool_call>", "</tool_call>"]:
        assert len(tok.encode(name, add_special_tokens=False).ids) == 1, name


def test_wybor_zgodny_z_regula():
    p = os.path.join(RESULTS, "tkx_v21_selection.json")
    if not os.path.isfile(p):
        pytest.skip("brak selection.json")
    sel = _load_json(p)
    if not sel.get("winner"):
        return
    assert sel["winner"] in {"V0J2-32k", "V0J5-32k", "V0J10-32k"}
    rec = sel["candidates"][sel["winner"]]
    assert rec["feasible"]
    assert rec["section_one_token"]
    for s, d in rec["polish_deltas"].items():
        assert d["delta_pct"] <= 1.0 + 1e-9, s
