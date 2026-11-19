"""Tworzy zamrożony zbiór zdań golden (dev + przypadki z załącznika A)."""
from __future__ import annotations

import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "audit", "data", "raw")
OUT = os.path.join(ROOT, "tkx_c", "golden", "dataset.json")
DOMAINS = ["przetargi_ogloszenia", "przetargi_kio", "samorzad_uchwaly",
           "granty_ogloszenia", "prawo_eli", "ocr_prasa", "tabele_json", "web"]
PER_DOMAIN = 150
SPLIT_RE = re.compile(r"(?<=[.!?])\s+|\n+")

CASES = [
    "1 234 567,89 zł",
    "wartość zamówienia: 2 450 000,00 zł brutto",
    "16 grudnia 2026 r.",
    "16.12.2026 r., godz. 12:00",
    "art. 5 ust. 2 pkt 3 lit. a",
    "Dz.U. z 2024 r. poz. 1320 ze zm.",
    "45233140-2",
    "ZP.271.12.2026",
    "KIO 1234/26",
    "NIP 123-456-32-18",
    "ul. Marszałkowska 140, 00-061 Warszawa",
    "Uchwała Nr XLII/1234/2026 Rady Miasta",
    "wkład własny 10%",
    "sekretariat@urzad.gov.pl",
    "Zażółć gęślą jaźń. ĄĆĘŁŃÓŚŹŻ.",
    "Wielkie litery: ZAMAWIAJĄCY OGŁASZA PRZETARG.",
    "Mieszany PL–EN: the offer deadline is 12.01.2026, zgodnie z SWZ.",
    "Nowa linia:\n\nDruga linia.\tTabulator.",
    "Emoji: zamówienie 🙂 📄 ✅ gotowe.",
]
for y in range(2015, 2036):
    CASES.append(f"w roku {y} r. zadanie")


def main() -> None:
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    texts: list[str] = []
    seen: set[str] = set()
    for dom in DOMAINS:
        ddir = os.path.join(RAW, dom)
        if not os.path.isdir(ddir):
            continue
        n, files = 0, sorted(os.listdir(ddir))
        for name in files:
            if n >= PER_DOMAIN:
                break
            doc = json.load(open(os.path.join(ddir, name), encoding="utf-8"))
            if doc.get("split") != "dev":
                continue
            for sent in SPLIT_RE.split(doc["text"]):
                sent = " ".join(sent.split())
                if not (20 <= len(sent) <= 220):
                    continue
                if sent in seen:
                    continue
                seen.add(sent)
                texts.append(sent)
                n += 1
                if n >= PER_DOMAIN:
                    break
    payload = {"seed": 20261119, "domains": DOMAINS, "per_domain": PER_DOMAIN,
               "sentences": texts + CASES,
               "note": "dev + załącznik A; bez testu; kolejność deterministyczna"}
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("zdań:", len(payload["sentences"]), "->", OUT)


if __name__ == "__main__":
    main()
