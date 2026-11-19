"""Testy audytu TKX-A (uzupełniają stare 10 testów repo).

Uruchomienie: python -m pytest -q
"""
from __future__ import annotations

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(ROOT, "audit"))

from common import MANIFEST_PATH, RESULTS_DIR, load_superbpe  # noqa: E402

CASES = [
    "1 234 567,89 zł",
    "wartość zamówienia: 2 450 000,00 zł brutto",
    "16 grudnia 2026 r.",
    "16.12.2026 r., godz. 12:00",
    "art. 5 ust. 2 pkt 3 lit. a",
    "Dz.U. z 2024 r. poz. 1320 ze zm.",
    "45233140-2",
    "ZP.271.12.2026",
    "KIO 1234/26",
    "NIP 123-456-32-18",
    "ul. Marszałkowska 140, 00-061 Warszawa",
    "Uchwała Nr XLII/1234/2026 Rady Miasta",
    "wkład własny 10%",
    "sekretariat@urzad.gov.pl",
]
OURS = os.path.join(ROOT, "tokenizers", "tokenizatorex-32k.json")
HF = os.path.join(ROOT, "hf", "tokenizatorex-32k", "tokenizer.json")


def test_h9_hf_package_not_shadowed():
    import tokenizers
    assert hasattr(tokenizers, "Tokenizer")
    assert "site-packages" in tokenizers.__file__ or "dist-packages" in tokenizers.__file__, \
        tokenizers.__file__


@pytest.mark.skipif(not os.path.exists(OURS), reason="brak tokenizera")
def test_roundtrip_appendix_a_ours():
    tok = load_superbpe("tokenizers/tokenizatorex-32k.json")
    for s in CASES:
        assert tok.decode(tok.encode(s)) == s


@pytest.mark.skipif(not os.path.exists(HF), reason="brak eksportu HF")
def test_roundtrip_appendix_a_hf():
    from tokenizers import Tokenizer
    tok = Tokenizer.from_file(HF)
    for s in CASES:
        ids = tok.encode(s, add_special_tokens=False).ids
        assert tok.decode(ids, skip_special_tokens=False) == s


@pytest.mark.skipif(not os.path.exists(HF), reason="brak eksportu HF")
def test_no_special_tokens_in_ordinary_text():
    from tokenizers import Tokenizer
    tok = Tokenizer.from_file(HF)
    specials = set(tok.get_added_tokens_decoder())
    ids = tok.encode("art. 5 ust. 2", add_special_tokens=False).ids
    assert not (set(ids) & specials)


@pytest.mark.skipif(not os.path.exists(MANIFEST_PATH), reason="brak manifestu korpusu")
def test_manifest_split_no_leak():
    m = json.load(open(MANIFEST_PATH, encoding="utf-8"))
    by_domain = {}
    for d in m["documents"]:
        by_domain.setdefault(d["domain"], []).append(d)
    for dom, docs in by_domain.items():
        ids = [d["id"] for d in docs]
        assert len(ids) == len(set(ids)), dom
        dev = sum(1 for d in docs if d["split"] == "dev")
        share = dev / len(docs)
        assert 0.30 <= share <= 0.50, (dom, share)
        for d in docs:
            assert d["sha256"] and len(d["sha256"]) == 64
            assert d["words"] >= 50
            assert d["split"] in ("dev", "test")


def test_tokenizer_manifest_slayer_sha():
    path = os.path.join(RESULTS_DIR, "tokenizers_manifest.json")
    if not os.path.exists(path):
        pytest.skip("brak manifestu tokenizerów")
    m = json.load(open(path, encoding="utf-8"))
    rows = {r["label"]: r for r in m["tokenizers"]}
    assert rows["Slayer1B"]["sha256"] == \
        "0640d3bd3674d7a6e59c540d945a2ad275a12e1bcaeb6007c37a90751f9815dd"


def test_appendix_a_token_counts_match_recon_order():
    """Liczby z rekonesansu są tylko orientacyjne — sprawdzamy rząd wielkości."""
    tok = load_superbpe("tokenizers/tokenizatorex-32k.json")
    assert len(tok.encode("1 234 567,89 zł")) <= 10
    assert len(tok.encode("art. 5 ust. 2 pkt 3 lit. a")) <= 14
    assert len(tok.encode("45233140-2")) <= 8


def test_manifest_domains_cover_requirements():
    if not os.path.exists(MANIFEST_PATH):
        pytest.skip("brak manifestu korpusu")
    m = json.load(open(MANIFEST_PATH, encoding="utf-8"))
    for dom in ("przetargi_ogloszenia", "przetargi_kio", "samorzad_uchwaly",
                "granty_ogloszenia", "prawo_eli", "ocr_prasa", "tabele_json"):
        assert dom in m["domains"], dom
        assert m["domains"][dom]["test_docs"] > 0
    assert m["domains"]["ocr_prasa"]["words"] >= 50_000
    for dom in ("przetargi_ogloszenia", "przetargi_kio", "samorzad_uchwaly",
                "granty_ogloszenia", "prawo_eli"):
        assert m["domains"][dom]["share_2026"] >= 0.5, dom
