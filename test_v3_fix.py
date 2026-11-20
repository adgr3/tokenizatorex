"""Testy poprawki V3 (WAŻNE-1 Codexa / ataki 1, 2, 8 Groka).

Reguła z protokołu §9.7: ciąg cyfr tniemy od prawej na grupy po 3,
lewy ogon 1–2 cyfry. Ta sama reguła obowiązuje w treningu, w enkoderze
Pythona i w eksporcie HF — testy sprawdzają kanoniczny eksport HF oraz
zgodność Python == HF.
"""
from __future__ import annotations

import os
import re
import sys

import pytest
from tokenizers import Tokenizer

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "audit"))

from superbpe import SuperBPETokenizer  # noqa: E402

HF_V3 = os.path.join(ROOT, "hf", "variants", "V3-32k", "tokenizer.json")
PY_V3 = os.path.join(ROOT, "tokenizers", "variants", "V3-32k", "superbpe.json")
DIGIT_RUN = re.compile(r"\d+")


@pytest.fixture(scope="module")
def hf_v3() -> Tokenizer:
    return Tokenizer.from_file(HF_V3)


@pytest.fixture(scope="module")
def py_v3() -> SuperBPETokenizer:
    return SuperBPETokenizer.load(PY_V3)


def pieces(tok: Tokenizer, text: str) -> list[str]:
    """Kawałki wizualizowane tak samo jak w examples.json (· = spacja)."""
    return [tok.decode([i], skip_special_tokens=False).replace(" ", "·")
            for i in tok.encode(text, add_special_tokens=False).ids]


def test_v3_grid_hundreds_and_thousands_are_single_tokens(hf_v3):
    bad3 = [f"{n:03d}" for n in range(1000)
            if len(hf_v3.encode(f"{n:03d}", add_special_tokens=False).ids) != 1]
    bad2 = [f"{n:02d}" for n in range(100)
            if len(hf_v3.encode(f"{n:02d}", add_special_tokens=False).ids) != 1]
    assert not bad3, bad3[:20]
    assert not bad2, bad2[:20]


@pytest.mark.parametrize("text,expected", [
    ("00-950", "00|-|950"),
    ("poz. 1320", "po|z.|·1|320"),
    ("0012", "0|012"),
    ("123456789012345", "123|456|789|012|345"),
    ("45233140-2", "45|233|140|-|2"),
    ("1999", "1|999"),
    ("2024", "2|024"),
    ("2027", "2|027"),
    ("2024 r.", "2|024|·r."),
    ("1234", "1|234"),
    ("1234567", "1|234|567"),
    ("1000000", "1|000|000"),
    ("100", "100"),
    ("950", "950"),
    ("1 234 567", "1|·234|·567"),
])
def test_v3_hard_cases_from_codex_table_a2(hf_v3, text, expected):
    assert "|".join(pieces(hf_v3, text)) == expected


@pytest.mark.parametrize("bare,spaced", [
    ("1234", "1 234"),
    ("1234567", "1 234 567"),
    ("1000000", "1 000 000"),
    ("1999", "1 999"),
])
def test_v3_amounts_same_digit_groups_in_both_notations(hf_v3, bare, spaced):
    stripped = [p.lstrip("·") for p in pieces(hf_v3, bare)]
    assert stripped == [p.lstrip("·") for p in pieces(hf_v3, spaced)]


def test_v3_cpv_body_is_always_two_three_three(hf_v3):
    # Kanoniczny HF na zamrożonym teście: wszystkie kody CPV mają kształt 2+3+3.
    import importlib.util
    import unicodedata
    from common import load_domain
    spec = importlib.util.spec_from_file_location(
        "mr3", os.path.join(ROOT, "tkx_c", "review_grok", "measure_r3.py"))
    mr3 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mr3)
    rx = re.compile(r"\b\d{8}-\d\b")
    found = 0
    for domain in mr3.OFFICIAL:
        for doc in load_domain(domain, "test"):
            text = unicodedata.normalize("NFC", doc["text"])
            spans = mr3.spans_of(hf_v3.encode(text, add_special_tokens=False))
            for match in rx.finditer(text):
                s = match.start()
                assert mr3.shape_label(mr3.piece_lengths(spans, s, s + 8)) == "2+3+3"
                found += 1
    assert found > 100


def test_v3_python_matches_hf_on_all_dev_digit_runs(hf_v3, py_v3):
    from common import load_domain
    checked = 0
    for domain in ("przetargi_ogloszenia", "przetargi_kio", "samorzad_uchwaly",
                   "granty_ogloszenia", "prawo_eli", "ocr_prasa", "tabele_json"):
        for doc in load_domain(domain, "dev"):
            for run in DIGIT_RUN.findall(doc["text"]):
                assert py_v3.encode_ordinary(run) == hf_v3.encode(run, add_special_tokens=False).ids, run
                checked += 1
    assert checked > 1000


def test_v3_paragraph_sign_is_recorded_as_two_byte_pieces(hf_v3):
    # § (U+00A7, UTF-8 C2 A7) nie jest częścią reguły cyfr i pozostaje
    # dwoma kawałkami — zapisujemy to jawnie zamiast udawać naprawę.
    assert len(hf_v3.encode("§", add_special_tokens=False).ids) == 2
