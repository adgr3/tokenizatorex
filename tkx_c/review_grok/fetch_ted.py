"""Pobiera ogłoszenia TED (PL) i strony BIP — źródła spoza korpusu TKX-A."""
from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw_extra")
os.makedirs(RAW, exist_ok=True)
UA = {"User-Agent": "tokenizatorex-review-r3/1.0 (public research)"}


def get(url, data=None, timeout=40, headers=None):
    h = dict(UA)
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def words(text):
    return len(text.split())


def save(rec):
    path = os.path.join(RAW, rec["id"] + ".json")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(rec, f, ensure_ascii=False)
        f.write("\n")


def xml_to_text(xml: str) -> str:
    xml = re.sub(r"(?is)<script.*?>.*?</script>", " ", xml)
    xml = re.sub(r"<[^>]+>", " ", xml)
    xml = xml.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    xml = re.sub(r"[ \t]+", " ", xml)
    xml = re.sub(r"\n{2,}", "\n", xml)
    return xml.strip()


def main():
    page = int(os.environ.get("TED_PAGE", "1"))
    docs = []
    body = json.dumps({
        "query": "buyer-country=POL AND publication-date>=20250101<=20251101",
        "fields": ["publication-number", "publication-date", "notice-title", "buyer-name", "links"],
        "limit": 20,
        "page": page,
        "scope": "ALL",
        "paginationMode": "PAGE_NUMBER",
    }).encode()
    raw = get("https://api.ted.europa.eu/v3/notices/search", data=body,
              headers={"Content-Type": "application/json", "Accept": "application/json"})
    payload = json.loads(raw.decode("utf-8"))
    notices = payload.get("notices") or []
    print("notices", len(notices), "keys", list(payload)[:8], flush=True)
    if notices:
        print("sample links", json.dumps(notices[0].get("links"), ensure_ascii=False)[:500], flush=True)
    for n in notices:
        num = n.get("publication-number")
        links = n.get("links") or {}
        url = None
        # różne kształty odpowiedzi
        if isinstance(links, dict):
            for key in ("xml", "html", "pdf"):
                node = links.get(key)
                if isinstance(node, dict):
                    url = node.get("POL") or node.get("pol") or node.get("ENG") or next(iter(node.values()), None)
                    if isinstance(url, dict):
                        url = url.get("url") or url.get("href")
                elif isinstance(node, str):
                    url = node
                if url:
                    break
        if not url and num:
            url = f"https://ted.europa.eu/en/notice/{num}/xml"
        if not url:
            continue
        try:
            data = get(url, timeout=40)
        except Exception as e:
            print("fail", num, type(e).__name__, flush=True)
            continue
        text = data.decode("utf-8", "replace")
        if text.lstrip().startswith("%PDF") or data[:4] == b"%PDF":
            print("pdf skip", num, flush=True)
            continue
        text = xml_to_text(text)
        if words(text) < 150:
            print("short", num, words(text), url[:80], flush=True)
            continue
        if len(text) > 60000:
            text = text[:60000]
        rec = {
            "id": "R3-extra-ted-" + re.sub(r"[^0-9A-Za-z]+", "-", str(num)),
            "source_tag": "R3-extra",
            "source": "ted",
            "url": url,
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "words": words(text),
            "text": text,
        }
        save(rec)
        docs.append({k: rec[k] for k in ("id", "source_tag", "source", "url", "sha256", "words")})
        print("ok", rec["id"], rec["words"], flush=True)
        if len(docs) >= 25:
            break

    # BIP Kraków — strona główna ma linki; bierzemy kilka podstron z treścią.
    try:
        home = get("https://www.bip.krakow.pl/").decode("utf-8", "replace")
        hrefs = re.findall(r'href="(https://www\.bip\.krakow\.pl/[^"]+|[^"]+)"', home)
        absu = []
        for h in hrefs:
            if h.startswith("/"):
                h = "https://www.bip.krakow.pl" + h
            if "bip.krakow.pl" in h and h not in absu:
                absu.append(h)
        print("bip links", len(absu), flush=True)
        taken = 0
        for h in absu:
            if any(x in h.lower() for x in ("uchwal", "zarzadzen", "obwieszcz", "przetarg")):
                try:
                    page = get(h, timeout=30).decode("utf-8", "replace")
                except Exception:
                    continue
                text = xml_to_text(page)
                if words(text) < 200:
                    continue
                if len(text) > 50000:
                    text = text[:50000]
                rec = {
                    "id": "R3-extra-bipkrk-" + hashlib.sha256(h.encode()).hexdigest()[:10],
                    "source_tag": "R3-extra",
                    "source": "bip_krakow",
                    "url": h,
                    "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                    "words": words(text),
                    "text": text,
                }
                save(rec)
                docs.append({k: rec[k] for k in ("id", "source_tag", "source", "url", "sha256", "words")})
                print("ok", rec["id"], rec["words"], flush=True)
                taken += 1
                if taken >= 12:
                    break
    except Exception as e:
        print("bip fail", type(e).__name__, e, flush=True)

    manifest_path = os.path.join(HERE, "r3_extra_manifest.json")
    prev = []
    if os.path.exists(manifest_path):
        prev = json.load(open(manifest_path, encoding="utf-8")).get("docs") or []
    # nie dubluj id
    have = {d["id"] for d in prev}
    for d in docs:
        if d["id"] not in have:
            prev.append(d)
    out = {"label": "R3-extra", "n": len(prev), "docs": prev}
    with open(manifest_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("manifest", out["n"], flush=True)


if __name__ == "__main__":
    main()
