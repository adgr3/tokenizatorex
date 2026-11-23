"""sprawdz_liczby_v2.py — sprawdza spójność liczb w raportach z plikami wyników.

Sprawdza:
  - istnienie i poprawność JSON w results/tkx_v2_*.json
  - obecność wymaganych raportów i plików
  - (best-effort) czy liczby wymienione w raportach występują w plikach wyników

Użycie: python scripts/sprawdz_liczby_v2.py
"""
from __future__ import annotations

import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(REPO, "results")
REQUIRED_FILES = [
    "tkx_v2/KARTA_WYMAGAN.md",
    "tkx_v2/KORPUS_DOMENOWY.md",
    "tkx_v2/wzorce.json",
    "tkx_v2/RAPORT_TEST_DOMENOWY.md",
    "tkx_v2/RAPORT_PROSTY_V2.md",
    "tkx_v2/ZNANE_WADY.md",
    "RELEASE_NOTES_v2.0.md",
]


def main():
    ok = True
    print("== Sprawdzanie plików ==")
    for rel in REQUIRED_FILES:
        p = os.path.join(REPO, rel)
        status = "OK" if os.path.isfile(p) else "BRAK"
        if status != "OK":
            ok = False
        print(f"  {status:4s} {rel}")

    print("\n== Pliki wyników tkx_v2 ==")
    rfiles = sorted(f for f in os.listdir(RES) if f.startswith("tkx_v2_") and f.endswith(".json"))
    if not rfiles:
        print("  (brak plików tkx_v2_*.json)")
    for f in rfiles:
        p = os.path.join(RES, f)
        try:
            obj = json.load(open(p, encoding="utf-8"))
            print(f"  OK   {f}  ({os.path.getsize(p)} B)")
        except Exception as e:  # noqa: BLE001
            ok = False
            print(f"  ZLE  {f}: {e}")

    # best-effort: sprawdź czy liczby z raportów występują w wynikach
    results_text = ""
    for f in rfiles:
        results_text += open(os.path.join(RES, f), encoding="utf-8").read()
    for rel in ["tkx_v2/RAPORT_TEST_DOMENOWY.md", "tkx_v2/RAPORT_PROSTY_V2.md", "RELEASE_NOTES_v2.0.md"]:
        p = os.path.join(REPO, rel)
        if not os.path.isfile(p):
            continue
        content = open(p, encoding="utf-8").read()
        nums = set(re.findall(r"\b\d+\.\d+\b", content))
        missing = [n for n in nums if n not in results_text and len(rfiles) > 0]
        if missing and rfiles:
            print(f"\n  Uwaga: {rel} zawiera liczby nieobecne w wynikach: {missing[:10]}")
    print("\n" + ("STATUS=OK" if ok else "STATUS=BLOKER: brakujące pliki"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
