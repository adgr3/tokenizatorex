"""Rozbicie zysku V0J2 vs V0 na held-out test wg formy (compact/pretty/result).

Wynik: results/tkx_v21_heldout_forms.json. Czyta teksty z danych poza gitem
(domyślnie tkx_v21/dane; fallback D:\\VPS\\fabryka\\tkx-json\\tkx_v21\\dane).
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from pathlib import Path

from tokenizers import Tokenizer

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
REPO = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get("TKX_V21_DATA", str(REPO / "tkx_v21" / "dane")))
if not DATA.is_dir():
    DATA = Path(r"D:\VPS\fabryka\tkx-json\tkx_v21\dane")
HELD = DATA / "json_generic_heldout_test.jsonl"


def local(name):
    return Tokenizer.from_file(str(REPO / "hf" / "variants" / name / "tokenizer.json"))


def n(tok, s):
    return len(tok.encode(s, add_special_tokens=False).ids)


def main():
    items = [json.loads(x) for x in open(HELD, encoding="utf-8") if x.strip()]
    leak = json.load(open(REPO / "results/tkx_v21_leak.json", encoding="utf-8"))
    covs = [r["coverage"] for r in leak["test_docs"]["json_generic_test"]["rows"]]
    assert len(covs) == len(items), (len(covs), len(items))
    v0 = local("V0-32k")
    v0j2 = local("V0J2-32k")
    by = defaultdict(lambda: {"docs": 0, "tokens_v0": 0, "tokens_v0j2": 0,
                              "words_v0": 0, "coverage": []})
    for it, cov in zip(items, covs):
        s = it["text"]
        b = by[it["form"]]
        b["docs"] += 1
        b["tokens_v0"] += n(v0, s)
        b["tokens_v0j2"] += n(v0j2, s)
        b["words_v0"] += len(s.split())
        b["coverage"].append(cov)
    out = {"source": "json_generic_heldout_test", "docs": len(items), "forms": {}}
    tot0 = tot2 = totw = 0
    allcov = []
    for form in sorted(by):
        b = by[form]
        delta = (b["tokens_v0j2"] / b["tokens_v0"] - 1) * 100
        out["forms"][form] = {
            "docs": b["docs"],
            "tokens_v0": b["tokens_v0"],
            "tokens_v0j2": b["tokens_v0j2"],
            "words_v0": b["words_v0"],
            "delta_pct": delta,
            "mean_tokens_per_doc_v0": b["tokens_v0"] / b["docs"],
            "mean_tokens_per_doc_v0j2": b["tokens_v0j2"] / b["docs"],
            "mean_coverage": sum(b["coverage"]) / len(b["coverage"]),
        }
        tot0 += b["tokens_v0"]
        tot2 += b["tokens_v0j2"]
        totw += b["words_v0"]
        allcov += b["coverage"]
    out["overall"] = {
        "docs": len(items), "tokens_v0": tot0, "tokens_v0j2": tot2,
        "words_v0": totw, "delta_pct": (tot2 / tot0 - 1) * 100,
        "mean_tokens_per_doc_v0": tot0 / len(items),
        "mean_tokens_per_doc_v0j2": tot2 / len(items),
        "mean_coverage": sum(allcov) / len(allcov),
    }
    out["note"] = ("compact/pretty korzystają ze wspólnego szkieletu wywołania; "
                   "result to odpowiedź narzędzia i jest bliższa nowej treści")
    with open(REPO / "results/tkx_v21_heldout_forms.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
