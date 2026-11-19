"""Agregat oficjalny (7 dziedzin) i cały korpus: fertility + CI + pary."""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common import BOOTSTRAP_N, RESULTS_DIR, SEED, build_encoders, load_domain, write_json

OFFICIAL = ["przetargi_ogloszenia", "przetargi_kio", "samorzad_uchwaly",
            "granty_ogloszenia", "prawo_eli", "ocr_prasa", "tabele_json"]
ALL = OFFICIAL + ["web", "wikipedia", "literatura", "prawo", "sejm", "nauka",
                  "dyskusje", "angielski"]
LABELS = ["TOKENIZATOREX", "TOKENIZATOREX-HF", "Slayer1B", "APT3-1B",
          "Pollock-2.0", "Bielik-v3", "PLLuM-12B", "GPT-4o"]


def aggregate(domains, encoders):
    tokens = {l: [] for l in encoders}
    words = []
    for dom in domains:
        for d in load_domain(dom, "test"):
            w = len(d["text"].split())
            words.append(w)
            for l, enc in encoders.items():
                tokens[l].append(len(enc.ids(d["text"])))
    words = np.array(words, dtype=float)
    rng = np.random.default_rng(SEED)
    idx = rng.integers(0, len(words), size=(BOOTSTRAP_N, len(words)))
    out = {"domains": domains, "documents": len(words), "words": int(words.sum()),
           "tokenizers": {}, "comparisons": {}}
    reps = {}
    for l in tokens:
        t = np.array(tokens[l], dtype=float)
        rep = t[idx].sum(1) / words[idx].sum(1)
        reps[l] = rep
        out["tokenizers"][l] = {"tokens": int(t.sum()),
                                "fertility": float(t.sum() / words.sum()),
                                "ci": [float(np.percentile(rep, 2.5)),
                                       float(np.percentile(rep, 97.5))]}
    ref = np.array(tokens["TOKENIZATOREX"], dtype=float)
    for l in tokens:
        if l == "TOKENIZATOREX":
            continue
        t = np.array(tokens[l], dtype=float)
        ratio = t.sum() / ref.sum()
        rep = t[idx].sum(1) / ref[idx].sum(1)
        out["comparisons"][l] = {
            "ratio": float(ratio), "ratio_ci": [float(np.percentile(rep, 2.5)),
                                                float(np.percentile(rep, 97.5))],
            "delta_tokens": int(t.sum() - ref.sum()),
        }
    return out


def main() -> None:
    encoders = build_encoders(LABELS)
    out = {"meta": {"bootstrap_n": BOOTSTRAP_N, "seed": SEED, "split": "test"},
           "official": aggregate(OFFICIAL, encoders),
           "all": aggregate(ALL, encoders)}
    write_json(os.path.join(RESULTS_DIR, "official_aggregate.json"), out)
    for key in ("official", "all"):
        r = out[key]
        print(key, r["documents"], r["words"])
        for l, v in r["tokenizers"].items():
            print(f"  {l:<20} {v['fertility']:.4f} [{v['ci'][0]:.4f};{v['ci'][1]:.4f}]")


if __name__ == "__main__":
    main()
