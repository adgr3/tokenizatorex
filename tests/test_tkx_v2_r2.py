import json
import os
import subprocess
import sys
from pathlib import Path

from tokenizers import Tokenizer

REPO = Path(__file__).resolve().parents[1]


def load_tok(name):
    return Tokenizer.from_file(str(REPO / "hf" / "variants" / name / "tokenizer.json"))


def test_special_chars_via_encode():
    v3 = load_tok("V3-32k")
    v0 = load_tok("V0-32k")
    # Task requirement: "§" in V3 = 2 tokens
    assert len(v3.encode("§", add_special_tokens=False).ids) == 2
    assert len(v0.encode("§", add_special_tokens=False).ids) == 1
    # Special chars file must be derived from encode==1
    sc = json.load(open(REPO / "results" / "tkx_v2_special_chars.json", encoding="utf-8"))
    for tok_label in ["TKX/V0-32k", "TKX/V3-32k"]:
        row = sc["tokenizers"][tok_label]
        tok = load_tok(tok_label.replace("TKX/", ""))
        for ch, is_single in row.items():
            ids = tok.encode(ch, add_special_tokens=False).ids
            assert (len(ids) == 1) == is_single, (tok_label, ch, ids)


def test_consistency_synthetic_contexts():
    # Test, który może zawieść: mierzymy dwa znane przypadki.
    # 1) "art. 12" skleja się z poprzedzającą spacją w części kontekstów.
    # 2) "123" ma identyczną segmentację we wszystkich prostych kontekstach.
    from tkx_v2.measure import _pattern_segmentation

    v0 = load_tok("V0-32k")
    merged = _pattern_segmentation(
        v0, "art. 12",
        ["art. 12 jest elementem dokumentu.", "tekst art. 12 tekst",
         "(art. 12) opis", "slowo, art. 12 slowo",
         "jeden dwa art. 12 trzy cztery"])
    assert merged["merged_with_prev_count"] >= 1
    assert merged["contexts_identical"] is False
    assert 1 <= merged["contexts_identical_count"] < 5

    same = _pattern_segmentation(v0, "123", ["123", " 123", "123 ", " 123 "])
    assert same["contexts_identical"] is True
    assert same["contexts_identical_count"] == 4


def test_number_gate_injected_bad_number(tmp_path):
    # Copy a report and inject a clearly fake number not in results.
    src = REPO / "RELEASE_NOTES_v2.0.md"
    dst = tmp_path / "RELEASE_NOTES_v2.0.md"
    text = src.read_text(encoding="utf-8")
    dst.write_text(text + "\n\nWstrzyknięta liczba kontrolna: 9876543,21\n", encoding="utf-8")
    # Run gate on this single file
    p = subprocess.run([sys.executable, str(REPO / "scripts" / "sprawdz_liczby_v2.py"), str(dst)],
                       cwd=REPO, capture_output=True, text=True,
                       encoding="utf-8", errors="replace",
                       env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"})
    assert p.returncode != 0, p.stdout + p.stderr


def test_roundtrip_nfc_nfd_v0_v3():
    v0 = load_tok("V0-32k")
    v3 = load_tok("V3-32k")
    nfc_samples = ["Zażółć gęślą jaźń", "Dzień dobry, § 2.", "Pójdźże, kiń tę chmurność"]
    nfd_samples = [__import__("unicodedata").normalize("NFD", s) for s in nfc_samples]

    # Expected result (explicit): V0 preserves NFC and NFD samples byte-for-byte in decode(encode(x)).
    for s in nfc_samples + nfd_samples:
        ids = v0.encode(s, add_special_tokens=False).ids
        assert v0.decode(ids) == s

    # Expected result (explicit): V3 preserves NFC samples, but normalizes NFD->NFC (round-trip differs for NFD).
    for s in nfc_samples:
        ids = v3.encode(s, add_special_tokens=False).ids
        assert v3.decode(ids) == s
    for s, nfc in zip(nfd_samples, nfc_samples):
        ids = v3.encode(s, add_special_tokens=False).ids
        dec = v3.decode(ids)
        assert dec == nfc
        assert dec != s
