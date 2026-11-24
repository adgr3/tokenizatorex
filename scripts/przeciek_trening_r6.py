"""R6: przeciek dokumentów testowych do korpusu treningowego tokenizera.

Korpus treningowy: `audit/tmp/stability_train.txt` (HPLT p2, 400 MB) odtworzony
deterministycznie z `audit/stability.py` (scan_parquet(...).head(200_000), pisz do
400 MB). Kontrola: SHA-256 = b0e7447cf94f8e0fa03edfeb3f6f10a2e63c9e32037f086cf5a434709ae6e558
(zgodny z tkx_v21/MANIFEST_DANYCH.json). Skrypt nie zapisuje korpusu do repo.

Próg zapisany przed pomiarem: dokument uznajemy za przeciek, gdy > 50% jego
unikalnych 13-gramów znakowych występuje w korpusie treningowym albo gdy cały
znormalizowany dokument jest jego dokładnym podciągiem. Dodatkowo raportujemy
odsetek dokumentów > 5% (próg zastrzeżenia przy tezie).

13-gramy liczone są na punktach kodowych Unicode (UTF-32) i haszowane splotem
wielomianowym mod 2^64 (kolizje pomijalne); to ta sama definicja „13 znaków”,
co wersja tekstowa, tylko szybciej.

Wynik: results/tkx_v2_r6_leak.json
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import unicodedata
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "results"
TRAIN = Path(r"D:\VPS\cache\tkx_r6\stability_train.txt")
TRAIN_HASHES = Path(r"D:\VPS\cache\tkx_r6\train_doc_sha256.json")
TRAIN_SHA = "b0e7447cf94f8e0fa03edfeb3f6f10a2e63c9e32037f086cf5a434709ae6e558"
SPEC1 = Path(r"D:\VPS\fabryka\spec1\data")
TC1 = Path(r"D:\VPS\fabryka\tc1\dane\test.jsonl")
JSON_HELDOUT = Path(r"D:\VPS\fabryka\tkx-json\tkx_v21\dane\json_generic_heldout_test.jsonl")
AUDIT_RAW = REPO / "audit" / "data" / "raw"
N = 13
THRESHOLD = 0.5
WARN_PCT = 5.0
sys.path.insert(0, str(REPO))

from tokenizers import Tokenizer  # noqa: E402

BASE = np.uint64(1000003)
KER = np.array([pow(int(BASE), N - 1 - k, 2 ** 64) for k in range(N)],
               dtype=np.uint64)


def norm(t: str) -> str:
    t = unicodedata.normalize("NFC", t)
    return t.replace("\r\n", "\n").replace("\r", "\n").strip()


def gram_hashes(t: str) -> np.ndarray:
    """Hasze wszystkich 13-gramów punktów kodowych (mod 2^64)."""
    code = np.frombuffer(t.encode("utf-32-le"), dtype="<u4").astype(np.uint64)
    if len(code) < N:
        return np.empty(0, dtype=np.uint64)
    return np.convolve(code, KER, mode="valid")


def load_jsonl(path: Path):
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            o = json.loads(line)
            t = o.get("text")
            if t is None:
                t = json.dumps(o, ensure_ascii=False)
            out.append(t)
    return out


def load_audit(domain: str):
    out = []
    for p in sorted((AUDIT_RAW / domain).glob("*.json")):
        d = json.load(open(p, encoding="utf-8"))
        if d.get("split") == "test":
            out.append(d["text"])
    return out


def measure_fertility(docs, tok):
    t = sum(len(tok.encode(x, add_special_tokens=False).ids) for x in docs)
    w = sum(len(x.split()) for x in docs)
    return t / w if w else float("nan"), t, w


def main() -> None:
    t0 = time.time()
    if not TRAIN.is_file():
        raise SystemExit(f"BLOKER: brak korpusu treningowego {TRAIN}")
    h = hashlib.sha256()
    with open(TRAIN, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    sha = h.hexdigest()
    if sha != TRAIN_SHA:
        raise SystemExit(f"BLOKER: SHA korpusu {sha} != {TRAIN_SHA}")
    print("korpus treningowy OK", TRAIN.stat().st_size, "SHA", sha, flush=True)

    # HPLT p2 jest już NFC (PROTOKOL_TKX_C §9.5); pełna normalizacja 400 MB
    # przez unicodedata.normalize jest patologicznie wolna na tym tekście, a jej
    # wynik byłby identyczny. Dokumenty testowe normalizujemy normalnie.
    train_norm = (TRAIN.read_text(encoding="utf-8")
                  .replace("\r\n", "\n").replace("\r", "\n").strip())
    train_hashes = set(json.loads(TRAIN_HASHES.read_text(encoding="utf-8")))
    print("wczytano trening", len(train_norm), "znaków; hashe dokumentów",
          len(train_hashes), flush=True)

    sources = {
        "1_bzp": load_jsonl(SPEC1 / "test.jsonl"),
        "2_du_eli": load_audit("prawo_eli"),
        "3_kio": load_audit("przetargi_kio"),
        "4_samorzad": load_audit("samorzad_uchwaly"),
        "5_granty": load_audit("granty_ogloszenia"),
        "6_json_narzedzia": load_jsonl(TC1),
        "7_ogolny": load_audit("web"),
        "json_bzp_tabele": load_audit("tabele_json"),
        "granty_149": load_jsonl(SPEC1 / "zbiorB.jsonl"),
        "json_heldout": load_jsonl(JSON_HELDOUT),
    }

    doc_hashes = {}
    parts = []
    for sid, docs in sources.items():
        for i, d in enumerate(docs):
            gh = np.unique(gram_hashes(norm(d)))
            doc_hashes[(sid, i)] = gh
            if len(gh):
                parts.append(gh)
    test_all = np.unique(np.concatenate(parts)) if parts else np.empty(0, np.uint64)
    print("dokumentów", sum(len(v) for v in sources.values()),
          "unikalnych 13-gramów testu", len(test_all), flush=True)

    found_parts = []
    n = len(train_norm)
    step = 25_000_000
    for start in range(0, max(1, n - N + 1), step):
        end = min(start + step + N - 1, n)
        gh = gram_hashes(train_norm[start:end])
        pos = np.searchsorted(test_all, gh)
        pos = np.minimum(pos, len(test_all) - 1)
        match = test_all[pos] == gh
        if match.any():
            found_parts.append(gh[match])
        print("  skan", min(end, n), "/", n, flush=True)
    found = (np.unique(np.concatenate(found_parts)) if found_parts
             else np.empty(0, np.uint64))
    print("znalezione 13-gramy", len(found), "czas", round(time.time() - t0, 1),
          flush=True)

    out = {
        "meta": {
            "script": "scripts/przeciek_trening_r6.py",
            "train_file": str(TRAIN),
            "train_sha256": sha,
            "train_bytes": TRAIN.stat().st_size,
            "train_chars": len(train_norm),
            "train_mb": 400,
            "train_docs": len(train_hashes),
            "n": N,
            "threshold": THRESHOLD,
            "threshold_pct": 50,
            "warn_pct": WARN_PCT,
            "gram_hash": "wielomian mod 2^64 na punktach kodowych UTF-32",
            "train_nfc": "HPLT p2 jest już NFC (PROTOKOL_TKX_C §9.5); bez pełnej "
                         "normalizacji 400 MB (wynik identyczny, a unicodedata.normalize "
                         "na tym tekście jest bardzo wolna)",
            "definition": "dokument = przeciek, gdy >50% unikalnych 13-gramów znakowych "
                          "jest w korpusie treningowym albo cały dokument jest dokładnym "
                          "podciągiem; dokumenty testowe normalizowane NFC, CRLF->LF, strip; "
                          "mianownik = unikalne 13-gramy dokumentu",
            "source": "korpus odtworzony z audit/stability.py (HPLT p2, head 200k, 400 MB)",
        },
        "sources": {},
    }
    for sid, docs in sources.items():
        rows = []
        for i, d in enumerate(docs):
            gh = doc_hashes[(sid, i)]
            if len(gh):
                pos = np.searchsorted(found, gh)
                pos = np.minimum(pos, len(found) - 1)
                hit = float((found[pos] == gh).sum()) / len(gh)
            else:
                hit = 0.0
            exact = (hashlib.sha256(norm(d).encode("utf-8")).hexdigest()
                     in train_hashes)
            rows.append({"doc": i, "chars": len(d), "coverage": hit, "exact": exact})
        n_docs = len(rows)
        over = sum(1 for r in rows if r["coverage"] > THRESHOLD)
        exact_n = sum(1 for r in rows if r["exact"])
        out["sources"][sid] = {
            "docs": n_docs,
            "mean_coverage": sum(r["coverage"] for r in rows) / n_docs if n_docs else 0.0,
            "max_coverage": max((r["coverage"] for r in rows), default=0.0),
            "docs_over_threshold": over,
            "docs_over_threshold_pct": 100.0 * over / n_docs if n_docs else 0.0,
            "exact_matches": exact_n,
            "exact_pct": 100.0 * exact_n / n_docs if n_docs else 0.0,
            "leak": bool(over or exact_n),
            "rows": rows,
        }
        print(f"  {sid}: {n_docs} dok., >50% {over}, exact {exact_n}, "
              f"max {out['sources'][sid]['max_coverage']:.1%}", flush=True)

    toks = {
        "V0-32k": Tokenizer.from_file(str(REPO / "hf/variants/V0-32k/tokenizer.json")),
        "V0J2-32k": Tokenizer.from_file(str(REPO / "hf/variants/V0J2-32k/tokenizer.json")),
    }
    clean = {}
    for sid, docs in sources.items():
        rows = out["sources"][sid]["rows"]
        keep = [d for d, r in zip(docs, rows)
                if r["coverage"] <= THRESHOLD and not r["exact"]]
        if len(keep) == len(docs):
            continue
        clean[sid] = {"docs_total": len(docs), "docs_clean": len(keep), "tokenizers": {}}
        for tname, tok in toks.items():
            f, t, w = measure_fertility(keep, tok)
            clean[sid]["tokenizers"][tname] = {
                "fertility": f, "tokens": t, "words": w,
            }
        print(f"  czysty podzbiór {sid}: {len(keep)}/{len(docs)} dok. -> "
              f"V0 {clean[sid]['tokenizers']['V0-32k']['fertility']:.3f}", flush=True)
    out["clean_subset"] = clean

    with open(RESULTS / "tkx_v2_r6_leak.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("zapisano results/tkx_v2_r6_leak.json, czas", round(time.time() - t0, 1))


if __name__ == "__main__":
    main()
