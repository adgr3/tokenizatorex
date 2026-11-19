"""Runda 1.2 — zapisy urzędowe i liczby (H1, H2).

Wyciąga z korpusu `test` prawdziwe wystąpienia kategorii, liczy tokeny na
wystąpienie dla wszystkich tokenizerów, bada lata 2015–2026 i długość kodów.

Wynik: audit/results/notations.json (+ notations.md)
"""
from __future__ import annotations

import os
import sys
from collections import Counter, defaultdict

import numpy as np

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common import (BOOTSTRAP_N, RESULTS_DIR, SEED, build_encoders, load_domain,
                    write_json)
from notation_patterns import COMPILED, PATTERNS, extract

DOMAINS = ["przetargi_ogloszenia", "przetargi_kio", "samorzad_uchwaly",
           "granty_ogloszenia", "prawo_eli", "ocr_prasa", "tabele_json",
           "web", "prawo"]
YEAR_TEMPLATE = "w roku {year} r. zadanie"
MAX_PER_CAT = 4000


def boot_mean(values: np.ndarray, n: int = 500, seed: int = SEED):
    if len(values) == 0:
        return (float("nan"), float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(values), size=(n, len(values)))
    means = values[idx].mean(1)
    return (float(values.mean()), float(np.percentile(means, 2.5)),
            float(np.percentile(means, 97.5)))


def main() -> None:
    encoders = build_encoders()
    out = {"meta": {"bootstrap_n": 500, "seed": SEED, "split": "test",
                    "max_occurrences_per_category": MAX_PER_CAT},
           "categories": {}, "h1": {}, "h2": {}}

    occ: dict[str, list[str]] = defaultdict(list)
    occ_dom: dict[str, Counter] = defaultdict(Counter)
    for dom in DOMAINS:
        for d in load_domain(dom, "test"):
            text = d["text"]
            for cat in PATTERNS:
                found = extract(text, cat, MAX_PER_CAT)
                if found:
                    occ[cat].extend(found)
                    occ_dom[cat][dom] += len(found)

    for cat, items in occ.items():
        items = items[:MAX_PER_CAT]
        if not items:
            continue
        arr = np.array([len(x) for x in items])
        row = {"count": len(items), "by_domain": dict(occ_dom[cat]),
               "examples": sorted(set(items))[:5],
               "chars_mean": float(arr.mean()), "tokenizers": {}}
        for label, enc in encoders.items():
            tok = np.array([len(enc.ids(x)) for x in items], dtype=float)
            mean, lo, hi = boot_mean(tok)
            row["tokenizers"][label] = {
                "tokens_mean": mean, "ci": [lo, hi],
                "tokens_median": float(np.median(tok)),
                "tokens_p90": float(np.percentile(tok, 90)),
                "tokens_per_char": float(tok.sum() / arr.sum()) if arr.sum() else None,
            }
        out["categories"][cat] = row
        ref = row["tokenizers"]["TOKENIZATOREX"]
        print(f"{cat:<18} {len(items):>5} wyst.  TOKENIZATOREX {ref['tokens_mean']:.2f} tok.")

    # --- H1: lata 2015–2026 -------------------------------------------------
    years = {}
    ref = "TOKENIZATOREX"
    year_occ = defaultdict(list)
    for d in load_domain("przetargi_ogloszenia", "test") + load_domain("prawo_eli", "test"):
        for m in COMPILED["rok"].finditer(d["text"]):
            y = int(m.group(0))
            if 2015 <= y <= 2026:
                year_occ[y].append(m.group(0))
    for y in range(2015, 2027):
        items = year_occ.get(y, [])
        row = {"occurrences": len(items)}
        if items:
            for label, enc in encoders.items():
                tok = np.array([len(enc.ids(x)) for x in items], dtype=float)
                row[label] = {"tokens_mean": float(tok.mean()), "ci": list(boot_mean(tok)[1:]),
                              "distinct_segmentation_share": _distinct_share(enc, items)}
        tpl = YEAR_TEMPLATE.format(year=y)
        row["template_total_tokens"] = {label: len(enc.ids(tpl)) for label, enc in encoders.items()}
        years[str(y)] = row
    out["h1"] = {"years": years, "template": YEAR_TEMPLATE,
                 "note": "template_total_tokens = liczba tokenów całego zdania-kontrolnego"}
    _h1_verdict(out, encoders, year_occ)

    # --- H2: długość liczb a koszt -----------------------------------------
    digit_occ = defaultdict(list)
    for dom in DOMAINS:
        for d in load_domain(dom, "test"):
            for m in __import__("re").finditer(r"\b\d{4,}\b", d["text"]):
                s = m.group(0)
                digit_occ[len(s)].append(s)
    h2 = {}
    for label, enc in encoders.items():
        xs, ys, per_digit = [], [], []
        for ln, items in sorted(digit_occ.items()):
            if not items:
                continue
            items = items[:2000]
            toks = np.array([len(enc.ids(x)) for x in items])
            xs.append(ln)
            ys.append(float(toks.mean()))
            per_digit.append(float(toks.sum() / (ln * len(items))))
        if len(xs) >= 3:
            corr = float(np.corrcoef(xs, ys)[0, 1])
        else:
            corr = float("nan")
        h2[label] = {"lengths": xs, "tokens_mean": ys, "tokens_per_digit": per_digit,
                     "corr_len_tokens": corr}
    out["h2"] = {"by_tokenizer": h2,
                 "note": "liczby całkowite 4+ cyfr z testu; tokens_per_digit = tokeny / (cyfry·wystąpienia)"}

    write_json(os.path.join(RESULTS_DIR, "notations.json"), out)
    _write_md(out)


def _distinct_share(enc, items: list[str]) -> float:
    sigs = Counter()
    for x in items:
        ids = enc.ids(x)
        sigs[tuple(enc.decode([i]) for i in ids)] += 1
    if not sigs:
        return float("nan")
    return 1.0 - sigs.most_common(1)[0][1] / sum(sigs.values())


def _h1_verdict(out, encoders, year_occ) -> None:
    early = [x for y in range(2015, 2025) for x in year_occ.get(y, [])]
    late = [x for y in range(2025, 2027) for x in year_occ.get(y, [])]
    res = {"early_n": len(early), "late_n": len(late), "tokenizers": {}}
    for label, enc in encoders.items():
        a = np.array([len(enc.ids(x)) for x in early], dtype=float)
        b = np.array([len(enc.ids(x)) for x in late], dtype=float)
        if len(a) and len(b):
            ma, la, ha = boot_mean(a)
            mb, lb, hb = boot_mean(b)
            res["tokenizers"][label] = {
                "early_mean": ma, "early_ci": [la, ha],
                "late_mean": mb, "late_ci": [lb, hb],
                "diff": mb - ma, "ratio": mb / ma if ma else None,
                "significant": bool(lb > ha or hb < la),
            }
    out["h1"]["early_vs_late"] = res


def _write_md(out: dict) -> None:
    lines = ["# Zapisy urzędowe i liczby (test)", "",
             "## Tokeny na wystąpienie (średnia; mniej = lepiej)", "",
             "| kategoria | wystąpień | TOKENIZATOREX | HF | Slayer1B | Pollock | Bielik | GPT-4o |",
             "|---|---:|---:|---:|---:|---:|---:|---:|"]
    labels = ["TOKENIZATOREX", "TOKENIZATOREX-HF", "Slayer1B", "Pollock-2.0",
              "Bielik-v3", "GPT-4o"]
    for cat, row in out["categories"].items():
        cells = [f"{row['tokenizers'][l]['tokens_mean']:.2f}" for l in labels]
        lines.append(f"| {cat} | {row['count']} | " + " | ".join(cells) + " |")
    lines += ["", "## H1 — koszt lat (średnia tokenów na samo wystąpienie roku)", "",
              "| rok | wystąpień | TOKENIZATOREX | HF | Slayer1B | szablon TOKENIZATOREX |",
              "|---:|---:|---:|---:|---:|---:|"]
    for y, row in out["h1"]["years"].items():
        if "TOKENIZATOREX" in row:
            lines.append(f"| {y} | {row['occurrences']} | {row['TOKENIZATOREX']['tokens_mean']:.3f} | "
                         f"{row['TOKENIZATOREX-HF']['tokens_mean']:.3f} | "
                         f"{row['Slayer1B']['tokens_mean']:.3f} | "
                         f"{row['template_total_tokens']['TOKENIZATOREX']} |")
    lines += ["", "## H2 — długość liczby a koszt", "",
              "| tokenizer | corr(długość, tokeny) | tokeny/cyfrę (4–12 cyfr) |",
              "|---|---:|---:|"]
    for label, r in out["h2"]["by_tokenizer"].items():
        pd = ", ".join(f"{x:.2f}" for x in r["tokens_per_digit"])
        lines.append(f"| {label} | {r['corr_len_tokens']:.3f} | {pd} |")
    path = os.path.join(RESULTS_DIR, "notations.md")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("zapisano", path)


if __name__ == "__main__":
    main()
