"""Długości pełnych uchwał (PDF) w tokenach TKX-HF oraz sonda lat.

Nie cytuje tekstów dokumentów. Wynik: r3_doc_lengths_extra.json.
"""
from __future__ import annotations

import json
import os
import re
import sys

import numpy as np
from tokenizers import Tokenizer as HFTokenizer  # noqa: F401  H9

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIT = os.path.dirname(HERE)
sys.path.append(AUDIT)

from common import build_encoders, percentile, write_json  # noqa: E402


def pack(xs: list[int]) -> dict:
    return {
        "docs": len(xs),
        "median": percentile(xs, 0.5) if xs else None,
        "p90": percentile(xs, 0.9) if xs else None,
        "mean": float(np.mean(xs)) if xs else None,
        "max": max(xs) if xs else None,
        "fit_2048": (sum(1 for x in xs if x <= 2048) / len(xs)) if xs else None,
        "fit_4096": (sum(1 for x in xs if x <= 4096) / len(xs)) if xs else None,
    }


def load_docs(domain: str) -> list[dict]:
    d = os.path.join(HERE, "raw_extra", domain)
    docs = []
    for name in sorted(os.listdir(d)):
        if name.endswith(".json"):
            docs.append(json.load(open(os.path.join(d, name), encoding="utf-8")))
    return docs


def main() -> None:
    encoders = build_encoders(["TOKENIZATOREX", "TOKENIZATOREX-HF"])
    hf = encoders["TOKENIZATOREX-HF"]
    strings = []
    for i in range(hf.vocab):
        try:
            strings.append(hf.decode([i]))
        except Exception:  # noqa: BLE001
            strings.append("")

    out = {"tokenizer": "TOKENIZATOREX-HF", "domains": {}}
    for dom in ("samorzad_slask_pdf", "samorzad_uchwaly"):
        docs = load_docs(dom)
        cur, upper, lower, words = [], [], [], []
        for d in docs:
            text = d["text"]
            ids = hf.ids(text)
            base = len(ids)
            up = extra = 0
            for i in ids:
                s = strings[i] if 0 <= i < len(strings) else ""
                digits = sum(ch.isdigit() for ch in s)
                if digits == 0:
                    up += 1
                else:
                    nond = any(not ch.isdigit() for ch in s)
                    up += digits + (1 if nond else 0)
                    extra += max(0, digits - 1)
            cur.append(base)
            upper.append(up)
            lower.append(base + extra)
            words.append(len(text.split()))
        out["domains"][dom] = {
            "docs": len(docs),
            "words": pack(words),
            "current": pack(cur),
            "digits_lower": pack(lower),
            "digits_upper": pack(upper),
        }
        print(dom, "med", out["domains"][dom]["current"]["median"],
              "p90", out["domains"][dom]["current"]["p90"],
              "fit2048", out["domains"][dom]["current"]["fit_2048"])

    years = {}
    probes = [2015, 2024, 2025, 2026, 2027]
    for lab, enc in encoders.items():
        years[lab] = {}
        for y in probes:
            sent = f"w roku {y} r. zadanie"
            ids = enc.ids(sent)
            pieces = [enc.decode([i]) for i in ids]
            years[lab][str(y)] = {"tokens": len(ids), "pieces": pieces,
                                  "roundtrip": enc.decode(ids) == sent}
    out["year_probe"] = {
        "sentence": "w roku RRRR r. zadanie",
        "note": "Zdanie syntetyczne, nie z korpusu. Sprawdza, czy lata 2025–2027 nadal kosztują więcej niż 2024.",
        "by_tokenizer": years,
    }

    man = json.load(open(os.path.join(HERE, "r3_extra_manifest.json"), encoding="utf-8"))
    year_in_id = {}
    no_year = 0
    for doc in man["documents"]:
        if doc["domain"] != "granty_ogloszenia":
            continue
        m = re.findall(r"20[0-9]{2}", doc["id"])
        if not m:
            no_year += 1
            continue
        y = m[-1]
        year_in_id[y] = year_in_id.get(y, 0) + 1
    out["ncn_year_in_id"] = {"with_year": year_in_id, "id_without_year": no_year,
                             "note": "Rok wyciągnięty ze sluga w manifeście. Filtr strony łapał stopkę, więc zbiór nie jest ograniczony do 2024–2026."}

    markers = {"ezamowienia": 0, "BZP": 0, "docs": 0}
    ted = os.path.join(HERE, "raw_extra", "przetargi_ogloszenia")
    for name in os.listdir(ted):
        if not name.endswith(".json"):
            continue
        raw = open(os.path.join(ted, name), encoding="utf-8").read()
        markers["docs"] += 1
        if "ezamowienia" in raw.lower():
            markers["ezamowienia"] += 1
        if "BZP" in raw:
            markers["BZP"] += 1
    out["ted_overlap_markers"] = markers
    out["ted_note"] = "Liczba plików TED, w których występuje napis. To nie jest identyfikacja tego samego postępowania, tylko sygnał, że ogłoszenie TED bywa tym samym gatunkiem co BZP."

    write_json(os.path.join(HERE, "r3_doc_lengths_extra.json"), out)
    print("year", json.dumps(years, ensure_ascii=False))
    print("ncn", year_in_id, "no_year", no_year)
    print("ted", markers)


if __name__ == "__main__":
    main()
