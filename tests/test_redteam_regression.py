"""R6: stałe testy regresji z red teamu A (SuperBPE / tokeny specjalne).

Zakres: zwykły polski urzędowy (liczba + słowo, daty, kwoty z NBSP, przepisy),
round-trip, literalne tokeny specjalne, fuzzing seed 20261124 (2 000 napisów).
Znane przypadki superwordów od środka słowa są `xfail(strict=True)` z opisem
„znana wada SuperBPE, naprawa w v2.1”.
"""
from __future__ import annotations

import json
import random
import re
import sys
from pathlib import Path

import pytest
from tokenizers import Tokenizer

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from redteam_cases import cases, unicode_cases  # noqa: E402

TOKS = {
    "V0-32k": REPO / "hf/variants/V0-32k/tokenizer.json",
    "V0J2-32k": REPO / "hf/variants/V0J2-32k/tokenizer.json",
}
KNOWN_SUPERWORDS = [
    "zgodność z", "kolejność z", "informacja z", "odpowiedź do", "uchwała się",
]
WORD_RUN_RE = re.compile(r"[^\W_]+", re.UNICODE)
LETTER_RUN_RE = re.compile(r"[^\W\d_][^\W_]*", re.UNICODE)
SPECIAL_NAMES = ["<|endoftext|>", "<|im_start|>", "<|im_end|>"]


def load_tok(label: str) -> Tokenizer:
    return Tokenizer.from_file(str(TOKS[label]))


def decode_all(tok: Tokenizer, ids) -> str:
    return tok.decode(list(ids), skip_special_tokens=False)


def crosses_word_space(token: str) -> bool:
    m = re.search(r"\s+", token)
    if m is None:
        return False
    before = token[:m.start()]
    after = token[m.end():]
    return bool(WORD_RUN_RE.search(before) and WORD_RUN_RE.search(after))


def bad_boundaries(tok: Tokenizer, text: str):
    enc = tok.encode(text, add_special_tokens=False)
    toks = [tok.decode([i], skip_special_tokens=False) for i in enc.ids]
    runs = [(m.start(), m.end()) for m in WORD_RUN_RE.finditer(text)]
    letter_runs = [(m.start(), m.end()) for m in LETTER_RUN_RE.finditer(text)]
    starts = [a for a, _ in enc.offsets]
    bad = []
    for k, start in enumerate(starts[1:], start=1):
        if not any(a < start < b for a, b in runs):
            continue
        if not any(a < start < b for a, b in letter_runs):
            continue
        left = toks[k - 1] if k - 1 < len(toks) else ""
        right = toks[k] if k < len(toks) else ""
        if crosses_word_space(left) or crosses_word_space(right):
            bad.append((start, left, right))
    return bad


def test_official_case_set_shape():
    cs = cases()
    assert len(cs) >= 150
    assert len({c[0] for c in cs}) == len(cs)
    assert len({c[1] for c in cs}) == 8
    assert min(sum(1 for c in cs if c[1] == g) for g in {c[1] for c in cs}) >= 10


def test_official_case_set_roundtrip():
    for label in TOKS:
        tok = load_tok(label)
        for cid, _group, text in cases():
            enc = tok.encode(text, add_special_tokens=False)
            assert decode_all(tok, enc.ids) == text, (label, cid, text)


def test_unicode_cases_roundtrip():
    for label in TOKS:
        tok = load_tok(label)
        for cid, _group, text, _clean in unicode_cases():
            enc = tok.encode(text, add_special_tokens=False)
            assert decode_all(tok, enc.ids) == text, (label, cid, text)


def test_nbsp_amounts_roundtrip():
    for label in TOKS:
        tok = load_tok(label)
        for text in ("1\u00a0234\u00a0567,89 zł", "1\u202f234\u202f567,89 zł"):
            enc = tok.encode(text, add_special_tokens=False)
            assert decode_all(tok, enc.ids) == text


def test_literal_special_tokens_not_injected_in_recommended_mode():
    for label, path in TOKS.items():
        tok = Tokenizer.from_file(str(path))
        special_ids = {i for i, t in tok.get_added_tokens_decoder().items() if t.special}
        for name in SPECIAL_NAMES + ["<tool_call>", "</tool_call>"]:
            tok.encode_special_tokens = True
            try:
                enc = tok.encode(name, add_special_tokens=False)
            finally:
                tok.encode_special_tokens = False
            assert not (set(enc.ids) & special_ids), (label, name, enc.ids)
            assert decode_all(tok, enc.ids) == name, (label, name)
        # <tool_call> w V0J2 jest zwykłym tokenem, nie ID specjalnym
        tok.encode_special_tokens = True
        try:
            ids = tok.encode("<tool_call>", add_special_tokens=False).ids
        finally:
            tok.encode_special_tokens = False
        assert not (set(ids) & special_ids)


def test_hf_tokenizer_config_has_split_special_tokens():
    for rel in ("hf/tokenizatorex-32k", "hf/variants/V0-32k",
                "hf/variants/V0J2-32k"):
        p = REPO / rel / "tokenizer_config.json"
        cfg = json.loads(p.read_text(encoding="utf-8"))
        assert cfg.get("split_special_tokens") is True, rel


def _fuzz_alphabet():
    chars = list("aąbcćdeęfghijklłmnńoópqrsśtuvwxyzźż"
                 "AĄBCĆDEĘFGHIJKLŁMNŃOÓPQRSŚTUVWXYZŹŻ"
                 "0123456789 .,;:!?-–—…„”\"'()[]{}/\\%+*=<>|_#@&")
    chars += ["\u00a0", "\u202f", "\u00ad", "\u200b", "\ufeff", "\r\n",
              "\t", "€", "§", "°", "²", "✅", "📄", "𝔘"]
    return chars


def test_fuzz_roundtrip_seed_20261124_2000():
    rng = random.Random(20261124)
    alphabet = _fuzz_alphabet()
    texts = ["".join(rng.choice(alphabet) for _ in range(rng.randint(1, 60)))
             for _ in range(2_000)]
    for label in TOKS:
        tok = load_tok(label)
        for text in texts:
            enc = tok.encode(text, add_special_tokens=False)
            assert decode_all(tok, enc.ids) == text


@pytest.mark.xfail(strict=True,
                   reason="znana wada SuperBPE, naprawa w v2.1: token końca słowa "
                          "zjada początek następnego (np. 'ność z')")
def test_known_superword_midword_boundary():
    for label in TOKS:
        tok = load_tok(label)
        found = {text: bad_boundaries(tok, text) for text in KNOWN_SUPERWORDS}
        assert all(not v for v in found.values()), {
            k: v for k, v in found.items() if v}
