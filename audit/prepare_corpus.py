"""Zbieranie i zamrażanie korpusu audytowego TKX-A (rundа 0).

Zasady:
* tylko źródła publiczne, bez logowania i bez akceptacji regulaminu;
* teksty zostają lokalnie (``audit/data/raw/``, gitignore), do repo idzie
  ``audit/data/MANIFEST.json`` (URL, data, dziedzina, podział, słowa, SHA-256);
* deterministyczny podział dev (40%) / test (60%) po dokumentach, seed 20261119;
* normalizacja tylko białych znaków — BEZ NFC/NFKC (H5 musi być mierzalne);
* dokumenty < 50 słów odrzucane (i liczone).

Użycie:
    python audit/prepare_corpus.py --only prawo_eli przetargi_kio
    python audit/prepare_corpus.py --manifest
"""
from __future__ import annotations

import argparse
import base64
import html as html_lib
import json
import os
import random
import re
import sys
import time
import unicodedata
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

import requests

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common import (BENCH_DIR, CACHE_DIR, MANIFEST_PATH, RAW_DIR, SEED, DEV_SHARE,
                    Document, clean_text, ensure_dirs, is_nfd, load_domain,
                    save_document, sha256_bytes, sha256_text, word_count, write_json)

UA = {"User-Agent": "Mozilla/5.0 (kompatybilny; audyt tokenizera; kontakt: repo adgr3/tokenizatorex)"}
MIN_WORDS = 50
DOC_CAP = 20_000
EXISTING_TARGET_BYTES = 2_000_000
OFFICIAL_DOMAIN_TARGET = {
    "przetargi_ogloszenia": (120, 100_000),
    "przetargi_kio": (110, 100_000),
    "samorzad_uchwaly": (400, 100_000),
    "granty_ogloszenia": (110, 100_000),
    "prawo_eli": (130, 100_000),
    "ocr_prasa": (60, 50_000),
    "tabele_json": (120, 50_000),
}
EXISTING_DOMAINS = ["web", "wikipedia", "literatura", "prawo", "sejm", "nauka", "dyskusje", "angielski"]

DYNAWORD = "https://huggingface.co/datasets/SlayerLab/polish-dynaword/resolve/main/data"
DYNAWORD_FILES = {
    "wikipedia": f"{DYNAWORD}/wikipedia/wikipedia.parquet",
    "literatura": f"{DYNAWORD}/wolne_lektury/wolne_lektury.parquet",
    "prawo": f"{DYNAWORD}/dziennik_ustaw/dziennik_ustaw.parquet",
    "sejm": f"{DYNAWORD}/sejm_committee_transcripts/sejm_committee_transcripts.parquet",
    "nauka": f"{DYNAWORD}/biblioteka_nauki/biblioteka_nauki.parquet",
    "dyskusje": f"{DYNAWORD}/plwiki_talk/plwiki_talk.parquet",
}
WIKITEXT = "https://huggingface.co/datasets/Salesforce/wikitext/resolve/main/wikitext-103-raw-v1/test-00000-of-00001.parquet"
HPLT = ("https://huggingface.co/datasets/SlayerLab/hplt-v3-pl-cleaned/resolve/main/"
        "data/european_hplt_v3_pl_bin8_5_p1.parquet")

# ---------------------------------------------------------------------------
# HTTP z cache (żeby ponowne uruchomienie nie obciążało źródeł)
# ---------------------------------------------------------------------------

def fetch(url: str, method: str = "GET", data=None, json_body=None,
          timeout: int = 90, retries: int = 3, refresh: bool = False,
          headers: dict | None = None) -> bytes:
    ensure_dirs()
    key_src = method + " " + url + " " + repr(data) + repr(json_body)
    key = sha256_bytes(key_src.encode("utf-8"))[:32]
    path = os.path.join(CACHE_DIR, key + ".bin")
    if os.path.exists(path) and not refresh:
        with open(path, "rb") as f:
            return f.read()
    h = dict(UA)
    if headers:
        h.update(headers)
    last = None
    for attempt in range(retries):
        try:
            if method == "GET":
                r = requests.get(url, timeout=timeout, headers=h)
            else:
                r = requests.post(url, data=data, json=json_body, timeout=timeout, headers=h)
            if r.status_code == 200:
                with open(path, "wb") as f:
                    f.write(r.content)
                with open(os.path.join(CACHE_DIR, key + ".json"), "w", encoding="utf-8") as f:
                    json.dump({"url": url, "method": method, "status": 200,
                               "content_type": r.headers.get("content-type")}, f, ensure_ascii=False)
                return r.content
            last = f"HTTP {r.status_code}"
        except Exception as ex:  # noqa: BLE001
            last = f"{type(ex).__name__}: {ex}"
        time.sleep(2 + attempt * 3)
    raise RuntimeError(f"nie udało się pobrać {url}: {last}")


# ---------------------------------------------------------------------------
# HTML -> tekst
# ---------------------------------------------------------------------------

BLOCK_TAGS = {"p", "div", "br", "li", "tr", "td", "th", "h1", "h2", "h3", "h4",
              "h5", "h6", "section", "article", "header", "footer", "table",
              "blockquote", "pre", "ul", "ol", "dd", "dt", "figcaption"}


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript", "svg"):
            self.skip += 1
        if tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript", "svg"):
            self.skip = max(0, self.skip - 1)
        if tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def html_to_text(html: str) -> str:
    p = TextExtractor()
    p.feed(html)
    return clean_text(html_lib.unescape("".join(p.parts)))


def extract_div(html: str, class_name: str) -> str:
    """Wyciąga pierwszy <div class="..."> z zawartością (bez zagnieżdżania tagów)."""
    m = re.search(r'<div[^>]*class="[^"]*\b' + re.escape(class_name) + r'\b[^"]*"[^>]*>', html)
    if not m:
        return ""
    depth, i = 1, m.end()
    tag_re = re.compile(r"<(/?)div\b[^>]*>", re.I)
    parts = []
    while depth and i < len(html):
        n = tag_re.search(html, i)
        if not n:
            parts.append(html[i:])
            break
        parts.append(html[i:n.start()])
        depth += -1 if n.group(1) else 1
        i = n.end()
    return html_to_text("".join(parts))


# ---------------------------------------------------------------------------
# Kolektory
# ---------------------------------------------------------------------------

def collect_bzp(refresh: bool = False, notice_type: str = "ContractNotice",
                limit: int = 120, as_json: bool = False, prefix: str = "bzp") -> list[Document]:
    api = "https://ezamowienia.gov.pl/mo-board/api/v1/notice"
    docs: list[Document] = []
    page = 1
    while len(docs) < limit and page <= 6:
        params = (f"?NoticeType={notice_type}&PublicationDateFrom=2026-01-01T00:00:00"
                  f"&PublicationDateTo=2026-11-19T23:59:59&PageSize=100&PageNumber={page}")
        try:
            raw = fetch(api + params, refresh=refresh)
        except Exception as ex:  # noqa: BLE001
            print(f"  BZP strona {page}: {ex}")
            break
        items = json.loads(raw.decode("utf-8"))
        if not items:
            break
        for it in items:
            if len(docs) >= limit:
                break
            body = it.get("htmlBody") or ""
            text = html_to_text(body)
            if as_json:
                rec = {
                    "numer_ogloszenia": it.get("noticeNumber"),
                    "rodzaj_ogloszenia": it.get("noticeType"),
                    "data_publikacji": it.get("publicationDate"),
                    "zamawiajacy": it.get("organizationName"),
                    "miejscowosc": it.get("organizationCity"),
                    "wojewodztwo": it.get("organizationProvince"),
                    "przedmiot_zamowienia": it.get("orderObject"),
                    "kody_cpv": it.get("cpvCode"),
                    "termin_skladania_ofert": it.get("submittingOffersDate"),
                    "identyfikator": it.get("tenderId"),
                    "tresc_ogloszenia": text,
                }
                text = json.dumps(rec, ensure_ascii=False, indent=2)
            if word_count(text) < MIN_WORDS:
                continue
            nid = it.get("noticeNumber") or it.get("tenderId") or f"page{page}"
            date = (it.get("publicationDate") or "")[:10]
            docs.append(Document(
                id=f"{prefix}-{nid}", domain="", url="https://ezamowienia.gov.pl/mo-client-board/bzp/notice-details/"
                + str(it.get("tenderId", "")), date=date, text=text,
                source="e-Zamówienia / BZP API (mo-board/api/v1/notice)"))
        page += 1
        time.sleep(2.2)  # limit 30 zapytań/min
    return docs


def collect_kio(refresh: bool = False, limit: int = 110) -> list[Document]:
    api = "https://orzeczenia.uzp.gov.pl/Home/GetResults"
    docs: list[Document] = []
    pg = 1
    while len(docs) < limit and pg <= 20:
        data = {"Phrase": "zamówienia publiczne", "Fle": "1", "SCnt": "1",
                "CountStats": "True", "Kind": "KIO", "Pg": str(pg),
                "Srt": "date_desc", "Dt": "01-01-2026 - 19-11-2026"}
        try:
            raw = fetch(api, method="POST", data=data, refresh=refresh,
                        headers={"X-Requested-With": "XMLHttpRequest"})
        except Exception as ex:  # noqa: BLE001
            print(f"  KIO strona {pg}: {ex}")
            break
        h = raw.decode("utf-8", errors="replace")
        ids = re.findall(r"/Home/Details/(\d+)", h)
        if not ids:
            break
        for did in ids:
            if len(docs) >= limit:
                break
            try:
                ch = fetch(f"https://orzeczenia.uzp.gov.pl/Home/ContentHtml/{did}?Kind=KIO&flection=0",
                           refresh=refresh).decode("utf-8", errors="replace")
            except Exception:  # noqa: BLE001
                continue
            text = html_to_text(ch)
            idx = text.upper().rfind("UZASADNIENIE")
            if idx >= 0:
                text = text[idx:]
            j = text.find("Sygn. akt")
            if j > 0:
                text = text[j:]
            try:
                det = fetch(f"https://orzeczenia.uzp.gov.pl/Home/Details/{did}", refresh=refresh)
                det_text = html_to_text(det.decode("utf-8", errors="replace"))
                m = re.search(r"Data wydania rozstrzygni[^0-9]*(\d{2}-\d{2}-\d{4})", det_text)
            except Exception:  # noqa: BLE001
                m = None
            date = ""
            if m:
                dd, mm, yy = m.group(1).split("-")
                date = f"{yy}-{mm}-{dd}"
            if word_count(text) < MIN_WORDS:
                continue
            docs.append(Document(
                id=f"kio-{did}", domain="", url=f"https://orzeczenia.uzp.gov.pl/Home/Details/{did}",
                date=date or "2026", text=text,
                source="UZP – wyszukiwarka orzeczeń (tylko uzasadnienie)"))
        pg += 1
        time.sleep(0.5)
    return docs


def collect_uchwaly(refresh: bool = False, limit: int = 140) -> list[Document]:
    api = "https://dzienniki.slask.eu/api/eli/acts/POL_WOJ_SL/2026"
    items = json.loads(fetch(api, refresh=refresh).decode("utf-8"))["items"]
    uch = [i for i in items if "uchwa" in (i.get("type") or "").lower()]
    random.Random(SEED).shuffle(uch)
    docs: list[Document] = []
    for it in uch:
        if len(docs) >= limit:
            break
        address = it.get("address") or it.get("eli")
        try:
            raw = fetch(f"https://dzienniki.slask.eu/api/eli/acts/{address}/text.html",
                        refresh=refresh)
        except Exception:  # noqa: BLE001
            continue
        text = html_to_text(raw.decode("utf-8", errors="replace"))
        if word_count(text) < MIN_WORDS:
            continue
        docs.append(Document(
            id="uchwala-" + address.replace("/", "-"), domain="",
            url=f"https://dzienniki.slask.eu/api/eli/acts/{address}/text.html",
            date=(it.get("promulgation") or it.get("announcementDate") or "")[:10],
            text=text, source="Dziennik Urzędowy Województwa Śląskiego (ELI API)"))
    return docs


def collect_eli(refresh: bool = False, limit: int = 130) -> list[Document]:
    from pypdf import PdfReader
    import io
    api = "https://api.sejm.gov.pl/eli/acts/DU/2026"
    items = json.loads(fetch(api, refresh=refresh).decode("utf-8"))["items"]
    random.Random(SEED).shuffle(items)
    docs: list[Document] = []
    for it in items:
        if len(docs) >= limit:
            break
        eli = it["ELI"]
        try:
            raw = fetch(f"https://api.sejm.gov.pl/eli/acts/{eli}/text.pdf", refresh=refresh)
            reader = PdfReader(io.BytesIO(raw))
            text = "\n".join((p.extract_text() or "") for p in reader.pages)
        except Exception:  # noqa: BLE001
            continue
        text = clean_text(text)
        if word_count(text) < MIN_WORDS:
            continue
        title = it.get("title") or ""
        docs.append(Document(
            id="eli-" + eli.replace("/", "-"), domain="", url=f"https://api.sejm.gov.pl/eli/acts/{eli}",
            date=(it.get("announcementDate") or it.get("promulgation") or "")[:10],
            text=title + "\n" + text, source="API ELI Sejmu (Dz.U. 2026, PDF)"))
    return docs


NIW_KW = ("konkurs", "nabor", "nabór", "dotacj", "grant", "regulamin", "wniosk",
          "finansow", "projekt", "program", "oferty")


def _sitemap_urls(url: str, refresh: bool) -> list[tuple[str, str]]:
    try:
        raw = fetch(url, refresh=refresh).decode("utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        return []
    out = []
    for block in re.findall(r"<url>(.*?)</url>", raw, re.S):
        loc = re.search(r"<loc>([^<]+)</loc>", block)
        lm = re.search(r"<lastmod>([^<]+)</lastmod>", block)
        if loc:
            out.append((loc.group(1).strip(), (lm.group(1).strip()[:10] if lm else "")))
    return out


def collect_granty(refresh: bool = False, limit: int = 110) -> list[Document]:
    """Ogłoszenia konkursów i regulaminy: NIW (strony, aktualności, publiczne PDF-y).

    Data dokumentu: dla PDF — rok/miesiąc z katalogu uploadu (``/uploads/RRRR/MM``),
    dla stron HTML — ``datePublished`` z JSON-LD (bez daty = pomijamy). Dwa przebiegi:
    najpierw dokumenty z 2026 r. (by spełnić warunek ≥50%), potem reszta.
    """
    from pypdf import PdfReader
    import io

    cand: list[tuple[str, str]] = []
    for i in range(1, 5):
        cand += _sitemap_urls(f"https://niw.gov.pl/page-sitemap{i}.xml", refresh)
    cand += _sitemap_urls("https://niw.gov.pl/nasze_programy-sitemap.xml", refresh)
    for i in range(1, 5):
        cand += _sitemap_urls(f"https://niw.gov.pl/post-sitemap{i}.xml", refresh)
    seen, uniq = set(), []
    for u, d in cand:
        if u in seen or "niw.gov.pl" not in u:
            continue
        seen.add(u)
        uniq.append((u, d))
    uniq.sort(key=lambda x: (not x[1].startswith("2026"), x[0]))
    random.Random(SEED).shuffle(uniq[int(len(uniq) * 0.7):])

    docs: list[Document] = []
    pdf_seen: set[str] = set()
    seen_text: set[str] = set()

    def add(url: str, date: str, text: str, source: str) -> bool:
        if len(docs) >= limit or not date:
            return False
        h = sha256_text(text)
        if h in seen_text:
            return False
        seen_text.add(h)
        docs.append(Document(id="grant-" + sha256_text(url)[:12], domain="", url=url,
                             date=date, text=text, source=source))
        return True

    for phase in ("2026", "all"):
        for u, lm in uniq:
            if len(docs) >= limit:
                break
            try:
                h = fetch(u, refresh=refresh).decode("utf-8", errors="replace")
            except Exception:  # noqa: BLE001
                continue
            m = re.search(r'"datePublished"\s*:\s*"([^"]+)"', h)
            page_date = m.group(1)[:10] if m else ""
            body = extract_div(h, "entry-content") or ""
            u_kw = any(k in u.lower() for k in ("konkurs", "nabor", "regulamin", "ogloszenie",
                                                "dotacj", "grant", "fundusz", "wniosk", "projekt", "program"))
            b_kw = sum(1 for k in NIW_KW if k in body.lower())
            if (page_date and word_count(body) >= 300 and u_kw and b_kw >= 3
                    and (phase == "all" or page_date.startswith("2026"))):
                add(u, page_date, body, "Narodowy Instytut Wolności (strona publiczna)")
            for pu in re.findall(r'href="(https://niw\.gov\.pl/[^"]+\.pdf)"', h, re.I)[:10]:
                if len(docs) >= limit:
                    break
                if pu in pdf_seen:
                    continue
                pdf_seen.add(pu)
                mm = re.search(r"/uploads/(\d{4})/(\d{2})/", pu)
                pdf_date = f"{mm.group(1)}-{mm.group(2)}-01" if mm else lm
                if phase == "2026" and not pdf_date.startswith("2026"):
                    continue
                try:
                    raw = fetch(pu, refresh=refresh, timeout=120)
                    text = clean_text("\n".join((p.extract_text() or "") for p in
                                                 PdfReader(io.BytesIO(raw)).pages))
                except Exception:  # noqa: BLE001
                    continue
                if word_count(text) < 200 or not any(k in text.lower() for k in NIW_KW):
                    continue
                add(pu, pdf_date, text, "Narodowy Instytut Wolności (PDF publiczny)")
            if phase == "2026" and len(docs) >= 55:
                # wystarczająco dużo 2026; dalej dobieramy już dowolne
                if len(docs) >= limit:
                    break
    return docs


def collect_polona(refresh: bool = False, limit: int = 60, max_pages: int = 6) -> list[Document]:
    docs: list[Document] = []
    seen: set[str] = set()
    for seed in range(1, 60):
        if len(docs) >= limit:
            break
        url = (f"https://polona2.pl/api/entities/?seed={seed}&size=100"
               f"&filters=has_text_content:1")
        try:
            raw = fetch(url, refresh=refresh).decode("utf-8", errors="replace")
            hits = json.loads(raw)["hits"]
        except Exception:  # noqa: BLE001
            continue
        for h in hits:
            if len(docs) >= limit:
                break
            if h.get("id") in seen or not h.get("is_public") or not h.get("has_text_content"):
                continue
            date = (h.get("date") or "")[:10]
            if not date or date >= "1940":
                continue
            seen.add(h["id"])
            try:
                ent = json.loads(fetch(f"https://polona2.pl/api/entities/{h['id']}",
                                       refresh=refresh).decode("utf-8")) 
            except Exception:  # noqa: BLE001
                continue
            scans = ent.get("scans") or []
            if not scans:
                continue
            pages = []
            for s in scans[:max_pages]:
                alto = next((r["url"] for r in (s.get("resources") or [])
                             if "alto" in r.get("mime", "")), None)
                if not alto:
                    continue
                try:
                    xml = fetch(alto, refresh=refresh)
                    root = ET.fromstring(xml)
                    strings = [el.attrib.get("CONTENT", "") for el in root.iter()
                               if el.tag.endswith("String")]
                    if strings:
                        pages.append(" ".join(strings))
                except Exception:  # noqa: BLE001
                    continue
            text = clean_text("\n\n".join(pages))
            if word_count(text) < MIN_WORDS:
                continue
            docs.append(Document(
                id="polona-" + h["id"], domain="", url=f"https://polona.pl/preview/{h.get('slug', h['id'])}",
                date=date, text=text, source="Polona (BN) – OCR ALTO, domena publiczna"))
    return docs


# ---------------------------------------------------------------------------
# Istniejące dziedziny (zgodność z README)
# ---------------------------------------------------------------------------

def collect_existing(domain: str, refresh: bool = False, target_bytes: int = EXISTING_TARGET_BYTES,
                     pool_rows: int = 6000) -> list[Document]:
    import polars as pl
    docs: list[Document] = []
    if domain == "web":
        df = pl.scan_parquet(HPLT).select("text").head(pool_rows).collect()
        texts = df.get_column("text").to_list()
        src_url = HPLT
    elif domain == "angielski":
        df = pl.scan_parquet(WIKITEXT).select("text").collect()
        texts = df.get_column("text").to_list()
        src_url = WIKITEXT
    else:
        src_url = DYNAWORD_FILES[domain]
        df = pl.scan_parquet(src_url).select("text").head(pool_rows).collect()
        texts = df.get_column("text").to_list()

    texts = [(t or "").replace("\r\n", "\n").strip() for t in texts]
    if domain == "angielski":
        # wikitext to akapity — sklejamy w dokumenty ~10 tys. znaków
        lines = [t for t in texts if len(t) >= 200 and not t.startswith("=")]
        grouped, buf, size = [], [], 0
        for t in lines:
            buf.append(t)
            size += len(t) + 1
            if size >= 10_000:
                grouped.append("\n".join(buf))
                buf, size = [], 0
        if buf:
            grouped.append("\n".join(buf))
        texts = grouped
    else:
        texts = [t for t in texts if len(t) >= 200]
    random.Random(7).shuffle(texts)
    total = 0
    for i, t in enumerate(texts):
        if total >= target_bytes:
            break
        t = clean_text(t[:20_000])
        if word_count(t) < MIN_WORDS:
            continue
        docs.append(Document(id=f"{domain}-{i:05d}", domain="", url=src_url, date="",
                             text=t, source=("held-out HPLT (inny shard niż trening)" if domain == "web"
                                             else "SlayerLab/polish-dynaword")))
        total += len(t.encode("utf-8"))
    return docs


# ---------------------------------------------------------------------------
# Zapis, podział, manifest
# ---------------------------------------------------------------------------

def domain_target(domain: str) -> tuple[int, int]:
    return OFFICIAL_DOMAIN_TARGET.get(domain, (9999, EXISTING_TARGET_BYTES))


def store_domain(domain: str, docs: list[Document], limit: int, min_words_target: int) -> dict:
    # deduplikacja po SHA-256 tekstu
    uniq, seen = [], set()
    for d in docs:
        d.domain = domain
        d.text = d.text[:DOC_CAP]  # jak w README: jeden dokument nie dominuje próbki
        h = sha256_text(d.text)
        if h in seen:
            continue
        seen.add(h)
        uniq.append(d)
    uniq.sort(key=lambda d: d.id)
    random.Random(SEED).shuffle(uniq)
    uniq = uniq[:limit]
    ndev = int(round(len(uniq) * DEV_SHARE))
    rejected = 0
    for i, d in enumerate(uniq):
        d.split = "dev" if i < ndev else "test"
        if word_count(d.text) < MIN_WORDS:
            rejected += 1
            continue
        save_document(d)
    kept = [d for d in uniq if word_count(d.text) >= MIN_WORDS]
    return {"requested": limit, "kept": len(kept), "rejected_short": rejected,
            "words": sum(word_count(d.text) for d in kept),
            "target_words": min_words_target}


def build_manifest() -> dict:
    domains = {}
    documents = []
    for name in sorted(os.listdir(RAW_DIR)):
        dpath = os.path.join(RAW_DIR, name)
        if not os.path.isdir(dpath):
            continue
        docs = load_domain(name)
        if not docs:
            continue
        stats = {"docs": len(docs), "words": sum(d["words"] for d in docs),
                 "nfd_docs": sum(1 for d in docs if d.get("nfd")),
                 "dev_docs": sum(1 for d in docs if d["split"] == "dev"),
                 "test_docs": sum(1 for d in docs if d["split"] == "test"),
                 "dev_words": sum(d["words"] for d in docs if d["split"] == "dev"),
                 "test_words": sum(d["words"] for d in docs if d["split"] == "test")}
        stats["share_2026"] = round(sum(1 for d in docs if (d.get("date") or "").startswith("2026"))
                                    / len(docs), 4)
        domains[name] = stats
        for d in docs:
            documents.append({"id": d["id"], "domain": name, "url": d["url"], "date": d["date"],
                              "source": d["source"], "split": d["split"], "words": d["words"],
                              "sha256": d["sha256"], "nfd": bool(d["nfd"])})
    return {"protocol": {"seed": SEED, "dev_share": DEV_SHARE, "min_words": MIN_WORDS,
                         "bootstrap_n": 1000, "created": time.strftime("%Y-%m-%d"),
                         "note": "ten sam seed w całym audycie"},
            "domains": domains, "documents": documents}


def write_bench_files() -> None:
    os.makedirs(BENCH_DIR, exist_ok=True)
    for name in sorted(os.listdir(RAW_DIR)):
        docs = load_domain(name)
        if not docs:
            continue
        with open(os.path.join(BENCH_DIR, name + ".txt"), "w", encoding="utf-8", newline="\n") as f:
            f.write("\n\n".join(d["text"] for d in docs))
        for split in ("dev", "test"):
            with open(os.path.join(BENCH_DIR, f"{name}.{split}.txt"), "w", encoding="utf-8",
                      newline="\n") as f:
                f.write("\n\n".join(d["text"] for d in docs if d["split"] == split))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--manifest", action="store_true")
    ap.add_argument("--bench", action="store_true")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    ensure_dirs()

    plan = []
    for name in ["przetargi_ogloszenia", "przetargi_kio", "samorzad_uchwaly",
                 "granty_ogloszenia", "prawo_eli", "ocr_prasa", "tabele_json"] + EXISTING_DOMAINS:
        if a.only is None or name in a.only:
            plan.append(name)

    for name in plan:
        if os.path.isdir(os.path.join(RAW_DIR, name)) and not a.refresh:
            existing = load_domain(name)
            if existing:
                print(f"{name}: już jest {len(existing)} dok. — pomijam")
                continue
        print(f"== {name}")
        t0 = time.time()
        limit, min_words = domain_target(name)
        if a.limit:
            limit = a.limit
        if name == "przetargi_ogloszenia":
            docs = collect_bzp(a.refresh, "ContractNotice", limit)
        elif name == "przetargi_kio":
            docs = collect_kio(a.refresh, limit)
        elif name == "samorzad_uchwaly":
            docs = collect_uchwaly(a.refresh, limit)
        elif name == "granty_ogloszenia":
            docs = collect_granty(a.refresh, limit)
        elif name == "prawo_eli":
            docs = collect_eli(a.refresh, limit)
        elif name == "ocr_prasa":
            docs = collect_polona(a.refresh, limit)
        elif name == "tabele_json":
            docs = collect_bzp(a.refresh, "TenderResultNotice", limit, as_json=True, prefix="bzp-json")
        else:
            docs = collect_existing(name, a.refresh)
        stats = store_domain(name, docs, limit, min_words)
        print(f"   {stats['kept']} dok., {stats['words']:,} słów, odrzucono krótkich "
              f"{stats['rejected_short']}, {time.time()-t0:.0f}s")

    if a.manifest or a.only is None:
        m = build_manifest()
        write_json(MANIFEST_PATH, m)
        print("\nMANIFEST:")
        for d, s in sorted(m["domains"].items()):
            print(f"  {d:<22} {s['docs']:>4} dok. {s['words']:>9,} słów "
                  f"(dev {s['dev_docs']}, test {s['test_docs']}, NFD {s['nfd_docs']}, "
                  f"2026 {s['share_2026']:.0%})")
    if a.bench:
        write_bench_files()
        print("zapisano pliki bench")


if __name__ == "__main__":
    main()
