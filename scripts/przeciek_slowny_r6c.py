"""R6c: przeciek dokumentów testowych do korpusu treningowego tokenizera.

Miara główna: 13-gramy SŁOWNE — normalizacja NFC, lowercase, `split()`,
13 kolejnych słów; mianownik = unikalne 13-gramy dokumentu. Próg zapisany
przed pomiarem: dokument = przeciek, gdy > 50% unikalnych 13-gramów słownych
jest w korpusie treningowym albo cały znormalizowany dokument jest dokładnym
podciągiem. Dodatkowo raportujemy odsetek dokumentów > 5%.

Kalibracja: ta sama miara na dokumentach opublikowanych PO dacie korpusu
HPLT p2 (`added = 2026-07-14`), czyli na pewno niewidzianych.

Miara znakowa z R6 (`results/tkx_v2_r6_leak.json`) zostaje jako dodatek:
13 znaków to około 2 słowa, więc mierzy wspólną polszczyznę, nie kopiowanie
dokumentów.

Korpus: `audit/tmp/stability_train.txt` (HPLT p2, 400 MB), odtworzony z
`audit/stability.py`; SHA-256 b0e7447c… zgodny z manifestem v21.

Wynik: results/tkx_v2_r6c_slowny_przeciek.json
"""
from __future__ import annotations

import hashlib
import json
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
CORPUS_DATE = "2026-07-14"
BASE = np.uint64(1000003)
KER = np.array([pow(int(BASE), N - 1 - k, 2 ** 64) for k in range(N)],
               dtype=np.uint64)


def norm(t: str) -> str:
    t = unicodedata.normalize("NFC", t)
    return t.replace("\r\n", "\n").replace("\r", "\n").strip()


def word_hashes(t: str) -> np.ndarray:
    """Hasze wszystkich 13-gramów słownych (NFC, lowercase, split())."""
    words = norm(t).lower().split()
    if len(words) < N:
        return np.empty(0, dtype=np.uint64)
    ids = np.fromiter((hash(w) for w in words), dtype=np.int64, count=len(words))
    return np.convolve(ids.view(np.uint64), KER, mode="valid")


def load_jsonl(path: Path):
    return [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]


def load_audit(domain: str):
    out = []
    for p in sorted((AUDIT_RAW / domain).glob("*.json")):
        d = json.load(open(p, encoding="utf-8"))
        if d.get("split") == "test":
            out.append(d)
    return out


def date_of(obj) -> str:
    for k in ("publicationDate", "date"):
        v = obj.get(k)
        if v:
            return str(v)[:10]
    return ""


def stats(rows):
    n = len(rows)
    over = sum(1 for r in rows if r["coverage"] > THRESHOLD)
    exact = sum(1 for r in rows if r["exact"])
    return {
        "docs": n,
        "mean_coverage": sum(r["coverage"] for r in rows) / n if n else 0.0,
        "max_coverage": max((r["coverage"] for r in rows), default=0.0),
        "docs_over_threshold": over,
        "docs_over_threshold_pct": 100.0 * over / n if n else 0.0,
        "exact_matches": exact,
        "exact_pct": 100.0 * exact / n if n else 0.0,
        "leak": bool(over or exact),
    }


def main() -> None:
    t0 = time.time()
    if not TRAIN.is_file():
        raise SystemExit(f"BLOKER: brak korpusu {TRAIN}")
    h = hashlib.sha256()
    with open(TRAIN, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    sha = h.hexdigest()
    if sha != TRAIN_SHA:
        raise SystemExit(f"BLOKER: SHA {sha} != {TRAIN_SHA}")
    print("korpus OK", TRAIN.stat().st_size, "SHA", sha, flush=True)

    train_text = TRAIN.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n").strip()
    train_hashes = set(json.loads(TRAIN_HASHES.read_text(encoding="utf-8")))
    print("trening znaków", len(train_text), flush=True)
    train_words = train_text.lower().split()
    print("trening słów", len(train_words), "czas", round(time.time() - t0, 1), flush=True)
    train_ids = np.fromiter((hash(w) for w in train_words), dtype=np.int64,
                            count=len(train_words)).view(np.uint64)
    del train_words
    train_h = np.convolve(train_ids, KER, mode="valid")
    del train_ids
    train_h = np.unique(train_h)
    print("unikalne 13-gramy słowne treningu", len(train_h),
          "czas", round(time.time() - t0, 1), flush=True)

    sources = {
        "1_bzp": load_jsonl(SPEC1 / "test.jsonl"),
        "2_du_eli": load_audit("prawo_eli"),
        "3_kio": load_audit("przetargi_kio"),
        "4_samorzad": load_audit("samorzad_uchwaly"),
        "5_granty": load_audit("granty_ogloszenia"),
        "6_json_narzedzia": [{"text": o.get("text") or json.dumps(o, ensure_ascii=False)}
                             for o in load_jsonl(TC1)],
        "7_ogolny": load_audit("web"),
        "json_bzp_tabele": load_audit("tabele_json"),
        "granty_149": load_jsonl(SPEC1 / "zbiorB.jsonl"),
        "json_heldout": [{"text": o["text"]} for o in load_jsonl(JSON_HELDOUT)],
    }

    out = {
        "meta": {
            "script": "scripts/przeciek_slowny_r6c.py",
            "train_file": str(TRAIN),
            "train_sha256": sha,
            "train_bytes": TRAIN.stat().st_size,
            "train_chars": len(train_text),
            "train_mb": 400,
            "train_docs": 159868,
            "corpus_added_min": CORPUS_DATE,
            "corpus_added_max": CORPUS_DATE,
            "n": N,
            "unit": "słowa",
            "normalization": "NFC, lowercase, split()",
            "threshold": THRESHOLD,
            "threshold_pct": 50,
            "warn_pct": WARN_PCT,
            "definition": "dokument = przeciek, gdy >50% unikalnych 13-gramów słownych "
                          "jest w korpusie treningowym albo cały znormalizowany dokument "
                          "jest dokładnym podciągiem; mianownik = unikalne 13-gramy dokumentu",
            "corpus_date": CORPUS_DATE,
            "corpus_date_source": "HPLT p2, kolumna `added` = 2026-07-14 dla wszystkich "
                                  "159868 dokumentów próbki treningowej",
            "calibration_definition": "ta sama miara na dokumentach z datą publikacji "
                                      "> 2026-07-14 (na pewno poza korpusem)",
            "char_addendum": "wynik 13-gramów znakowych z R6 jest w "
                             "results/tkx_v2_r6_leak.json; 13 znaków ≈ 2 słowa, "
                             "więc mierzy wspólną polszczyznę/szablony, nie kopie",
        },
        "sources": {},
        "control": {},
    }

    all_control_rows = []
    for sid, objs in sources.items():
        rows = []
        for i, o in enumerate(objs):
            text = o["text"]
            gh = np.unique(word_hashes(text))
            if len(gh):
                pos = np.searchsorted(train_h, gh)
                pos = np.minimum(pos, len(train_h) - 1)
                hit = float((train_h[pos] == gh).sum()) / len(gh)
            else:
                hit = 0.0
            exact = (hashlib.sha256(norm(text).encode("utf-8")).hexdigest()
                     in train_hashes)
            rows.append({"doc": i, "chars": len(text), "date": date_of(o),
                         "coverage": hit, "exact": exact})
        st = stats(rows)
        st["rows"] = rows
        st["dates"] = {
            "min": min((r["date"] for r in rows if r["date"]), default=""),
            "max": max((r["date"] for r in rows if r["date"]), default=""),
            "with_date": sum(1 for r in rows if r["date"]),
            "after_corpus": sum(1 for r in rows if r["date"] and r["date"] > CORPUS_DATE),
        }
        out["sources"][sid] = st
        after = [r for r in rows if r["date"] and r["date"] > CORPUS_DATE]
        if after:
            out["control"][sid] = stats(after)
            all_control_rows.extend(after)
        print(f"  {sid}: {st['docs']} dok., >50% {st['docs_over_threshold']}, "
              f"exact {st['exact_matches']}, max {st['max_coverage']:.1%}, "
              f"po dacie {len(after)}", flush=True)

    out["control"]["all"] = stats(all_control_rows)
    out["control"]["all"]["note"] = ("Zbiorczy zbiór kontrolny: dokumenty z datą "
                                     f"> {CORPUS_DATE} (BZP, KIO, granty 149, Dz.U., "
                                     "samorząd — tylko te źródła mają daty).")

    with open(RESULTS / "tkx_v2_r6c_slowny_przeciek.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("zapisano results/tkx_v2_r6c_slowny_przeciek.json, czas",
          round(time.time() - t0, 1))
    print("kontrola ALL:", {k: out["control"]["all"][k] for k in
                            ("docs", "docs_over_threshold", "docs_over_threshold_pct",
                             "exact_matches", "max_coverage")})


if __name__ == "__main__":
    main()
