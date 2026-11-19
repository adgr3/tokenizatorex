"""NFD vs NFC dla wariantów (kanoniczny HF)."""
from __future__ import annotations

import json
import os
import sys
import unicodedata

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(ROOT, "audit"))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common import bootstrap_indices  # noqa: E402
from measure_lib import OFFICIAL, VARIANTS, docs, hf_encode, load_hf  # noqa: E402

RES = os.path.join(ROOT, "tkx_c", "results")


def main() -> None:
    toks = {v: load_hf(v) for v in ("V0-32k", "V1-32k", "V2-32k")}
    out = {"meta": {"split": "test", "comparison": "NFD vs NFC", "bootstrap_n": 1000,
                    "seed": 20261119}, "domains": {}, "official": {}}
    for d in OFFICIAL:
        docs_ = docs(d)
        rows = {v: {"nfc": [], "nfd": []} for v in toks}
        for doc in docs_:
            text = doc["text"]
            nfc = unicodedata.normalize("NFC", text)
            nfd = unicodedata.normalize("NFD", text)
            for v, tok in toks.items():
                rows[v]["nfc"].append(len(hf_encode(tok, nfc)))
                rows[v]["nfd"].append(len(hf_encode(tok, nfd)))
        row = {"docs": len(docs_), "variants": {}}
        for v in toks:
            a = np.array(rows[v]["nfc"], dtype=float)
            b = np.array(rows[v]["nfd"], dtype=float)
            idx = bootstrap_indices(len(a))
            rep = (b[idx].sum(1) - a[idx].sum(1)) / a[idx].sum(1)
            row["variants"][v] = {
                "tokens_nfc": int(a.sum()), "tokens_nfd": int(b.sum()),
                "increase": float((b.sum() - a.sum()) / a.sum()),
                "increase_ci": [float(np.percentile(rep, 2.5)),
                                float(np.percentile(rep, 97.5))],
            }
        out["domains"][d] = row
    for label, doms in (("official", OFFICIAL),):
        rows = {v: {"nfc": [], "nfd": []} for v in toks}
        for d in doms:
            for doc in docs(d):
                nfc = unicodedata.normalize("NFC", doc["text"])
                nfd = unicodedata.normalize("NFD", doc["text"])
                for v, tok in toks.items():
                    rows[v]["nfc"].append(len(hf_encode(tok, nfc)))
                    rows[v]["nfd"].append(len(hf_encode(tok, nfd)))
        row = {"variants": {}}
        for v in toks:
            a = np.array(rows[v]["nfc"], dtype=float)
            b = np.array(rows[v]["nfd"], dtype=float)
            idx = bootstrap_indices(len(a))
            rep = (b[idx].sum(1) - a[idx].sum(1)) / a[idx].sum(1)
            row["variants"][v] = {
                "tokens_nfc": int(a.sum()), "tokens_nfd": int(b.sum()),
                "increase": float((b.sum() - a.sum()) / a.sum()),
                "increase_ci": [float(np.percentile(rep, 2.5)),
                                float(np.percentile(rep, 97.5))],
            }
        out[label] = row
    with open(os.path.join(RES, "nfd.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
        f.write("\n")
    for v, r in out["official"]["variants"].items():
        print(v, f"{r['increase']:+.1%}", [round(x, 4) for x in r["increase_ci"]])


if __name__ == "__main__":
    main()
