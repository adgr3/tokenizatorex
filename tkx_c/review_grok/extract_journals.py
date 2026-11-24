"""Wyciąga tekst z lokalnych PDF dziennika (mazowieckie) do raw_extra.

PDF-y zostały pobrane wcześniej spoza repozytorium. Do repozytorium
trafia tylko manifest (URL, SHA-256, liczba słów).
"""
from __future__ import annotations

import hashlib
import json
import os

import fitz

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw_extra")
os.makedirs(RAW, exist_ok=True)
DL = os.environ.get("TKX_GROK_DOWNLOADS", "grok-downloads")
# Pełny akt bywa bardzo długi. Sufit znaków jak przy TED, żeby jeden PDF
# nie zdominował bootstrapu dokumentów. Liczymy słowa na tekście, który
# naprawdę idzie do tokenizera.
CAP = 60000
SOURCES = [
    ("1.pdf", "https://edziennik.mazowieckie.pl/WDU_W/2024/1765/akt.pdf", "1765"),
    ("2.pdf", "https://edziennik.mazowieckie.pl/WDU_W/2024/7371/akt.pdf", "7371"),
]


def words(text: str) -> int:
    return len(text.split())


def extract(path: str) -> tuple[str, int, int]:
    doc = fitz.open(path)
    pages = doc.page_count
    parts = []
    thin = 0
    for i in range(pages):
        t = doc.load_page(i).get_text("text") or ""
        if len(t.split()) < 15:
            thin += 1
            continue
        parts.append(t)
    doc.close()
    text = "\n".join(parts).strip()
    return text, pages, thin


def main() -> None:
    docs = []
    for name, url, pos in SOURCES:
        path = os.path.join(DL, name)
        text, pages, thin = extract(path)
        full_words = words(text)
        truncated = len(text) > CAP
        if truncated:
            text = text[:CAP]
        if words(text) < 200:
            print("skip", pos, "words", words(text), "pages", pages, flush=True)
            continue
        rec = {
            "id": f"R3-extra-maz-{pos}",
            "source_tag": "R3-extra",
            "source": "edziennik_mazowieckie",
            "url": url,
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "words": words(text),
            "pages": pages,
            "thin_pages": thin,
            "full_words_before_cap": full_words,
            "truncated": truncated,
            "text": text,
        }
        out = os.path.join(RAW, rec["id"] + ".json")
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            json.dump(rec, f, ensure_ascii=False)
            f.write("\n")
        docs.append({k: rec[k] for k in (
            "id", "source_tag", "source", "url", "sha256", "words",
            "pages", "thin_pages", "full_words_before_cap", "truncated")})
        print("ok", rec["id"], rec["words"], "pages", pages, "thin", thin, flush=True)

    manifest_path = os.path.join(HERE, "r3_extra_manifest.json")
    prev = []
    if os.path.exists(manifest_path):
        prev = json.load(open(manifest_path, encoding="utf-8")).get("docs") or []
    have = {d["id"] for d in prev}
    for d in docs:
        if d["id"] not in have:
            prev.append(d)
        else:
            for i, old in enumerate(prev):
                if old["id"] == d["id"]:
                    prev[i] = d
    out = {"label": "R3-extra", "n": len(prev), "docs": prev}
    with open(manifest_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("manifest", out["n"], flush=True)


if __name__ == "__main__":
    main()
