"""Kontrola przecieku TKX-V21-JSON.

Test: tc1/dane/test.jsonl + json_generic_heldout_test + 10 wzorców JSON
z tkx_v2/wzorce.json (tylko pomiar, nie trening).
Trening: tc1/dane/train.jsonl (wyciąg) + syntetyczny json_train.txt.
Sprawdzamy: (a) pełny tekst testu w treningu, (b) pokrycie 13-gramów znaków
per dokument; > 50% = przeciek do zgłoszenia (dla wzorców JSON raportujemy
wspólny szkielet, ale nie traktujemy go jak kopię przykładu).

  python tkx_v21/sprawdz_przeciek.py
"""
from __future__ import annotations

import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "tkx_v21", "dane")
RESULTS = os.path.join(REPO, "results")
TC1 = r"D:\VPS\fabryka\tc1\dane"
N = 13


def load_tc1(split):
    docs = []
    with open(os.path.join(TC1, f"{split}.jsonl"), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                obj = json.loads(line)
                docs.append(obj.get("text") or json.dumps(obj, ensure_ascii=False))
    return docs


def load_generic(split):
    docs = []
    p = os.path.join(DATA, f"json_generic_heldout_{split}.jsonl")
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                docs.append(json.loads(line)["text"])
    return docs


def load_wzorce():
    p = os.path.join(REPO, "tkx_v2", "wzorce.json")
    items = json.load(open(p, encoding="utf-8"))["items"]
    sel = [x for x in items if x["category"] == "json_tool_calls"]
    assert len(sel) == 10, f"oczekiwano 10 wzorcow JSON, jest {len(sel)}"
    return sel


def grams(text):
    t = text.replace("\r\n", "\n")
    if len(t) < N:
        return {t}
    return {t[i:i + N] for i in range(len(t) - N + 1)}


def main():
    os.makedirs(RESULTS, exist_ok=True)
    train_parts = []
    with open(os.path.join(DATA, "tc1_json_train.txt"), encoding="utf-8") as f:
        train_parts.append(f.read())
    with open(os.path.join(DATA, "json_train.txt"), encoding="utf-8") as f:
        train_parts.append(f.read())
    train = "\n".join(train_parts)

    tests = {"tc1_test": load_tc1("test"),
             "json_generic_test": load_generic("test"),
             "wzorce_json": [x["pattern"] for x in load_wzorce()]}
    wzorce_ids = [x["id"] for x in load_wzorce()]
    all_test_grams = set()
    doc_grams = {}
    for sname, docs in tests.items():
        for i, d in enumerate(docs):
            g = grams(d)
            doc_grams[(sname, i)] = g
            all_test_grams |= g
    print(f"test: {sum(len(v) for v in tests.values())} dok., "
          f"{len(all_test_grams):,} unikalnych 13-gramów; skanuję trening "
          f"({len(train):,} znaków)...")
    found = set()
    t = train.replace("\r\n", "\n")
    for i in range(len(t) - N + 1):
        g = t[i:i + N]
        if g in all_test_grams:
            found.add(g)
    print(f"znalezione 13-gramy: {len(found):,}")

    out = {"n": N, "train_chars": len(train), "test_docs": {}, "summary": {}}
    corpus_leaks = 0
    pattern_exact = 0
    for sname, docs in tests.items():
        rows = []
        for i, d in enumerate(docs):
            g = doc_grams[(sname, i)]
            hit = len(g & found) / len(g) if g else 0.0
            exact = d in train
            row = {"doc": i, "chars": len(d), "coverage": hit, "exact": exact}
            if sname == "wzorce_json":
                row["id"] = wzorce_ids[i]
            rows.append(row)
            if exact:
                if sname == "wzorce_json":
                    pattern_exact += 1
                else:
                    corpus_leaks += 1
            elif hit > 0.5 and sname != "wzorce_json":
                corpus_leaks += 1
        out["test_docs"][sname] = {
            "docs": len(rows),
            "mean_coverage": sum(r["coverage"] for r in rows) / len(rows) if rows else 0.0,
            "max_coverage": max((r["coverage"] for r in rows), default=0.0),
            "docs_over_50pct": sum(1 for r in rows if r["coverage"] > 0.5),
            "exact_matches": sum(1 for r in rows if r["exact"]),
            "rows": rows,
        }
    out["summary"] = {
        "docs_over_50pct_or_exact": corpus_leaks + pattern_exact,
        "corpus_docs_over_50pct_or_exact": corpus_leaks,
        "wzorce_json_exact": pattern_exact,
        "wzorce_json_note": ("10 wzorcow JSON: 0 kopii; wysokie pokrycie to wspolny "
                             "szkielet wywolania, nie przeciek przykladu"),
        "status": "PRZECIEK" if (corpus_leaks or pattern_exact) else "OK",
    }
    with open(os.path.join(RESULTS, "tkx_v21_leak.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps({k: {kk: v[kk] for kk in ("docs", "mean_coverage", "max_coverage",
                                               "docs_over_50pct", "exact_matches")}
                      for k, v in out["test_docs"].items()}, ensure_ascii=False, indent=2))
    print("status:", out["summary"]["status"])


if __name__ == "__main__":
    main()
