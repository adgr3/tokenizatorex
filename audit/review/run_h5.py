"""R2 #3: H5 NFD. Do 25 pierwszych dokumentow TEST (sort po id) na dziedzinę,
text -> unicodedata.normalize('NFD', text); wzrost = suma tokenow wariantu /
suma tokenow baseline - 1. Bez normalizacji baseline.
"""
from __future__ import annotations

import unicodedata

import r2lib


def main() -> None:
    toks = r2lib.get_tokenizers()
    out = {
        "definition": "per domain first 25 test docs sorted by id; NFD = "
        "unicodedata.normalize('NFD', text) on whole text; increase = "
        "sum(variant_tokens)/sum(baseline_tokens) - 1",
        "per_domain": {},
        "total": {},
    }
    totals = {label: {"baseline": 0, "nfd": 0} for label in toks}
    for dom in r2lib.OFFICIAL7:
        docs = r2lib.load_docs(dom)[:25]
        entry = {"docs": len(docs), "ids": [d["id"] for d in docs], "tokenizers": {}}
        for label, tok in toks.items():
            base = sum(r2lib.n_tokens(tok, d["text"]) for d in docs)
            nfd = sum(r2lib.n_tokens(tok, unicodedata.normalize("NFD", d["text"])) for d in docs)
            entry["tokenizers"][label] = {
                "baseline_tokens": base,
                "nfd_tokens": nfd,
                "relative_increase": nfd / base - 1,
            }
            totals[label]["baseline"] += base
            totals[label]["nfd"] += nfd
        out["per_domain"][dom] = entry
        print(dom, "docs", len(docs))
        for label, v in entry["tokenizers"].items():
            print(f"  {label:18s} base={v['baseline_tokens']:8d} nfd={v['nfd_tokens']:8d} +{v['relative_increase']*100:.3f}%")
    for label in toks:
        t = totals[label]
        out["total"][label] = {
            "baseline_tokens": t["baseline"],
            "nfd_tokens": t["nfd"],
            "relative_increase": t["nfd"] / t["baseline"] - 1,
        }
        print(f"TOTAL {label:18s} +{out['total'][label]['relative_increase']*100:.3f}%")
    path = r2lib.write_json("r2_h5_nfd.json", out)
    print("WROTE", path)


if __name__ == "__main__":
    main()
