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
        p = os.path.join(REPO, "tkx_v21", "hf", name, "tokenizer.json")
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
    # Korpus nie przecieka; wzorce JSON mają świadomie raportowane 2/10 > 50%.
    assert leak["summary"]["status"] == "CZESCIOWE_POKRYCIE_SZKIELETEM"
    assert leak["summary"]["pattern_docs_over_50pct"] == 2
    assert leak["test_docs"]["wzorce_json"]["max_coverage"] > 0.5
    for s, row in leak["test_docs"].items():
        assert row["exact_matches"] == 0, s
        if s in ("tc1_test", "json_generic_test"):
            assert row["docs_over_50pct"] == 0, s
    assert leak["summary"]["wzorce_json_exact"] == 0


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
            assert tok.decode(ids, skip_special_tokens=False) == text, (name, text)


def test_tokeny_specjalne_v0j5s():
    tok = _load_tok("V0J5S-32k")
    for name in ["<|system|>", "<|uzytkownik|>", "<|asystent|>", "<|narzedzie|>",
                 "<tool_call>", "</tool_call>"]:
        assert len(tok.encode(name, add_special_tokens=False).ids) == 1, name


def test_granty149_i_kandydat_warunkowy():
    gp = os.path.join(RESULTS, "tkx_v21_granty149.json")
    sp = os.path.join(RESULTS, "tkx_v21_selection_r2.json")
    if not (os.path.isfile(gp) and os.path.isfile(sp)):
        pytest.skip("brak wynikow granty149/selection_r2")
    g = _load_json(gp)
    s = _load_json(sp)
    assert g["docs"] == 149
    assert g["tokenizers"]["V0J2-32k"]["delta_vs_v0r_pct"] <= 1.0
    assert s["conditional_winner"] == "V0J2-32k"
    assert s["original_result"]["winner"] is None  # nie mylić z wyborem
    assert "warunkowy" in s["conditional_note"]


def test_przeciek_wzorcow_json():
    p = os.path.join(RESULTS, "tkx_v21_leak.json")
    if not os.path.isfile(p):
        pytest.skip("brak results/tkx_v21_leak.json")
    leak = _load_json(p)
    w = leak["test_docs"]["wzorce_json"]
    assert w["docs"] == 10
    assert w["exact_matches"] == 0
    assert 0.0 <= w["max_coverage"] <= 1.0


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


def test_formaty_dat_kwot_paragraf():
    p = os.path.join(RESULTS, "tkx_v21_formaty.json")
    if not os.path.isfile(p):
        pytest.skip("brak results/tkx_v21_formaty.json")
    d = _load_json(p)
    # "§" = 1 token w V0 i V0J2
    par = d["paragraf"]["§"]
    assert par["V0"] == 1
    assert par["V0J2"] == 1
    # Średnia na datach V0J2 <= V0 + 0,1
    da = d["summary"]["date_avg"]
    assert da["V0J2"] <= da["V0"] + 0.1 + 1e-9
    # 12 dat, 9 kwot, 9 form z §; każdy zapis kwoty ma własne 40 próbek.
    assert len(d["daty"]) == 12
    assert len(d["kwoty"]) == 9
    assert len(d["paragraf"]) == 9
    assert all(n == 40 for n in d["kwoty_n"].values())
    lo, hi = d["kwoty_zakres"]["1,2 mln zł"]
    assert lo >= 1_000_000 and hi <= 500_000_000
    lo, hi = d["kwoty_zakres"]["123 tys. zł"]
    assert lo >= 1_000 and hi <= 999_000
    assert not any(s.startswith("0,0 mln") for s in d["samples"]["1,2 mln zł"])
    assert not any(s.startswith("0 tys") for s in d["samples"]["123 tys. zł"])


def test_heldout_forms_breakdown():
    p = os.path.join(RESULTS, "tkx_v21_heldout_forms.json")
    if not os.path.isfile(p):
        pytest.skip("brak results/tkx_v21_heldout_forms.json")
    d = _load_json(p)
    assert d["docs"] == 100
    assert sum(x["docs"] for x in d["forms"].values()) == 100
    assert d["overall"]["delta_pct"] < -25
    assert d["forms"]["result"]["delta_pct"] > -15
    assert d["forms"]["compact"]["delta_pct"] < -40
