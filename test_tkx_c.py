"""Testy jednostkowe TKX-C: cyfry, NFC, zgodność wsteczna v1."""
from __future__ import annotations

import os
import unicodedata

import pytest

from superbpe import (WORD_PATTERN, WORD_PATTERN_SINGLE_DIGITS, SuperBPETokenizer,
                      normalize_text, pretokens)

ROOT = os.path.dirname(os.path.abspath(__file__))
V1 = os.path.join(ROOT, "tokenizers", "tokenizatorex-32k.json")


def test_single_digits_are_separate():
    cases = ["2024", "2027", "2031", "1 234 567,89", "45233140-2",
             "ZP.271.12.2026", "Dz.U. z 2024 r. poz. 1320"]
    for text in cases:
        pts = pretokens(text, WORD_PATTERN_SINGLE_DIGITS)
        digit_pts = [p for p in pts if any(c.isdigit() for c in p)]
        assert digit_pts, text
        assert all(len(p) == 1 and p.isdigit() for p in digit_pts), (text, digit_pts)
        assert all(not any(c.isdigit() for c in p) for p in pts if p not in digit_pts)


def test_v1_pattern_still_groups_digits():
    assert pretokens("2024", WORD_PATTERN) == ["202", "4"]


def test_nfc_is_single_function():
    nfd = unicodedata.normalize("NFD", "Zażółć gęślą jaźń")
    assert normalize_text(nfd, "nfc") == unicodedata.normalize("NFC", nfd)
    assert normalize_text(nfd, "none") == nfd
    with pytest.raises(ValueError):
        normalize_text("x", "bad")


def test_digits_and_nfc_pretokens_equal_after_nfc():
    nfd = unicodedata.normalize("NFD", "w roku 2026 r. kwota 1 234,50 zł")
    a = pretokens(nfd, WORD_PATTERN_SINGLE_DIGITS, normalize="nfc")
    b = pretokens(unicodedata.normalize("NFC", nfd), WORD_PATTERN_SINGLE_DIGITS)
    assert a == b


def test_load_v1_keeps_defaults():
    if not os.path.exists(V1):
        pytest.skip("brak v1")
    tok = SuperBPETokenizer.load(V1)
    assert tok.digits == "grouped"
    assert tok.normalize == "none"
    assert tok.word_pattern == WORD_PATTERN
    s = "Zażółć gęślą jaźń 2024"
    assert tok.decode(tok.encode(s)) == s
