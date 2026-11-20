"""Atak 5: koszt V2/V2b/V3 vs V0 na dokumentach R3-extra.

Tokenizer = eksport HF. Tekst zostaje w raw_extra (gitignored).
Do JSON idą tylko liczby, URL-e i SHA-256 z manifestu.
"""
from __future__ import annotations

import json
import os
import sys

from tokenizers import Tokenizer  # HF przed dopisaniem repo

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(ROOT, "audit"))

import numpy as np  # noqa: E402

from common import bootstrap_indices  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw_extra")
HF = os.path.join(ROOT, "hf", "variants")
VARIANTS = ["V0-32k", "V2-32k", "V2b-32k", "V3-32k"]


def load_tok(name: str) -> Tokenizer:
    return Tokenizer.from_file(os.path.join(HF, name, "tokenizer.json"))


def ci_delta(a: np.ndarray, b: np.ndarray, w: np.ndarray) -> dict:
    idx = bootstrap_indices(len(w))
    diff = (b[idx] - a[idx]).sum(1) / w[idx].sum(1)
    point = float((b.sum() - a.sum()) / a.sum()) if a.sum() else None
    fert_a = float(a.sum() / w.sum()) if w.sum() else None
    lo, hi = np.percentile(diff, [2.5, 97.5])
    return {
        "docs": int(len(w)),
        "words": int(w.sum()),
        "tokens_v0": int(a.sum()),
        "tokens": int(b.sum()),
        "delta_pct": point,
        "delta_pct_ci95": [float(lo / fert_a), float(hi / fert_a)] if fert_a else None,
        "fertility_v0": fert_a,
        "fertility": float(b.sum() / w.sum()) if w.sum() else None,
    }


def main() -> None:
    manifest = json.load(open(os.path.join(HERE, "r3_extra_manifest.json"), encoding="utf-8"))
    toks = {name: load_tok(name) for name in VARIANTS}
    rows = []
    for doc in manifest["docs"]:
        path = os.path.join(RAW, doc["id"] + ".json")
        rec = json.load(open(path, encoding="utf-8"))
        text = rec["text"]
        nwords = len(text.split())
        counts = {}
        for name, tok in toks.items():
            counts[name] = len(tok.encode(text, add_special_tokens=False).ids)
        row = {
            "id": doc["id"],
            "source": doc["source"],
            "url": doc["url"],
            "sha256": doc["sha256"],
            "words": nwords,
            "tokens": counts,
        }
        v0 = counts["V0-32k"]
        row["delta_pct"] = {
            name: (counts[name] - v0) / v0 if v0 else None
            for name in VARIANTS if name != "V0-32k"
        }
        rows.append(row)
        print(doc["id"], nwords, {k: counts[k] for k in VARIANTS}, flush=True)

    by_source = {}
    sources = sorted({r["source"] for r in rows})
    groups = {"ALL": rows}
    for src in sources:
        groups[src] = [r for r in rows if r["source"] == src]

    aggregates = {}
    for label, group in groups.items():
        if not group:
            continue
        w = np.array([r["words"] for r in group], dtype=np.float64)
        base = np.array([r["tokens"]["V0-32k"] for r in group], dtype=np.float64)
        aggregates[label] = {}
        for name in VARIANTS:
            if name == "V0-32k":
                aggregates[label][name] = {
                    "docs": int(len(group)),
                    "words": int(w.sum()),
                    "tokens": int(base.sum()),
                    "fertility": float(base.sum() / w.sum()) if w.sum() else None,
                }
                continue
            b = np.array([r["tokens"][name] for r in group], dtype=np.float64)
            aggregates[label][name] = ci_delta(base, b, w)
        order = sorted(
            ("V2-32k", "V2b-32k", "V3-32k"),
            key=lambda n: aggregates[label][n]["delta_pct"],
        )
        aggregates[label]["order_by_delta"] = order

    # mediana dokumentu, żeby jeden długi akt nie był jedyną historią
    medians = {}
    for name in ("V2-32k", "V2b-32k", "V3-32k"):
        vals = [r["delta_pct"][name] for r in rows]
        medians[name] = float(np.median(vals))

    out = {
        "meta": {
            "label": "R3-extra",
            "tokenizer": "hf/variants/*/tokenizer.json",
            "variants": VARIANTS,
            "add_special_tokens": False,
            "words": "text.split() na tekście, który wszedł do enkodera",
            "delta": "(tokens_v - tokens_v0) / tokens_v0",
            "bootstrap": "1000x, seed 20261119, common.bootstrap_indices, pary dokumentów",
            "ci": "percentyl 2.5/97.5 różnicy tokenów/słowo, podzielony przez fertility V0",
            "note": "Tekst lokalny w raw_extra (gitignored). Ten plik nie zawiera treści.",
            "genre_note": "TED to ogłoszenia zamówień (inny host niż ezamowienia). Dziennik mazowiecki i BIP to inne gatunki.",
        },
        "n": len(rows),
        "aggregates": aggregates,
        "median_doc_delta_pct": medians,
        "docs": rows,
    }
    path = os.path.join(HERE, "attack5_extra.json")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("wrote", path, "n", len(rows), flush=True)
    print("ALL", json.dumps(aggregates["ALL"], ensure_ascii=False)[:2000], flush=True)


if __name__ == "__main__":
    main()
