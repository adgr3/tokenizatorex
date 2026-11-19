"""R2 #2: H1 koszt lat. Kazde wystapienie roku 2015..2026 (jako izolowany string)
kodujemy osobno i liczymy tokeny. Dziedziny: przetargi_ogloszenia + prawo_eli (TEST).
"""
from __future__ import annotations

import collections
import json
import re

import r2lib

YEAR_RE = re.compile(r"(?<!\d)(20(?:1[5-9]|2[0-6]))(?!\d)")

TOKENS = ["TOKENIZATOREX", "Slayer1B"]


def main() -> None:
    toks = r2lib.get_tokenizers()
    out = {
        "definition": "regex (?<!\\d)(20(?:1[5-9]|2[0-6]))(?!\\d); kazde wystapienie "
        "kodowane jako izolowany string roku; srednia = suma tokenow / liczba wystapien",
        "domains": ["przetargi_ogloszenia", "prawo_eli"],
        "split": "test",
        "years": {},
        "per_year": {},
    }
    for label in TOKENS:
        out["per_year"][label] = {}
    for dom in out["domains"]:
        docs = r2lib.load_docs(dom)
        counts = collections.Counter()
        for d in docs:
            for y in YEAR_RE.findall(d["text"]):
                counts[y] += 1
        out["years"][dom] = {"docs": len(docs), "counts": dict(sorted(counts.items()))}
        print(dom, "docs", len(docs), "years", dict(sorted(counts.items())))

    for label in TOKENS:
        tok = toks[label]
        per_year = {}
        for year in sorted({y for dom in out["domains"] for y in out["years"][dom]["counts"]}):
            ntok = len(tok.encode(year))
            occ = sum(out["years"][dom]["counts"].get(year, 0) for dom in out["domains"])
            per_year[year] = {
                "occurrences": occ,
                "tokens_per_occurrence": ntok,
                "mean_tokens_per_occurrence": ntok,
                "total_tokens": ntok * occ,
            }
        out["per_year"][label] = per_year
        print(f"{label:18s}", {y: (v["occurrences"], v["tokens_per_occurrence"]) for y, v in per_year.items()})
        for year in ("2024", "2026"):
            print(f"  {label} {year}: count={per_year[year]['occurrences']} mean={per_year[year]['mean_tokens_per_occurrence']:.6f}")

    path = r2lib.write_json("r2_h1_calendar.json", out)
    print("WROTE", path)


if __name__ == "__main__":
    main()
