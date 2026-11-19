"""Runda 1.4 — odporność na zniekształcenia (H5).

Warianty: bez polskich znaków, CAPS, Title, literówki 2%/5%, szum OCR 2%/5%,
NFD, mieszanka PL–EN, emoji. Raport: wzrost tokenów bezwzględny i względny
z 95% CI bootstrapu po dokumentach.

Wynik: audit/results/robustness.json (+ robustness.md)
"""
from __future__ import annotations

import hashlib
import os
import random
import sys
import unicodedata

import numpy as np

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common import BOOTSTRAP_N, RESULTS_DIR, SEED, build_encoders, load_domain, write_json

DOMAINS = ["przetargi_ogloszenia", "przetargi_kio", "samorzad_uchwaly",
           "granty_ogloszenia", "prawo_eli", "ocr_prasa", "tabele_json", "web"]
N_DOCS = {"web": 50}
N_DEFAULT = 25
PL_MAP = str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ")
OCR_MAP = [("rn", "m"), ("m", "rn"), ("l", "1"), ("1", "l"), ("ę", "e"),
           ("ą", "a"), ("ó", "o"), ("ś", "s"), ("ż", "z"), ("ź", "z"), ("ć", "c"),
           ("ń", "n")]
EN_SENTENCE = ("The contracting authority shall evaluate the offer in accordance "
               "with the terms of reference and the applicable provisions of law.")
EMOJI = " 🙂📄✅"


def _rng(doc) -> random.Random:
    h = int(hashlib.sha1(doc["id"].encode("utf-8")).hexdigest()[:12], 16)
    return random.Random(SEED + h)


def typo(text: str, p: float, rng: random.Random) -> str:
    out = []
    for w in text.split(" "):
        if len(w) > 3 and rng.random() < p:
            i = rng.randrange(len(w) - 1)
            w = w[:i] + w[i + 1] + w[i] + w[i + 2:]
        out.append(w)
    return " ".join(out)


def ocr_noise(text: str, p: float, rng: random.Random) -> str:
    out = []
    i = 0
    while i < len(text):
        a, b = None, None
        for src, dst in OCR_MAP:
            if text.startswith(src, i):
                a, b = src, dst
                break
        if a and rng.random() < p:
            out.append(b)
            i += len(a)
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def mixed(text: str, rng: random.Random) -> str:
    parts = text.split(". ")
    out = []
    for i, p in enumerate(parts):
        out.append(p)
        if i % 8 == 7:
            out.append(EN_SENTENCE)
    return ". ".join(out)


def emojify(text: str, rng: random.Random) -> str:
    parts = text.split(". ")
    out = []
    for p in parts:
        if rng.random() < 0.2:
            p = p + " " + rng.choice(EMOJI.strip().split())
        out.append(p)
    return ". ".join(out)


VARIANTS = {
    "bez_pl": lambda t, r: t.translate(PL_MAP),
    "caps": lambda t, r: t.upper(),
    "title": lambda t, r: t.title(),
    "typo_2": lambda t, r: typo(t, 0.02, r),
    "typo_5": lambda t, r: typo(t, 0.05, r),
    "ocr_2": lambda t, r: ocr_noise(t, 0.02, r),
    "ocr_5": lambda t, r: ocr_noise(t, 0.05, r),
    "nfd": lambda t, r: unicodedata.normalize("NFD", t),
    "mixed_en": lambda t, r: mixed(t, r),
    "emoji": lambda t, r: emojify(t, r),
}


def boot_ratio_ci(num: list[float], den: list[float], n: int = BOOTSTRAP_N, seed: int = SEED):
    if not num:
        return (float("nan"),) * 3
    a = np.array(num, dtype=float)
    b = np.array(den, dtype=float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(a), size=(n, len(a)))
    rep = a[idx].sum(1) / b[idx].sum(1)
    return (float(a.sum() / b.sum()), float(np.percentile(rep, 2.5)),
            float(np.percentile(rep, 97.5)))


def main() -> None:
    encoders = build_encoders()
    out = {"meta": {"bootstrap_n": BOOTSTRAP_N, "seed": SEED, "split": "test",
                    "n_docs": N_DOCS, "variants": list(VARIANTS)},
           "domains": {}, "aggregate": {}}

    # przygotuj dokumenty i warianty raz na dokument
    prepared = {}
    for dom in DOMAINS:
        docs = load_domain(dom, "test")
        rng = np.random.default_rng(SEED)
        if len(docs) > N_DOCS.get(dom, N_DEFAULT):
            idx = rng.choice(len(docs), size=N_DOCS.get(dom, N_DEFAULT), replace=False)
            docs = [docs[i] for i in sorted(idx)]
        prepared[dom] = docs
        res = {"docs": len(docs), "words": sum(len(d["text"].split()) for d in docs),
               "variants": {}}
        rows = {v: {"num": [], "den": [], "delta_words": []} for v in VARIANTS}
        word_counts = {v: [] for v in VARIANTS}
        for v in VARIANTS:
            for label in encoders:
                rows[v][label] = {"num": [], "den": []}
        for d in docs:
            text = d["text"]
            r = _rng(d)
            w0 = len(text.split())
            base_counts = {label: len(enc.ids(text)) for label, enc in encoders.items()}
            for v, fn in VARIANTS.items():
                tv = fn(text, r)
                word_counts[v].append(len(tv.split()) - w0)
                for label, enc in encoders.items():
                    base = base_counts[label]
                    var = len(enc.ids(tv))
                    rows[v][label]["num"].append(var - base)
                    rows[v][label]["den"].append(base)
        for v in VARIANTS:
            rv = {"delta_words_mean": float(np.mean(word_counts[v])) if word_counts[v] else 0.0,
                  "tokenizers": {}}
            for label in encoders:
                delta = rows[v][label]["num"]
                base = rows[v][label]["den"]
                mean_delta, lo_d, hi_d = boot_ratio_ci(delta, [1] * len(delta))
                ratio, lo, hi = boot_ratio_ci([d + b for d, b in zip(delta, base)], base)
                rv["tokenizers"][label] = {
                    "delta_tokens_total": int(sum(delta)),
                    "delta_per_doc_mean": mean_delta,
                    "delta_per_doc_ci": [lo_d, hi_d],
                    "relative_increase": ratio - 1.0,
                    "relative_ci": [lo - 1.0, hi - 1.0],
                }
            res["variants"][v] = rv
        out["domains"][dom] = res
        ref = res["variants"]["nfd"]["tokenizers"]["TOKENIZATOREX"]["relative_increase"]
        print(f"{dom:<22} NFD +{ref:.1%}  CAPS +"
              f"{res['variants']['caps']['tokenizers']['TOKENIZATOREX']['relative_increase']:.1%}")

    # agregat po dziedzinach urzędowych (bez web/angielskiego)
    out["aggregate"] = _aggregate(out["domains"], [d for d in DOMAINS if d != "web"], encoders)
    out["aggregate_web"] = _aggregate(out["domains"], ["web"], encoders)
    out["h5_verdict"] = _verdict(out, encoders)
    write_json(os.path.join(RESULTS_DIR, "robustness.json"), out)
    write_md(out)
    print("H5", out["h5_verdict"])


def _aggregate(domains: dict, names: list[str], encoders) -> dict:
    agg = {"domains": names, "variants": {}}
    for v in VARIANTS:
        rv = {"tokenizers": {}}
        for label in encoders:
            rel = [domains[d]["variants"][v]["tokenizers"][label]["relative_increase"] for d in names]
            absd = [domains[d]["variants"][v]["tokenizers"][label]["delta_per_doc_mean"] for d in names]
            rv["tokenizers"][label] = {
                "relative_increase_mean": float(np.mean(rel)),
                "relative_range": [float(min(rel)), float(max(rel))],
                "delta_per_doc_mean": float(np.mean(absd)),
            }
        agg["variants"][v] = rv
    return agg


def _verdict(out: dict, encoders) -> dict:
    ref = "TOKENIZATOREX"
    polish = ["Slayer1B", "APT3-1B", "Pollock-2.0", "Bielik-v3", "PLLuM-12B",
              "TOKENIZATOREX-base"]
    agg = out["aggregate"]["variants"]
    over25 = [v for v in VARIANTS
              if agg[v]["tokenizers"][ref]["relative_increase_mean"] > 0.25]
    worse_than_some = []
    for v in VARIANTS:
        r = agg[v]["tokenizers"][ref]["relative_increase_mean"]
        for lab in polish:
            if r > agg[v]["tokenizers"][lab]["relative_increase_mean"] + 0.01:
                worse_than_some.append({"variant": v, "vs": lab,
                                        "delta_pp": r - agg[v]["tokenizers"][lab]["relative_increase_mean"]})
    return {"variants_over_25pct": over25,
            "confirmed": bool(over25) or bool(worse_than_some),
            "worse_relative_than_polish": worse_than_some[:12]}


def write_md(out: dict) -> None:
    ref = "TOKENIZATOREX"
    lines = ["# Odporność na zniekształcenia (test)", "",
             "Wzrost liczby tokenów względem czystego tekstu (średnia po dziedzinach "
             "urzędowych; 95% CI w JSON).", "",
             "| wariant | TOKENIZATOREX | HF | Slayer1B | APT3 | Pollock | GPT-4o |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    labs = [ref, "TOKENIZATOREX-HF", "Slayer1B", "APT3-1B", "Pollock-2.0", "GPT-4o"]
    for v, r in out["aggregate"]["variants"].items():
        cells = [f"{r['tokenizers'][l]['relative_increase_mean']:+.1%}" for l in labs]
        lines.append(f"| {v} | " + " | ".join(cells) + " |")
    lines += ["", "## Werdykt H5", ""]
    v = out["h5_verdict"]
    lines.append(f"* Warianty > 25%: {', '.join(v['variants_over_25pct']) or 'brak'}")
    lines.append(f"* H5: {'POTWIERDZONA' if v['confirmed'] else 'OBALONA'}")
    if v["worse_relative_than_polish"]:
        lines.append("* TOKENIZATOREX traci względnie więcej niż:")
        for w in v["worse_relative_than_polish"][:6]:
            lines.append(f"  * {w['variant']} vs {w['vs']}: +{w['delta_pp']:.1%} pkt proc.")
    path = os.path.join(RESULTS_DIR, "robustness.md")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("zapisano", path)


if __name__ == "__main__":
    main()
