"""Zestawienie R2 vs R1 do raportu (tylko odczyt wynikow)."""
from __future__ import annotations

import json
import os

import r2lib

R1 = r2lib.RESULTS
HERE = os.path.dirname(os.path.abspath(__file__))


def load(name):
    return json.load(open(os.path.join(HERE, name), encoding="utf-8"))


def load_r1(name):
    return json.load(open(os.path.join(R1, name), encoding="utf-8"))


def rel(a, b):
    return (a - b) / b if b else None


def pct(x):
    return f"{x*100:+.4f}%"


def main():
    f2 = load("r2_fertility.json")
    f1 = load_r1("fertility.json")
    print("FERTILITY")
    for dom, e in f2["domains"].items():
        for lab, v in e["tokenizers"].items():
            r1 = f1["domains"][dom]["tokenizers"][lab]["fertility"]
            print(f"  {dom:24s} {lab:18s} R2={v['fertility']:.9f} R1={r1:.9f} rel={pct(rel(v['fertility'], r1))}")

    h1_2 = load("r2_h1_calendar.json")
    h1_1 = load_r1("notations.json")["h1"]["years"]
    print("H1")
    for lab in ("TOKENIZATOREX", "Slayer1B"):
        for year in ("2024", "2026"):
            v = h1_2["per_year"][lab][year]
            r1 = h1_1[year][lab]["tokens_mean"]
            r1c = h1_1[year]["occurrences"]
            print(f"  {lab:18s} {year} mean R2={v['mean_tokens_per_occurrence']:.4f} R1={r1:.4f} "
                  f"count R2={v['occurrences']} R1={r1c} relcount={pct(rel(v['occurrences'], r1c))}")

    h5_2 = load("r2_h5_nfd.json")
    h5_1 = load_r1("robustness.json")["domains"]
    print("H5 per domain")
    for dom, e in h5_2["per_domain"].items():
        for lab in ("TOKENIZATOREX", "TOKENIZATOREX-HF", "Slayer1B"):
            v = e["tokenizers"][lab]["relative_increase"]
            r1 = h5_1[dom]["variants"]["nfd"]["tokenizers"][lab]["relative_increase"]
            print(f"  {dom:24s} {lab:18s} R2={pct(v)} R1={pct(r1)} rel={pct(rel(v, r1))}")
    print("H5 aggregate")
    agg1 = load_r1("robustness.json")["aggregate"]["variants"]["nfd"]["tokenizers"]
    for lab in ("TOKENIZATOREX", "TOKENIZATOREX-HF", "Slayer1B"):
        vals = [h5_2["per_domain"][d]["tokenizers"][lab]["relative_increase"] for d in h5_2["per_domain"]]
        mean2 = sum(vals) / len(vals)
        r1 = agg1[lab]["relative_increase_mean"]
        pooled = h5_2["total"][lab]["relative_increase"]
        print(f"  {lab:18s} R2pooled={pct(pooled)} R2mean={pct(mean2)} R1mean={pct(r1)} relmean={pct(rel(mean2, r1))}")

    h6_2 = load("r2_h6_superwords.json")
    h6_1 = load_r1("superwords.json")
    print("H6")
    print(f"  dict R2={h6_2['dict_share']:.6f} R1={h6_1['vocab']['midword_share_of_superwords']:.6f} "
          f"rel={pct(rel(h6_2['dict_share'], h6_1['vocab']['midword_share_of_superwords']))}")
    for scope, key in (("usage_all_test", "midword_uses_share"), ("usage_official7", None)):
        v = h6_2[scope]["share_of_all_occurrences"]
        if key:
            r1 = h6_1["usage"][key]
            print(f"  {scope:18s} share_all R2={v:.6f} R1={r1:.6f} rel={pct(rel(v, r1))}")
        print(f"  {scope:18s} share_super R2={h6_2[scope]['share_of_superword_occurrences']:.6f}")

    h8_2 = load("r2_h8_hf_parity.json")
    h8_1 = load_r1("hf_parity.json")["domains"]["przetargi_ogloszenia"]
    print("H8")
    for k2, k1 in (("share_identical_chunks", "identical_share"),
                   ("token_delta_hf_minus_ref", "token_delta"),
                   ("ref_tokens", "tokens_ours"), ("hf_tokens", "tokens_hf")):
        v2, v1 = h8_2[k2], h8_1[k1]
        print(f"  {k2:24s} R2={v2} R1={v1} rel={pct(rel(v2, v1)) if isinstance(v1, (int, float)) and v1 else None}")


if __name__ == "__main__":
    main()
