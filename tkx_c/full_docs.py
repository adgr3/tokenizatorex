"""Pobiera pełne (bez cięcia 20k) dokumenty do pomiaru kontekstu."""
from __future__ import annotations

import io
import json
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(ROOT, "audit"))
import prepare_corpus as pc  # noqa: E402
from common import SEED, clean_text  # noqa: E402
from pypdf import PdfReader  # noqa: E402

OUT = os.path.join(ROOT, "tkx_c", "data", "full_docs.json")
LIMIT = 20


def uchwaly_pdf() -> list[dict]:
    raw = pc.fetch("https://dzienniki.slask.eu/api/eli/acts/POL_WOJ_SL/2026")
    items = json.loads(raw.decode("utf-8"))["items"]
    items = [i for i in items if "uchwa" in (i.get("type") or "").lower()]
    random.Random(SEED).shuffle(items)
    out = []
    for it in items[:LIMIT]:
        addr = it.get("address") or it.get("eli")
        try:
            raw = pc.fetch(f"https://dzienniki.slask.eu/api/eli/acts/{addr}/text.pdf",
                           timeout=120)
            text = "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(raw)).pages)
        except Exception:
            continue
        text = clean_text(text)
        if len(text.split()) < 50:
            continue
        out.append({"id": "full-uchwala-" + addr.replace("/", "-"),
                    "domain": "samorzad_uchwaly",
                    "url": f"https://dzienniki.slask.eu/api/eli/acts/{addr}/text.pdf",
                    "date": (it.get("promulgation") or "")[:10], "text": text})
    return out


def main() -> None:
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    docs = []
    docs += [{"id": d.id, "domain": "przetargi_ogloszenia", "url": d.url,
              "date": d.date, "text": d.text}
             for d in pc.collect_bzp(limit=LIMIT)]
    docs += [{"id": d.id, "domain": "przetargi_kio", "url": d.url,
              "date": d.date, "text": d.text}
             for d in pc.collect_kio(limit=LIMIT)]
    docs += [{"id": d.id, "domain": "granty_ogloszenia", "url": d.url,
              "date": d.date, "text": d.text}
             for d in pc.collect_granty(limit=LIMIT)]
    docs += uchwaly_pdf()
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"note": "pełne dokumenty, świeża próbka z tych samych źródeł; nie test",
                   "documents": docs}, f, ensure_ascii=False)
        f.write("\n")
    for dom in ("przetargi_ogloszenia", "przetargi_kio", "granty_ogloszenia",
                "samorzad_uchwaly"):
        xs = [len(d["text"].split()) for d in docs if d["domain"] == dom]
        print(dom, len(xs), "docs", sum(xs), "words", max(xs) if xs else 0)


if __name__ == "__main__":
    main()
