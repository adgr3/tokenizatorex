"""Testy jednostkowe TKX-C: cyfry, NFC, zgodność wsteczna v1."""
from __future__ import annotations

import os
import unicodedata

import pytest

from superbpe import (WORD_PATTERN, WORD_PATTERN_GROUPS3, WORD_PATTERN_SINGLE_DIGITS,
                      WORD_PATTERN_SPACE_FIRST, SuperBPETokenizer, normalize_text,
                      pretokens, split_groups3)

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


def test_v2b_space_attaches_to_first_digit():
    pts = pretokens("w roku 2024 r. kwota 1 234 zł", WORD_PATTERN_SPACE_FIRST)
    assert " 2" in pts and " 1" in pts
    assert "roku " not in pts
    assert all(not (p.endswith(" ") and p.strip().isalpha()) for p in pts)


def test_v3_groups_from_right():
    assert split_groups3("2024") == ["2", "024"]
    assert split_groups3("45233140") == ["45", "233", "140"]
    assert split_groups3(" 45233140") == [" 45", "233", "140"]
    assert split_groups3("12345") == ["12", "345"]
    assert pretokens("w roku 2024 r.", WORD_PATTERN_GROUPS3)[:4] == ["w", " roku", " 2", "024"]


def test_v3_forced_tokens_present_after_small_train():
    from collections import Counter
    from superbpe import chunks
    tok = SuperBPETokenizer(digits="groups3", normalize="nfc")
    cnt1 = Counter(pretokens("2024 45233140 000 999 w roku 2035", tok.word_pattern))
    tok.train_stage1(cnt1, 4000, log=None)
    have = set(tok.vocab)
    for s in ("000", "999", "024", "233", "45", "99", "0"):
        assert s.encode() in have, s


def test_v2b_and_v3_roundtrip_via_hf_export(tmp_path):
    from tokenizers import Tokenizer
    from collections import Counter
    from superbpe import chunks
    from export_hf import to_hf
    text = "w roku 2024 r. zadanie 1 234 567,89 zł CPV 45233140-2"
    for mode in ("space_first", "groups3"):
        tok = SuperBPETokenizer(digits=mode, normalize="nfc")
        cnt1 = Counter(pretokens(text * 4, tok.word_pattern))
        tok.train_stage1(cnt1, 4000, log=None)
        tok.train_stage2(Counter(chunks(text * 4)), 4200, log=None)
        tok.add_specials(["<|endoftext|>"])
        path = str(tmp_path / (mode + ".json"))
        to_hf(tok).save(path)
        hf = Tokenizer.from_file(path)
        for s in ("w roku 2024 r. zadanie", "1 234 567,89 zł", "45233140-2"):
            ids = hf.encode(s, add_special_tokens=False).ids
            assert hf.decode(ids, skip_special_tokens=False) == s
            assert ids == tok.encode(s), (mode, s)


def test_load_v1_keeps_defaults():
    if not os.path.exists(V1):
        pytest.skip("brak v1")
    tok = SuperBPETokenizer.load(V1)
    assert tok.digits == "grouped"
    assert tok.normalize == "none"
    assert tok.word_pattern == WORD_PATTERN
    s = "Zażółć gęślą jaźń 2024"
    assert tok.decode(tok.encode(s)) == s
