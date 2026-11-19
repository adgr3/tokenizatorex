"""Runda 1.1 — wydajność na dziedzinach (fertility, bajty/token, znaki/token).

Wynik: audit/results/fertility.json (+ fertility.md)
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common import (BOOTSTRAP_N, RESULTS_DIR, SEED, bootstrap_indices, build_encoders, load_domain,
                    write_json)

DOMAINS = ["przetargi_ogloszenia", "przetargi_kio", "samorzad_uchwaly",
           "granty_ogloszenia", "prawo_eli", "ocr_prasa", "tabele_json",
           "web", "wikipedia", "literatura", "prawo", "sejm", "nauka",
           "dyskusje", "angielski"]
REFERENCE = "TOKENIZATOREX"


def _boot_idx(k: int, n: int = BOOTSTRAP_N, seed: int = SEED) -> np.ndarray:
    return bootstrap_indices(k, n, seed)


def _ci_from_replicates(rep: np.ndarray) -> list[float]:
    return [float(np.percentile(rep, 2.5)), float(np.percentile(rep, 97.5))]


def measure(enc, docs):
    toks, words, byts, chars = [], [], [], []
    for d in docs:
        t = d["text"]
        ids = enc.ids(t)
        toks.append(len(ids))
        words.append(len(t.split()))
        b = t.encode("utf-8")
        byts.append(len(b))
        chars.append(len(t))
    return (np.array(toks, dtype=float), np.array(words, dtype=float),
            np.array(byts, dtype=float), np.array(chars, dtype=float))


def main() -> None:
    encoders = build_encoders()
    out = {"meta": {"bootstrap_n": BOOTSTRAP_N, "seed": SEED, "split": "test",
                    "reference": REFERENCE,
                    "word_definition": "str.split()",
                    "special_tokens": False},
           "domains": {}, "comparisons": {}, "ranking": {}}

    for dom in DOMAINS:
        docs = load_domain(dom, "test")
        if not docs:
            print(f"{dom}: brak testu — pomijam")
            continue
        idx = _boot_idx(len(docs))
        wsum = np.array([len(d["text"].split()) for d in docs], dtype=float)
        row = {"docs": len(docs), "words": int(wsum.sum()), "tokenizers": {}}
        arrays = {}
        for label, enc in encoders.items():
            t, w, b, c = measure(enc, docs)
            arrays[label] = (t, w, b, c)
            fert_rep = t[idx].sum(1) / w[idx].sum(1)
            bpt_rep = b[idx].sum(1) / t[idx].sum(1)
            cpt_rep = c[idx].sum(1) / t[idx].sum(1)
            row["tokenizers"][label] = {
                "tokens": int(t.sum()),
                "fertility": float(t.sum() / w.sum()),
                "fertility_ci": _ci_from_replicates(fert_rep),
                "bytes_per_token": float(b.sum() / t.sum()),
                "bytes_per_token_ci": _ci_from_replicates(bpt_rep),
                "chars_per_token": float(c.sum() / t.sum()),
                "chars_per_token_ci": _ci_from_replicates(cpt_rep),
            }
        out["domains"][dom] = row
        out["ranking"][dom] = sorted(
            [(lab, v["fertility"]) for lab, v in row["tokenizers"].items()],
            key=lambda x: x[1])
        ref_t, ref_w, _, _ = arrays[REFERENCE]
        comp = {}
        for label, (t, w, _, _) in arrays.items():
            if label == REFERENCE:
                continue
            diff_rep = (t[idx] - ref_t[idx]).sum(1) / w[idx].sum(1)
            ratio_rep = t[idx].sum(1) / ref_t[idx].sum(1)
            diff = float((t.sum() - ref_t.sum()) / w.sum())
            ratio = float(t.sum() / ref_t.sum())
            comp[label] = {
                "diff_tokens_per_word": diff,
                "diff_ci": _ci_from_replicates(diff_rep),
                "ratio_vs_reference": ratio,
                "ratio_ci": _ci_from_replicates(ratio_rep),
                "fraza": f"{label} vs {REFERENCE}",
                "significant": bool(np.percentile(diff_rep, 2.5) > 0 or np.percentile(diff_rep, 97.5) < 0),
                "practical_ge_1pct": bool(abs(ratio - 1) >= 0.01),
                "verdict": ("istotna" if (np.percentile(diff_rep, 2.5) > 0 or np.percentile(diff_rep, 97.5) < 0)
                            and abs(ratio - 1) >= 0.01 else "nieistotna"),
            }
        out["comparisons"][dom] = comp
        print(f"{dom:<22} {len(docs):>4} dok.  ref {row['tokenizers'][REFERENCE]['fertility']:.3f}  "
              f"best {out['ranking'][dom][0][0]} {out['ranking'][dom][0][1]:.3f}")

    write_json(os.path.join(RESULTS_DIR, "fertility.json"), out)
    write_markdown(out)


def write_markdown(out: dict) -> None:
    labs = list(out["meta"].get("labels", [])) or list(
        next(iter(out["domains"].values()))["tokenizers"].keys())
    doms = list(out["domains"].keys())
    lines = ["# Fertility na `test` (tokeny/słowo; mniej = lepiej)\n",
             "Wartości z 95% CI bootstrapu po dokumentach (1000 powtórzeń, seed 20261119).\n",
             "| tokenizer | " + " | ".join(doms) + " |",
             "|---|" + "---:|" * len(doms)]
    for lab in labs:
        cells = []
        for d in doms:
            v = out["domains"][d]["tokenizers"][lab]
            cells.append(f"{v['fertility']:.3f} [{v['fertility_ci'][0]:.3f}; {v['fertility_ci'][1]:.3f}]")
        lines.append(f"| {lab} | " + " | ".join(cells) + " |")
    lines += ["", "## Rankingi (test)", ""]
    for d in doms:
        r = out["ranking"][d]
        lines.append(f"* **{d}**: " + ", ".join(f"{i+1}. {n} {v:.3f}" for i, (n, v) in enumerate(r)))
    lines += ["", "## Różnice względem TOKENIZATOREX (test)", "",
              "| dziedzina | tokenizer | różnica tok./słowo [95% CI] | stosunek | werdykt |",
              "|---|---|---:|---:|---|"]
    for d in doms:
        for lab, c in out["comparisons"][d].items():
            lines.append(f"| {d} | {lab} | {c['diff_tokens_per_word']:+.4f} "
                         f"[{c['diff_ci'][0]:+.4f}; {c['diff_ci'][1]:+.4f}] | "
                         f"{c['ratio_vs_reference']:.3f} | {c['verdict']} |")
    path = os.path.join(RESULTS_DIR, "fertility.md")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("zapisano", path)


if __name__ == "__main__":
    main()
