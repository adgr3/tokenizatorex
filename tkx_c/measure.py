"""Pomiary TKX-C na teście TKX-A (kanoniczny HF).

Wyniki: tkx_c/results/fertility.json, digits_cost.json, calendar.json,
vocab.json. Uruchomienie: python tkx_c/measure.py --only core
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter

import numpy as np

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from measure_lib import DOMAINS, OFFICIAL, ROOT, VARIANTS, docs, hf_encode, load_hf

sys.path.append(os.path.join(ROOT, "audit"))
from common import bootstrap_indices  # noqa: E402

RES = os.path.join(ROOT, "tkx_c", "results")
os.makedirs(RES, exist_ok=True)


def write(name: str, obj) -> None:
    with open(os.path.join(RES, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")


def _ci(rep):
    return [float(np.percentile(rep, 2.5)), float(np.percentile(rep, 97.5))]


def core() -> None:
    TOKS = {v: load_hf(v) for v in VARIANTS}
    toks = {v: {} for v in VARIANTS}
    words = {d: [] for d in DOMAINS}
    byts = {d: [] for d in DOMAINS}
    chars = {d: [] for d in DOMAINS}
    counters = {v: Counter() for v in VARIANTS}
    doc_counts = {v: {d: [] for d in DOMAINS} for v in VARIANTS}
    for d in DOMAINS:
        ds = docs(d)
        for doc in ds:
            text = doc["text"]
            words[d].append(len(text.split()))
            byts[d].append(len(text.encode("utf-8")))
            chars[d].append(len(text))
            for v in VARIANTS:
                ids = hf_encode(TOKS[v], text)
                doc_counts[v][d].append(len(ids))
                counters[v].update(ids)
        print("core", d, len(ds))

    fertility = {"meta": {"split": "test", "bootstrap_n": 1000, "seed": 20261119,
                          "canonical": "HF export / variants", "domains": DOMAINS},
                 "domains": {}, "official": {}}
    for d in DOMAINS:
        w = np.array(words[d], dtype=float)
        idx = bootstrap_indices(len(w))
        row = {"docs": len(w), "words": int(w.sum()), "variants": {}}
        for v in VARIANTS:
            t = np.array(doc_counts[v][d], dtype=float)
            b = np.array(byts[d], dtype=float)
            c = np.array(chars[d], dtype=float)
            fr = t[idx].sum(1) / w[idx].sum(1)
            bp = b[idx].sum(1) / t[idx].sum(1)
            cp = c[idx].sum(1) / t[idx].sum(1)
            row["variants"][v] = {
                "tokens": int(t.sum()), "fertility": float(t.sum() / w.sum()),
                "fertility_ci": _ci(fr),
                "bytes_per_token": float(b.sum() / t.sum()),
                "bytes_per_token_ci": _ci(bp),
                "chars_per_token": float(c.sum() / t.sum()),
                "chars_per_token_ci": _ci(cp),
            }
        fertility["domains"][d] = row
    # agregat oficjalny (suma/suma) + CI
    for label, doms in (("official", OFFICIAL), ("all", DOMAINS)):
        w = np.array([x for d in doms for x in words[d]], dtype=float)
        idx = bootstrap_indices(len(w))
        row = {"docs": len(w), "words": int(w.sum()), "variants": {}}
        for v in VARIANTS:
            t = np.array([x for d in doms for x in doc_counts[v][d]], dtype=float)
            b = np.array([x for d in doms for x in byts[d]], dtype=float)
            fr = t[idx].sum(1) / w[idx].sum(1)
            bp = b[idx].sum(1) / t[idx].sum(1)
            row["variants"][v] = {"tokens": int(t.sum()),
                                  "fertility": float(t.sum() / w.sum()),
                                  "fertility_ci": _ci(fr),
                                  "bytes_per_token": float(b.sum() / t.sum()),
                                  "bytes_per_token_ci": _ci(bp)}
        fertility[label] = row
    write("fertility.json", fertility)

    # prawdziwy koszt cyfr V1 vs V0, parowany po dokumentach
    audit = json.load(open(os.path.join(ROOT, "audit", "results", "digits_cost.json"),
                           encoding="utf-8"))
    digits = {"meta": {"comparison": "V1-32k vs V0-32k", "split": "test",
                       "bootstrap_n": 1000, "seed": 20261119},
              "domains": {}, "official": {}}
    for d in DOMAINS:
        a = np.array(doc_counts["V0-32k"][d], dtype=float)
        b = np.array(doc_counts["V1-32k"][d], dtype=float)
        w = np.array(words[d], dtype=float)
        idx = bootstrap_indices(len(w))
        diff = (b[idx] - a[idx]).sum(1) / w[idx].sum(1)
        row = {"docs": len(w), "words": int(w.sum()),
               "tokens_v0": int(a.sum()), "tokens_v1": int(b.sum()),
               "delta_tokens": int(b.sum() - a.sum()),
               "delta_tokens_per_word": float((b.sum() - a.sum()) / w.sum()),
               "delta_ci": _ci(diff),
               "delta_pct": float((b.sum() - a.sum()) / a.sum()),
               "delta_pct_ci": [c / (a.sum() / w.sum()) for c in _ci(diff)],
               "audit_lower_pct": audit["domains"].get(d, {}).get("lower_pct_of_tokens"),
               "audit_upper_pct": audit["domains"].get(d, {}).get("upper_pct_of_tokens")}
        digits["domains"][d] = row
    for label, doms in (("official", OFFICIAL), ("all", DOMAINS)):
        a = np.array([x for d in doms for x in doc_counts["V0-32k"][d]], dtype=float)
        b = np.array([x for d in doms for x in doc_counts["V1-32k"][d]], dtype=float)
        w = np.array([x for d in doms for x in words[d]], dtype=float)
        idx = bootstrap_indices(len(w))
        diff = (b[idx] - a[idx]).sum(1) / w[idx].sum(1)
        digits[label] = {"docs": len(w), "words": int(w.sum()),
                         "tokens_v0": int(a.sum()), "tokens_v1": int(b.sum()),
                         "delta_tokens": int(b.sum() - a.sum()),
                         "delta_pct": float((b.sum() - a.sum()) / a.sum()),
                         "delta_tokens_per_word": float((b.sum() - a.sum()) / w.sum()),
                         "delta_ci": _ci(diff),
                         "delta_pct_ci": [c / (a.sum() / w.sum()) for c in _ci(diff)]}
    write("digits_cost.json", digits)

    # V2b/V3 (i V2 dla porównania) vs V0 — ten sam parowany bootstrap po dokumentach.
    new = {"meta": {"comparison": "V2/V2b/V3 vs V0-32k", "split": "test",
                    "bootstrap_n": 1000, "seed": 20261119, "post_hoc": True},
           "domains": {}, "official": {}}
    for v in ("V2-32k", "V2b-32k", "V3-32k"):
        new["domains"][v] = {}
    for d in DOMAINS:
        a = np.array(doc_counts["V0-32k"][d], dtype=float)
        w = np.array(words[d], dtype=float)
        idx = bootstrap_indices(len(w))
        for v in ("V2-32k", "V2b-32k", "V3-32k"):
            b = np.array(doc_counts[v][d], dtype=float)
            diff = (b[idx] - a[idx]).sum(1) / w[idx].sum(1)
            new["domains"][v][d] = {
                "docs": len(w), "tokens_v0": int(a.sum()), "tokens_v": int(b.sum()),
                "delta_pct": float((b.sum() - a.sum()) / a.sum()),
                "delta_pct_ci": [c / (a.sum() / w.sum()) for c in _ci(diff)],
                "delta_tokens_per_word": float((b.sum() - a.sum()) / w.sum()),
                "audit_lower_pct": audit["domains"].get(d, {}).get("lower_pct_of_tokens"),
                "audit_upper_pct": audit["domains"].get(d, {}).get("upper_pct_of_tokens")}
    for label, doms in (("official", OFFICIAL), ("all", DOMAINS)):
        a = np.array([x for d in doms for x in doc_counts["V0-32k"][d]], dtype=float)
        w = np.array([x for d in doms for x in words[d]], dtype=float)
        idx = bootstrap_indices(len(w))
        new[label] = {}
        for v in ("V2-32k", "V2b-32k", "V3-32k"):
            b = np.array([x for d in doms for x in doc_counts[v][d]], dtype=float)
            diff = (b[idx] - a[idx]).sum(1) / w[idx].sum(1)
            new[label][v] = {"docs": len(w), "tokens_v0": int(a.sum()),
                             "tokens_v": int(b.sum()),
                             "delta_pct": float((b.sum() - a.sum()) / a.sum()),
                             "delta_pct_ci": [c / (a.sum() / w.sum()) for c in _ci(diff)]}
    write("digits_cost_new.json", new)

    # kalendarz
    cal = {"template": "w roku {year} r. zadanie", "years": list(range(2015, 2036)),
           "variants": {}, "flat": {}}
    for v in VARIANTS:
        tok = TOKS[v]
        vals = {str(y): len(hf_encode(tok, f"w roku {y} r. zadanie"))
                for y in range(2015, 2036)}
        cal["variants"][v] = vals
        cal["flat"][v] = len(set(vals.values())) == 1
    write("calendar.json", cal)

    # słownik
    voc = {"meta": {"split": "test", "canonical": "HF export"},
           "variants": {}}
    v0 = TOKS["V0-32k"]
    v0_vocab = set(v0.get_vocab())
    for v in VARIANTS:
        tok = TOKS[v]
        vocab = tok.get_vocab()
        used = counters[v]
        dead = len(vocab) - len(used)
        rare = sum(1 for c in used.values() if c < 5)
        digit_tokens = sum(c for i, c in used.items()
                           if any(ch.isdigit() for ch in (tok.id_to_token(i) or "")))
        total = sum(used.values())
        new = [(tok.id_to_token(i), c) for i, c in used.most_common()
               if tok.id_to_token(i) not in v0_vocab][:50]
        voc["variants"][v] = {
            "vocab": len(vocab), "used_types": len(used),
            "dead": dead, "dead_share": dead / len(vocab),
            "rare_lt5": rare, "rare_share": rare / len(vocab),
            "digit_token_uses": digit_tokens,
            "digit_token_share": digit_tokens / total if total else None,
            "top_new": new,
        }
    write("vocab.json", voc)
    print("core done")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="core")
    a = ap.parse_args()
    if a.only == "core":
        core()
