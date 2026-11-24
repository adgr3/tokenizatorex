"""Poprawka 2: ta sama reguła, ale granty 149 zamiast 12 (jawnie po fakcie).

  python tkx_v21/wybierz_r2.py

Nie zmienia wyniku oryginalnego protokołu. Zapisuje kandydata warunkowego.
"""
from __future__ import annotations

import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(REPO, "results")
CANDIDATES = ["V0J2-32k", "V0J5-32k", "V0J10-32k"]
THRESHOLD = 1.01


def main():
    dev = json.load(open(os.path.join(R, "tkx_v21_dev.json"), encoding="utf-8"))
    orig = json.load(open(os.path.join(R, "tkx_v21_selection.json"), encoding="utf-8"))
    g149 = json.load(open(os.path.join(R, "tkx_v21_granty149.json"), encoding="utf-8"))
    base = "V0R-32k"
    out = {
        "rule": "jak PROTOKOL, ale granty 149 zamiast 12; poprawka po fakcie",
        "base": base, "threshold": THRESHOLD,
        "original_result": {"winner": orig.get("winner"),
                            "note": "wynik obowiazujacy wedlug protokolu"},
        "granty149": {
            "docs": g149["docs"],
            "fertility": {k: v["fertility"] for k, v in g149["tokenizers"].items()},
            "delta_vs_v0r_pct": {k: v.get("delta_vs_v0r_pct") for k, v in g149["tokenizers"].items()},
        },
        "candidates": {}, "conditional_winner": None,
    }
    feasible = []
    for c in CANDIDATES:
        rec = orig["candidates"].get(c, {})
        if not rec.get("present"):
            out["candidates"][c] = {"present": False}
            continue
        deltas = {s: dict(d) for s, d in rec["polish_deltas"].items()}
        d149 = g149["tokenizers"][c]
        base149 = g149["tokenizers"][base]
        deltas["granty"] = {
            "v0r": base149["fertility"], "variant": d149["fertility"],
            "delta_pct": (d149["fertility"] / base149["fertility"] - 1) * 100,
            "pass": d149["fertility"] <= THRESHOLD * base149["fertility"],
            "n": g149["docs"],
            "ci_v0r": base149["ci"], "ci_variant": d149["ci"],
        }
        fails = [s for s, d in deltas.items() if not d["pass"]]
        ok = not fails and rec.get("section_one_token", False)
        out["candidates"][c] = {
            "present": True,
            "json_dev_combined": rec["json_dev_combined"],
            "polish_deltas": deltas,
            "section_one_token": rec.get("section_one_token"),
            "feasible": ok, "fails": fails,
        }
        if ok:
            feasible.append((rec["json_dev_combined"]["fertility"], c))
    if feasible:
        feasible.sort()
        out["conditional_winner"] = feasible[0][1]
        out["conditional_note"] = ("kandydat warunkowy do potwierdzenia w TKX-D; "
                                   "NIE jest wybrany wedlug oryginalnego protokolu")
    else:
        out["conditional_note"] = "nawet z grantami 149 brak kandydata"
    with open(os.path.join(R, "tkx_v21_selection_r2.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps({"original": out["original_result"]["winner"],
                      "conditional": out["conditional_winner"],
                      "feasible": [c for _, c in feasible]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
