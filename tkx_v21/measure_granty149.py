"""Granty 149: większy zbiór ogłoszeń grantowych (spec1/zbiorB.jsonl).

Tylko odczyt danych; do repo trafiają wyłącznie liczby.
  python tkx_v21/measure_granty149.py
"""
from __future__ import annotations

import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from tkx_v21.measure_v21 import load_tokenizers, measure_source  # noqa: E402

SRC = r"D:\VPS\fabryka\spec1\data\zbiorB.jsonl"
OUT = os.path.join(REPO, "results", "tkx_v21_granty149.json")


def main():
    docs = []
    with open(SRC, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            t = json.loads(line).get("text")
            if t:
                docs.append(t)
    toks = load_tokenizers()
    out = {
        "source": SRC,
        "docs": len(docs),
        "words": sum(len(d.split()) for d in docs),
        "bytes": sum(len(d.encode("utf-8")) for d in docs),
        "seed": 20261123,
        "method": "suma tokenow / suma slow (str.split), bootstrap 1000x po dokumentach",
        "tokenizers": {},
    }
    for label, tok in toks.items():
        row = measure_source(tok, docs)
        out["tokenizers"][label] = {k: v for k, v in row.items() if not k.startswith("_")}
    base = out["tokenizers"].get("V0R-32k")
    if base:
        for label, row in out["tokenizers"].items():
            row["delta_vs_v0r_pct"] = (row["fertility"] / base["fertility"] - 1) * 100
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"{len(docs)} dok., {out['words']} slow, {out['bytes']} B")
    for label, row in out["tokenizers"].items():
        print(f"{label:14s} {row['fertility']:.4f} "
              f"[{row['ci'][0]:.4f}-{row['ci'][1]:.4f}] "
              f"{row.get('delta_vs_v0r_pct', 0):+.2f}%")


if __name__ == "__main__":
    main()
