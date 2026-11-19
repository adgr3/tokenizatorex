"""R3-extra: dokumenty urzędowe z INNYCH źródeł niż zamrożony korpus.

Teksty lądują w audit/review_grok/raw_extra/ (gitignore).
Do repo idzie tylko manifest: URL, data, SHA-256, liczby.
Nie mieszać z audit/data/raw/.
"""
from __future__ import annotations

import hashlib
import html as html_lib
import io
import json
import os
import random
import re
import sys
import time
from xml.etree import ElementTree as ET

import requests

# H9: pakiet HF zanim repo wejdzie na sys.path.
from tokenizers import Tokenizer as HFTokenizer  # noqa: F401

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIT = os.path.dirname(HERE)
REPO = os.path.dirname(AUDIT)
sys.path.append(AUDIT)

from common import clean_text, sha256_text, word_count, write_json  # noqa: E402
from prepare_corpus import html_to_text  # noqa: E402

RAW = os.path.join(HERE, "raw_extra")
MANIFEST = os.path.join(HERE, "r3_extra_manifest.json")
TARGET = 40
SEED = 20261119
MIN_WORDS = 80
UA = {
    "User-Agent": "Mozilla/5.0 (compatible; tokenizer-audit/1.0)",
    "Accept": "*/*",
    "Accept-Language": "pl-PL,pl;q=0.9",
}


def session() -> requests.Session:
    s = requests.Session()
    s.headers.update(UA)
    return s


def save_doc(domain: str, doc_id: str, url: str, date: str, source: str, text: str) -> dict | None:
    text = clean_text(text)
    words = word_count(text)
    if words < MIN_WORDS:
        return None
    safe = re.sub(r"[^\w.\-]+", "_", doc_id)[:120]
    rec = {
        "id": safe,
        "domain": domain,
        "url": url,
        "date": (date or "")[:10],
        "source": source,
        "split": "R3-extra",
        "text": text,
        "words": words,
        "chars": len(text),
        "sha256": sha256_text(text),
    }
    d = os.path.join(RAW, domain)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, safe + ".json")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(rec, f, ensure_ascii=False)
        f.write("\n")
    public = {k: rec[k] for k in ("id", "domain", "url", "date", "source", "split", "words", "chars", "sha256")}
    return public


def pdf_text(raw: bytes) -> str:
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(raw))
    return "\n".join((p.extract_text() or "") for p in reader.pages)


def collect_uchwaly_ds(s: requests.Session, n: int = TARGET) -> list[dict]:
    """Dziennik Urzędowy Województwa Dolnośląskiego, pełny PDF (nie text.html)."""
    url = "https://edzienniki.duw.pl/api/eli/acts/POL_WOJ_DS/2026"
    print("DS lista…")
    items = s.get(url, timeout=120).json()["items"]
    uch = [it for it in items if "uchwa" in (it.get("type") or "").lower() and it.get("pos")]
    rng = random.Random(SEED)
    rng.shuffle(uch)
    out = []
    skipped_big = 0
    for it in uch:
        if len(out) >= n:
            break
        address = it.get("address") or f"POL_WOJ_DS/2026/{it['pos']}"
        pdf_url = f"https://edzienniki.duw.pl/api/eli/acts/{address}/text.pdf"
        try:
            r = s.get(pdf_url, timeout=90)
        except Exception as ex:  # noqa: BLE001
            print("  skip", address, type(ex).__name__)
            continue
        if r.status_code != 200 or len(r.content) < 500:
            continue
        if len(r.content) > 4_000_000:
            skipped_big += 1
            continue
        if not r.content.startswith(b"%PDF"):
            continue
        try:
            text = pdf_text(r.content)
        except Exception:  # noqa: BLE001
            continue
        date = (it.get("announcementDate") or it.get("promulgation") or "")[:10]
        rec = save_doc(
            "samorzad_uchwaly",
            "ds-" + address.replace("/", "-"),
            pdf_url,
            date,
            "Dziennik Urzędowy Województwa Dolnośląskiego (ELI text.pdf, nie śląski)",
            text,
        )
        if rec:
            out.append(rec)
            print(f"  DS {len(out)}/{n} poz.{it.get('pos')} słowa {rec['words']} znaki {rec['chars']}")
        time.sleep(0.35)
    print(f"DS zebrano {len(out)}, pominięto PDF >4 MB: {skipped_big}")
    return out


def ted_polish(xml: str) -> str:
    root = ET.fromstring(xml)
    chunks = []
    for el in root.iter():
        if any(k.endswith("languageID") and v == "POL" for k, v in el.attrib.items()):
            txt = "".join(el.itertext()).strip()
            if txt:
                chunks.append(txt)
    # bez zagnieżdżonych duplikatów: zostaw fragmenty dłuższe niż rodzic już wziął
    # iter() daje rodzica i dzieci; dzieci powielają tekst. Bierzemy tylko liście z POL.
    leaves = []
    for el in root.iter():
        if not any(k.endswith("languageID") and v == "POL" for k, v in el.attrib.items()):
            continue
        if any(True for _ in list(el)):
            continue
        txt = (el.text or "").strip()
        if txt:
            leaves.append(txt)
    use = leaves or chunks
    return "\n".join(use)


def collect_ted(s: requests.Session, n: int = TARGET) -> list[dict]:
    """Ogłoszenia TED (zamówienia PL), nie e-Zamówienia/BZP."""
    out = []
    seen = set()
    page = 1
    while len(out) < n and page <= 4:
        body = {
            "query": "buyer-country=POL AND form-type=competition AND publication-date>=20260101",
            "fields": ["publication-number", "publication-date", "buyer-country"],
            "limit": 50,
            "paginationMode": "PAGE_NUMBER",
            "page": page,
        }
        r = s.post("https://api.ted.europa.eu/v3/notices/search", json=body, timeout=60)
        r.raise_for_status()
        notices = r.json().get("notices") or []
        if not notices:
            break
        for note in notices:
            if len(out) >= n:
                break
            num = note.get("publication-number")
            if not num or num in seen:
                continue
            seen.add(num)
            xml_url = f"https://ted.europa.eu/en/notice/{num}/xml"
            try:
                xr = s.get(xml_url, timeout=60)
            except Exception as ex:  # noqa: BLE001
                print("  TED", num, type(ex).__name__)
                continue
            if xr.status_code != 200 or b"<" not in xr.content[:200]:
                continue
            try:
                text = ted_polish(xr.text)
            except Exception:  # noqa: BLE001
                continue
            date = (note.get("publication-date") or "")[:10]
            rec = save_doc(
                "przetargi_ogloszenia",
                "ted-" + num.replace("/", "-"),
                xml_url,
                date,
                "TED Search API v3 (buyer-country=POL, form-type=competition), tekst languageID=POL",
                text,
            )
            if rec:
                out.append(rec)
                print(f"  TED {len(out)}/{n} {num} słowa {rec['words']}")
            time.sleep(0.3)
        page += 1
    print(f"TED zebrano {len(out)}")
    return out


def strip_html(text: str) -> str:
    text = re.sub(r"(?is)<script[^>]*>.*?</script>", " ", text)
    text = re.sub(r"(?is)<style[^>]*>.*?</style>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    return html_lib.unescape(text)


def collect_saos(s: requests.Session, n: int = TARGET) -> list[dict]:
    """Orzeczenia sądów o zamówieniach publicznych (SAOS), nie UZP/KIO."""
    out = []
    page = 0
    while len(out) < n and page < 15:
        r = s.get(
            "https://www.saos.org.pl/api/search/judgments",
            params={
                "pageSize": 20,
                "pageNumber": page,
                "all": "zamówienia publiczne",
                "judgmentDateFrom": "2025-01-01",
                "sortingField": "JUDGMENT_DATE",
                "sortingDirection": "DESC",
            },
            timeout=60,
        )
        r.raise_for_status()
        items = r.json().get("items") or []
        if not items:
            break
        for it in items:
            if len(out) >= n:
                break
            href = it.get("href")
            if not href:
                continue
            try:
                full = s.get(href, timeout=60).json()
            except Exception:  # noqa: BLE001
                continue
            data = full.get("data") or {}
            raw_txt = data.get("textContent") or ""
            if len(raw_txt) < 400:
                continue
            date = (data.get("judgmentDate") or it.get("judgmentDate") or "")[:10]
            rec = save_doc(
                "przetargi_kio",
                "saos-" + str(data.get("id") or it.get("id")),
                href,
                date,
                "SAOS (saos.org.pl) — orzeczenia sądów powszechnych, zapytanie „zamówienia publiczne”; nie UZP/KIO",
                strip_html(raw_txt),
            )
            if rec:
                out.append(rec)
                print(f"  SAOS {len(out)}/{n} {rec['id']} słowa {rec['words']}")
            time.sleep(0.25)
        page += 1
    print(f"SAOS zebrano {len(out)}")
    return out


def collect_ncn(s: requests.Session, n: int = TARGET) -> list[dict]:
    """Ogłoszenia konkursów NCN, nie NIW."""
    r = s.get("https://ncn.gov.pl/konkursy-krajowe", timeout=60)
    r.raise_for_status()
    hrefs = sorted(set(re.findall(r'href="(/ogloszenia/konkursy/[a-z0-9\-]+)"', r.text)))
    rng = random.Random(SEED)
    rng.shuffle(hrefs)
    out = []
    recent, rest = [], []
    checked = 0
    for href in hrefs:
        if len(out) >= n or checked >= 90:
            break
        url = "https://ncn.gov.pl" + href
        try:
            page = s.get(url, timeout=40)
        except Exception:  # noqa: BLE001
            continue
        checked += 1
        if page.status_code != 200:
            continue
        text = html_to_text(page.text)
        if word_count(text) < 200:
            continue
        bucket = recent if re.search(r"202[4-6]", text) else rest
        bucket.append((url, text))
        time.sleep(0.2)
        # jak tylko mamy dość nowych, nie czytaj dalej
        if len(recent) >= n:
            break
    pool = recent + rest
    for url, text in pool:
        if len(out) >= n:
            break
        slug = url.rstrip("/").split("/")[-1]
        rec = save_doc(
            "granty_ogloszenia",
            "ncn-" + slug,
            url,
            "",
            "Narodowe Centrum Nauki (ncn.gov.pl/ogloszenia/konkursy), nie NIW",
            text,
        )
        if rec:
            # data z tekstu, jeśli jest rok
            m = re.search(r"(202[4-6])", text)
            rec["date"] = (m.group(1) + "-01-01") if m else ""
            out.append(rec)
            print(f"  NCN {len(out)}/{n} {slug} słowa {rec['words']}")
    print(f"NCN zebrano {len(out)} (kandydatów z rokiem 2024–2026: {len(recent)}, sprawdzonych stron: {checked})")
    return out


def main() -> None:
    s = session()
    docs = []
    docs += collect_uchwaly_ds(s)
    docs += collect_ted(s)
    docs += collect_saos(s)
    docs += collect_ncn(s)
    # daty NCN dopisane po save_doc — zsynchronizuj plik
    for rec in docs:
        if rec["domain"] == "granty_ogloszenia" and rec.get("date"):
            path = os.path.join(RAW, rec["domain"], rec["id"] + ".json")
            if os.path.exists(path):
                full = json.load(open(path, encoding="utf-8"))
                full["date"] = rec["date"]
                with open(path, "w", encoding="utf-8", newline="\n") as f:
                    json.dump(full, f, ensure_ascii=False)
                    f.write("\n")
    by = {}
    for d in docs:
        by.setdefault(d["domain"], 0)
        by[d["domain"]] += 1
    manifest = {
        "label": "R3-extra",
        "note": "Nowe dokumenty, inne źródła niż zamrożony test. Tekst tylko w raw_extra/ (gitignore).",
        "target_per_domain": TARGET,
        "counts": by,
        "documents": docs,
    }
    write_json(MANIFEST, manifest)
    print("MANIFEST", MANIFEST, by)


if __name__ == "__main__":
    main()
