"""R3 task 4: absolute token counts in a 2048-token context.

Domains: przetargi_ogloszenia and granty_ogloszenia (TEST).
Additional "typical SWZ" proxy: the longest 25% of przetargi_ogloszenia
documents (measured in str.split words).  This is an explicit PROXY, not a real
SWZ / ToR document set.
"""
from __future__ import annotations

import os
import sys

sys.dont_write_bytecode = True
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import numpy as np  # noqa: E402

import rtlib as R  # noqa: E402

CONTEXT = 2048


def summarize(counts: list[int]) -> dict:
    a = np.asarray(counts, dtype=float)
    return {
        "docs": int(a.size),
        "tokens_total": int(a.sum()),
        "mean": float(a.mean()),
        "median": float(np.median(a)),
        "p90": float(np.percentile(a, 90)),
        "p95": float(np.percentile(a, 95)),
        "min": int(a.min()),
        "max": int(a.max()),
        "share_fit_2048": float((a <= CONTEXT).mean()),
        "docs_fit_2048": int((a <= CONTEXT).sum()),
        "docs_over_2048": int((a > CONTEXT).sum()),
        "avg_docs_per_2048": CONTEXT / float(a.mean()),
        "truncated_token_share": float(np.clip(a - CONTEXT, 0, None).sum() / a.sum()),
    }


def main() -> None:
    tokenizers = R.get_tokenizers(R.LABELS)
    domains = ["przetargi_ogloszenia", "granty_ogloszenia"]
    docs_by_dom = R.load_domain_docs(domains)
    counts = {}
    for dom in domains:
        counts[dom] = {lab: [] for lab in tokenizers}
        for d in docs_by_dom[dom]:
            for lab, tok in tokenizers.items():
                counts[dom][lab].append(R.n_tokens(tok, d["text"]))

    # SWZ proxy: longest 25% of przetargi_ogloszenia by word count
    prz = docs_by_dom["przetargi_ogloszenia"]
    order = sorted(range(len(prz)), key=lambda i: R.words_split(prz[i]["text"]), reverse=True)
    k = max(1, int(round(0.25 * len(prz))))
    idx = order[:k]
    proxy = {lab: [] for lab in tokenizers}
    for i in idx:
        for lab, tok in tokenizers.items():
            proxy[lab].append(R.n_tokens(tok, prz[i]["text"]))

    out = {
        "meta": {"split": "test", "context_tokens": CONTEXT, "domains": domains,
                 "swz_proxy": "longest 25% of przetargi_ogloszenia TEST docs by str.split words; PROXY, not real SWZ",
                 "swz_proxy_docs": k},
        "domains": {}, "swz_proxy": {},
    }
    for dom in domains:
        out["domains"][dom] = {
            "docs": len(docs_by_dom[dom]),
            "words": sum(R.words_split(d["text"]) for d in docs_by_dom[dom]),
            "tokenizers": {lab: summarize(counts[dom][lab]) for lab in tokenizers},
        }
    out["swz_proxy"] = {
        "docs": k,
        "words": sum(R.words_split(prz[i]["text"]) for i in idx),
        "tokenizers": {lab: summarize(proxy[lab]) for lab in tokenizers},
        "doc_ids": [prz[i]["id"] for i in idx],
    }
    path = R.write_json("r3_context2048.json", out)
    print("saved", path)

    def show(title, table):
        print(f"\n=== {title} ===")
        print(f"{'tokenizer':<18} {'n':>4} {'mean':>7} {'median':>7} {'p90':>7} "
              f"{'p95':>7} {'max':>7} {'fit2048':>8} {'docs/2048':>9}")
        for lab, s in table.items():
            print(f"{lab:<18} {s['docs']:>4} {s['mean']:>7.1f} {s['median']:>7.1f} "
                  f"{s['p90']:>7.1f} {s['p95']:>7.1f} {s['max']:>7} "
                  f"{100*s['share_fit_2048']:>7.1f}% {s['avg_docs_per_2048']:>9.3f}")

    for dom in domains:
        show(f"{dom} ({out['domains'][dom]['docs']} docs, {out['domains'][dom]['words']} words)",
             out["domains"][dom]["tokenizers"])
    show(f"SWZ proxy: longest 25% przetargi ({k} docs, {out['swz_proxy']['words']} words)",
         out["swz_proxy"]["tokenizers"])


if __name__ == "__main__":
    main()
