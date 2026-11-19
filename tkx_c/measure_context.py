"""Długość pełnych dokumentów a okno 2048/4096 (kanoniczny HF)."""
from __future__ import annotations

import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from measure_lib import VARIANTS, hf_encode, load_hf  # noqa: E402

RES = os.path.join(ROOT, "tkx_c", "results")
DATA = os.path.join(ROOT, "tkx_c", "data", "full_docs.json")


def main() -> None:
    data = json.load(open(DATA, encoding="utf-8"))
    docs = data["documents"]
    toks = {v: load_hf(v) for v in VARIANTS}
    out = {"meta": {"source": "tkx_c/data/full_docs.json",
                    "note": "świeża próbka pełnych dokumentów z tych samych źródeł; nie test TKX-A",
                    "docs": len(docs)},
           "domains": {}}
    for dom in ("przetargi_ogloszenia", "przetargi_kio", "granty_ogloszenia",
                "samorzad_uchwaly"):
        ds = [d for d in docs if d["domain"] == dom]
        row = {"docs": len(ds), "variants": {}}
        for v, tok in toks.items():
            counts = np.array([len(hf_encode(tok, d["text"])) for d in ds], dtype=float)
            row["variants"][v] = {
                "median": float(np.median(counts)),
                "p90": float(np.percentile(counts, 90)),
                "mean": float(counts.mean()),
                "max": int(counts.max()),
                "fit_2048": float((counts <= 2048).mean()),
                "fit_4096": float((counts <= 4096).mean()),
            }
        out["domains"][dom] = row
        print(dom, {v: round(row["variants"][v]["median"]) for v in ("V0-32k", "V1-32k", "V2-32k")})
    with open(os.path.join(RES, "context.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
        f.write("\n")


if __name__ == "__main__":
    main()
