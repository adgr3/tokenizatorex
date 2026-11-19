"""Próbka 40 uchwał śląskich: text.html (to ma audyt) vs pełny text.pdf.

Teksty PDF tylko w raw_extra (gitignore). Wynik liczbowy: r3_slask_pdf.json.
"""
from __future__ import annotations

import io
import json
import os
import random
import sys
import time

import requests

from tokenizers import Tokenizer as HFTokenizer  # noqa: F401

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIT = os.path.dirname(HERE)
sys.path.append(AUDIT)

from common import build_encoders, clean_text, load_domain, sha256_text, word_count, write_json  # noqa: E402

RAW = os.path.join(HERE, "raw_extra", "samorzad_slask_pdf")
N = 40
SEED = 20261119
CORE = ["TOKENIZATOREX", "TOKENIZATOREX-HF", "Slayer1B", "Pollock-2.0", "APT3-1B"]


def pdf_text(raw: bytes) -> str:
    from pypdf import PdfReader
    return "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(raw)).pages)


def summarize(enc, docs):
    tok = words = 0
    for d in docs:
        t = d["text"]
        tok += len(enc.ids(t))
        words += len(t.split())
    return {"tokens": tok, "words": words, "fertility": tok / words if words else None}


def main() -> None:
    os.makedirs(RAW, exist_ok=True)
    docs = [d for d in load_domain("samorzad_uchwaly", "test")]
    rng = random.Random(SEED)
    rng.shuffle(docs)
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (compatible; tokenizer-audit/1.0)",
        "Accept": "*/*",
        "Accept-Language": "pl-PL,pl;q=0.9",
    })
    pairs = []
    skipped = 0
    for d in docs:
        if len(pairs) >= N:
            break
        # url .../text.html -> text.pdf
        url = d["url"]
        if not url.endswith("/text.html"):
            skipped += 1
            continue
        pdf_url = url[: -len("text.html")] + "text.pdf"
        try:
            r = s.get(pdf_url, timeout=90)
        except Exception as ex:  # noqa: BLE001
            print("skip", type(ex).__name__)
            continue
        if r.status_code != 200 or not r.content.startswith(b"%PDF") or len(r.content) > 4_000_000:
            skipped += 1
            continue
        try:
            text = clean_text(pdf_text(r.content))
        except Exception:  # noqa: BLE001
            skipped += 1
            continue
        if word_count(text) < 40:
            skipped += 1
            continue
        rec = {
            "id": d["id"],
            "url": pdf_url,
            "html_chars": len(d["text"]),
            "html_words": len(d["text"].split()),
            "pdf_chars": len(text),
            "pdf_words": word_count(text),
            "sha256_pdf": sha256_text(text),
            "text": text,
        }
        path = os.path.join(RAW, d["id"].replace("/", "_") + ".json")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(rec, f, ensure_ascii=False)
            f.write("\n")
        pairs.append(rec)
        print(f"  {len(pairs)}/{N} html {rec['html_chars']} -> pdf {rec['pdf_chars']} słów {rec['pdf_words']}")
        time.sleep(0.3)
    print("pobrano", len(pairs), "pominięto", skipped)
    print("tokenizery…")
    enc = build_encoders(CORE)
    html_docs = []
    pdf_docs = []
    by_id = {d["id"]: d for d in load_domain("samorzad_uchwaly", "test")}
    for rec in pairs:
        html_docs.append(by_id[rec["id"]])
        pdf_docs.append({"id": rec["id"], "text": rec["text"]})
    rows_h = {lab: summarize(enc[lab], html_docs) for lab in CORE}
    rows_p = {lab: summarize(enc[lab], pdf_docs) for lab in CORE}
    def rank(rows):
        return sorted(rows, key=lambda k: rows[k]["fertility"])
    out = {
        "n": len(pairs),
        "skipped": skipped,
        "seed": SEED,
        "note": "Ta sama uchwała: text.html (audyt, zwykle 1. strona) vs text.pdf (pełny akt). PDF >4 MB pominięte.",
        "html_chars_sum": sum(r["html_chars"] for r in pairs),
        "pdf_chars_sum": sum(r["pdf_chars"] for r in pairs),
        "html_words_sum": sum(r["html_words"] for r in pairs),
        "pdf_words_sum": sum(r["pdf_words"] for r in pairs),
        "median_pdf_over_html_chars": sorted(r["pdf_chars"] / r["html_chars"] for r in pairs)[len(pairs)//2],
        "html": rows_h,
        "pdf": rows_p,
        "rank_html": rank(rows_h),
        "rank_pdf": rank(rows_p),
        "per_doc": [{k: rec[k] for k in ("id", "url", "html_chars", "html_words", "pdf_chars", "pdf_words", "sha256_pdf")}
                    for rec in pairs],
    }
    write_json(os.path.join(HERE, "r3_slask_pdf.json"), out)
    print("rank html", out["rank_html"])
    print("rank pdf", out["rank_pdf"])
    print("chars", out["html_chars_sum"], "->", out["pdf_chars_sum"])


if __name__ == "__main__":
    main()
