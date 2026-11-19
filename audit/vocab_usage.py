"""Runda 1.7 — użycie słownika: tokeny martwe/rzadkie, Zipf, Rényi α=2,5.

Wynik: audit/results/vocab_usage.json (+ vocab_usage.md)
"""
from __future__ import annotations

import os
import sys
from collections import Counter

import numpy as np

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common import RESULTS_DIR, build_encoders, load_domain, write_json

DOMAINS = ["przetargi_ogloszenia", "przetargi_kio", "samorzad_uchwaly",
           "granty_ogloszenia", "prawo_eli", "ocr_prasa", "tabele_json",
           "web", "wikipedia", "literatura", "prawo", "sejm", "nauka",
           "dyskusje", "angielski"]
ALPHA = 2.5


def renyi_eff(counts: np.ndarray, vocab_size: int) -> dict:
    counts = counts[counts > 0].astype(float)
    total = counts.sum()
    p = counts / total
    h = (1.0 / (1.0 - ALPHA)) * np.log(np.sum(p ** ALPHA))
    return {"H_alpha": float(h), "effective_vocab": float(np.exp(h)),
            "renyi_efficiency": float(np.exp(h) / vocab_size)}


def main() -> None:
    encoders = build_encoders()
    docs = [d for dom in DOMAINS for d in load_domain(dom, "test")]
    out = {"meta": {"split": "test", "domains": DOMAINS, "alpha": ALPHA,
                    "dead_definition": "0 użyć na całym korpusie testowym",
                    "rare_definition": "< 5 użyć"}, "tokenizers": {}}
    for label, enc in encoders.items():
        counter = Counter()
        n_tokens = 0
        for d in docs:
            ids = enc.ids(d["text"])
            counter.update(ids)
            n_tokens += len(ids)
        vocab_size = enc.vocab
        used = len(counter)
        counts = np.array(list(counter.values()), dtype=float)
        dead = vocab_size - used
        rare = int((counts < 5).sum())
        sorted_counts = np.sort(counts)[::-1]
        row = {
            "vocab": vocab_size, "tokens": n_tokens, "used_types": used,
            "dead_types": dead, "dead_share": dead / vocab_size if vocab_size else None,
            "rare_types_lt5": rare, "rare_share": rare / vocab_size if vocab_size else None,
            "top10_token_share": float(sorted_counts[:10].sum() / n_tokens),
            "top100_token_share": float(sorted_counts[:100].sum() / n_tokens),
            "top1000_token_share": float(sorted_counts[:1000].sum() / n_tokens),
            "renyi": renyi_eff(counts, vocab_size),
        }
        ranks = np.arange(1, len(sorted_counts) + 1)
        mask = sorted_counts > 0
        row["zipf_slope"] = float(np.polyfit(np.log(ranks[mask]), np.log(sorted_counts[mask]), 1)[0])
        out["tokenizers"][label] = row
        print(f"{label:<20} vocab {vocab_size:>7,} used {used:>6,} dead {dead:>6,} "
              f"({dead/vocab_size:.1%})  Rényi {row['renyi']['renyi_efficiency']:.4f}")
    write_json(os.path.join(RESULTS_DIR, "vocab_usage.json"), out)
    write_md(out)


def write_md(out: dict) -> None:
    lines = ["# Użycie słownika (test)", "",
             "| tokenizer | słownik | użyte typy | martwe | <5 użyć | Rényi eff. α=2,5 | top-1000 share | Zipf slope |",
             "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for l, r in out["tokenizers"].items():
        lines.append(f"| {l} | {r['vocab']:,} | {r['used_types']:,} | "
                     f"{r['dead_types']:,} ({r['dead_share']:.1%}) | "
                     f"{r['rare_types_lt5']:,} ({r['rare_share']:.1%}) | "
                     f"{r['renyi']['renyi_efficiency']:.4f} | "
                     f"{r['top1000_token_share']:.1%} | {r['zipf_slope']:.2f} |")
    lines += ["", "Rényi: `exp(H_α)/|V|`, α = 2,5, częstości z korpusu testowego.",
              "Tokeny specjalne nie są liczone (brak użyć)."]
    path = os.path.join(RESULTS_DIR, "vocab_usage.md")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
