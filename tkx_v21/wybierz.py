"""Reguła wyboru TKX-V21-JSON — czyta tylko wyniki dev (bez testu).

  python tkx_v21/wybierz.py

Wynik: results/tkx_v21_selection.json
"""
from __future__ import annotations

import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(REPO, "results")
CANDIDATES = ["V0J2-32k", "V0J5-32k", "V0J10-32k"]
POLISH = ["bzp_ogloszenia", "du_eli", "kio", "samorzad", "granty",
          "json_bzp_tabele", "general_web"]
THRESHOLD = 1.01  # +1% względem V0R


def main():
    dev = json.load(open(os.path.join(RESULTS, "tkx_v21_dev.json"), encoding="utf-8"))
    base = "V0R-32k"
    if base not in dev["tokenizers"]:
        raise SystemExit(f"brak {base} w tkx_v21_dev.json")
    out = {"rule": "min fertility JSON na dev; kazde polskie zrodlo <= 1.01 x V0R; § = 1 token",
           "base": base, "threshold": THRESHOLD, "candidates": {}, "winner": None}
    feasible = []
    for c in CANDIDATES:
        if c not in dev["tokenizers"]:
            out["candidates"][c] = {"present": False}
            continue
        deltas = {}
        ok = True
        fails = []
        for s in POLISH:
            b = dev["sources"][s]["tokenizers"][base]["fertility"]
            v = dev["sources"][s]["tokenizers"][c]["fertility"]
            d = (v / b - 1.0) * 100.0 if b else float("inf")
            deltas[s] = {"v0r": b, "variant": v, "delta_pct": d,
                         "pass": v <= THRESHOLD * b}
            if not deltas[s]["pass"]:
                ok = False
                fails.append(s)
        sec = dev["section_sign"][c]["one_token"]
        if not sec:
            ok = False
            fails.append("§")
        dev_fert = dev["tokenizers"][c]["json_dev_combined"]["fertility"]
        rec = {"present": True, "json_dev_combined": dev["tokenizers"][c]["json_dev_combined"],
               "polish_deltas": deltas, "section_one_token": sec,
               "feasible": ok, "fails": fails}
        out["candidates"][c] = rec
        if ok:
            feasible.append((dev_fert, c))
    if feasible:
        feasible.sort()
        out["winner"] = feasible[0][1]
        out["winner_json_dev_fertility"] = feasible[0][0]
        out["note"] = "kandydat do potwierdzenia w TKX-D; nie jest to wybór jakosci modelu"
    else:
        out["note"] = "brak kandydata spelniajacego warunek polski"
    with open(os.path.join(RESULTS, "tkx_v21_selection.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps({"winner": out["winner"], "feasible": [c for _, c in feasible]},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
