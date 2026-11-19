"""H3/H4 dla wariantów: ten sam zapis w 7 kontekstach (kanoniczny HF)."""
from __future__ import annotations

import json
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(ROOT, "audit"))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from measure_lib import DOMAINS, OFFICIAL, load_hf, docs  # noqa: E402
from notation_patterns import ABBREVIATIONS, PATTERNS, extract  # noqa: E402
from consistency import abbr_contexts, contexts, span_signature  # noqa: E402

RES = os.path.join(ROOT, "tkx_c", "results")
VARIANTS = ["V0-32k", "V1-32k", "V2-32k"]
MAX_STRINGS = 100


class Adapter:
    def __init__(self, tok):
        self.tok = tok

    def ids(self, text):
        return self.tok.encode(text, add_special_tokens=False).ids

    def decode(self, ids):
        return self.tok.decode(ids, skip_special_tokens=False)


def analyse(adapter, strings, ctx_fn):
    total = diff = 0
    examples = []
    for s in strings:
        sigs = {}
        for name, ctx in ctx_fn(s).items():
            sig = span_signature(adapter, ctx, s)
            if sig is not None:
                sigs[name] = sig
        if not sigs:
            continue
        c = Counter(sigs.values())
        best, n = c.most_common(1)[0]
        total += len(sigs)
        diff += len(sigs) - n
        if len(c) > 1 and len(examples) < 3:
            examples.append({"string": s, "variants": len(c)})
    return {"pairs": total, "share_other": diff / total if total else None,
            "examples": examples}


def main() -> None:
    out = {"meta": {"split": "test", "max_strings": MAX_STRINGS,
                    "variants": VARIANTS}, "categories": {}, "abbreviations": {}}
    samples = {}
    for cat in PATTERNS:
        found = []
        for dom in OFFICIAL + ["web"]:
            for d in docs(dom):
                for s in extract(d["text"], cat, 500):
                    s = s.strip()
                    if 2 <= len(s) <= 60 and "\n" not in s and "\t" not in s:
                        found.append(s)
                if len(found) > 3000:
                    break
        samples[cat] = sorted(set(found))[:MAX_STRINGS]
        print(cat, len(samples[cat]))

    toks = {v: Adapter(load_hf(v)) for v in VARIANTS}
    for cat, strings in samples.items():
        out["categories"][cat] = {v: analyse(toks[v], strings, contexts)
                                  for v in VARIANTS}
    for a in ABBREVIATIONS:
        out["abbreviations"][a] = {v: analyse(toks[v], [a], abbr_contexts)
                                   for v in VARIANTS}
    with open(os.path.join(RES, "consistency.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
        f.write("\n")
    for cat in ["kwota", "data_cyfrowa", "przepis", "cpv", "znak_sprawy"]:
        if cat in out["categories"]:
            print(cat, {v: round(out["categories"][cat][v]["share_other"], 3)
                        for v in VARIANTS})


if __name__ == "__main__":
    main()
