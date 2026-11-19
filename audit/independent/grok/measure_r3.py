"""Pomiary red teamu R3 (Grok). Nie zmienia tokenizerów ani skryptów rundy 1.

Wyniki: audit/review_grok/r3_*.json
Pełne teksty odbudowane z cache zostają w pamięci; na dysk idą tylko liczby.
"""
from __future__ import annotations

import io
import json
import os
import random
import sys
from collections import Counter

import numpy as np

from tokenizers import Tokenizer as HFTokenizer  # noqa: F401  H9: przed repo na sys.path

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIT = os.path.dirname(HERE)
REPO = os.path.dirname(AUDIT)
sys.path.append(AUDIT)

from common import (  # noqa: E402
    CACHE_DIR, RAW_DIR, load_domain, percentile, read_json, write_json,
)
from prepare_corpus import extract_div, html_to_text  # noqa: E402
from common import build_encoders, clean_text  # noqa: E402

OFFICIAL = [
    "przetargi_ogloszenia", "przetargi_kio", "samorzad_uchwaly",
    "granty_ogloszenia", "prawo_eli", "ocr_prasa", "tabele_json",
]
CORE = ["TOKENIZATOREX", "TOKENIZATOREX-HF", "Slayer1B", "Pollock-2.0", "APT3-1B"]
ALPHA = 2.5
LABELS_ALL = None  # wszystkie z tokenizer_specs()


def cache_index() -> dict[str, str]:
    idx = {}
    for name in os.listdir(CACHE_DIR):
        if not name.endswith(".json"):
            continue
        meta = json.load(open(os.path.join(CACHE_DIR, name), encoding="utf-8"))
        url = meta.get("url")
        if url:
            idx[url] = os.path.join(CACHE_DIR, name[:-5] + ".bin")
    return idx


def read_bin(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def pdf_text(raw: bytes) -> str:
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(raw))
    return "\n".join((p.extract_text() or "") for p in reader.pages)


def bzp_maps(idx: dict[str, str]) -> dict[str, dict]:
    """noticeNumber -> rekord API (z pełnym htmlBody)."""
    out = {}
    for url, path in idx.items():
        if "ezamowienia.gov.pl/mo-board/api/v1/notice" not in url:
            continue
        try:
            items = json.loads(read_bin(path).decode("utf-8"))
        except Exception:  # noqa: BLE001
            continue
        if not isinstance(items, list):
            continue
        for it in items:
            num = it.get("noticeNumber")
            if num:
                out[num] = it
    return out


def bzp_plain(it: dict) -> str:
    return html_to_text(it.get("htmlBody") or "")


def bzp_json_text(it: dict) -> str:
    text = html_to_text(it.get("htmlBody") or "")
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
    return json.dumps(rec, ensure_ascii=False, indent=2)


def kio_text(idx, did: str) -> str | None:
    url = f"https://orzeczenia.uzp.gov.pl/Home/ContentHtml/{did}?Kind=KIO&flection=0"
    path = idx.get(url)
    if not path:
        return None
    text = html_to_text(read_bin(path).decode("utf-8", errors="replace"))
    i = text.upper().rfind("UZASADNIENIE")
    if i >= 0:
        text = text[i:]
    j = text.find("Sygn. akt")
    if j > 0:
        text = text[j:]
    return text


def eli_titles(idx) -> dict[str, str]:
    url = "https://api.sejm.gov.pl/eli/acts/DU/2026"
    path = idx.get(url)
    if not path:
        return {}
    data = json.loads(read_bin(path).decode("utf-8"))
    return {it["ELI"]: (it.get("title") or "") for it in data.get("items") or []}


def eli_full(idx, eli: str, titles: dict[str, str]) -> str | None:
    url = f"https://api.sejm.gov.pl/eli/acts/{eli}/text.pdf"
    path = idx.get(url)
    if not path:
        return None
    try:
        text = pdf_text(read_bin(path))
    except Exception:  # noqa: BLE001
        return None
    title = titles.get(eli, "")
    return (title + "\n" + text) if title else text


def grant_full(idx, url: str) -> str | None:
    path = idx.get(url)
    if not path:
        return None
    raw = read_bin(path)
    if url.lower().endswith(".pdf") or raw[:5] == b"%PDF-":
        try:
            return pdf_text(raw)
        except Exception:  # noqa: BLE001
            return None
    html = raw.decode("utf-8", errors="replace")
    return extract_div(html, "entry-content") or html_to_text(html)


def polona_full(idx, eid: str) -> str | None:
    path = idx.get(f"https://polona2.pl/api/entities/{eid}")
    if not path:
        return None
    try:
        ent = json.loads(read_bin(path).decode("utf-8"))
    except Exception:  # noqa: BLE001
        return None
    pages = []
    for scan in (ent.get("scans") or [])[:6]:
        alto = next((r.get("url") for r in (scan.get("resources") or [])
                     if "alto" in (r.get("mime") or "")), None)
        if not alto or alto not in idx:
            continue
        try:
            root = __import__("xml.etree.ElementTree", fromlist=["ET"]).ElementTree(
                __import__("xml.etree.ElementTree", fromlist=["ET"]).fromstring(read_bin(idx[alto]))
            ).getroot()
        except Exception:  # noqa: BLE001
            continue
        strings = [el.attrib.get("CONTENT", "") for el in root.iter() if el.tag.endswith("String")]
        if strings:
            pages.append(" ".join(strings))
    if not pages:
        return None
    return "\n\n".join(pages)


def uchwala_html(idx, url: str) -> str | None:
    path = idx.get(url)
    if not path:
        return None
    return html_to_text(read_bin(path).decode("utf-8", errors="replace"))


def rebuild_domain(domain: str, docs: list[dict], idx, bzp, titles) -> tuple[list[dict], dict]:
    """Zwraca dokumenty z pełnym tekstem (ta sama ekstrakcja co runda 1, bez [:20000])."""
    full_docs = []
    stats = {"docs": len(docs), "rebuilt": 0, "prefix_ok": 0, "missing": 0,
             "stored_chars": 0, "full_chars": 0, "stored_at_cap": 0}
    for d in docs:
        text = None
        did = d["id"]
        if domain == "przetargi_ogloszenia":
            it = bzp.get(did[len("bzp-"):])
            text = bzp_plain(it) if it else None
        elif domain == "tabele_json":
            it = bzp.get(did[len("bzp-json-"):])
            text = bzp_json_text(it) if it else None
        elif domain == "przetargi_kio" and did.startswith("kio-"):
            text = kio_text(idx, did[len("kio-"):])
        elif domain == "prawo_eli" and did.startswith("eli-"):
            parts = did[len("eli-"):].split("-")
            if len(parts) >= 3:
                text = eli_full(idx, "/".join(parts[:3]), titles)
        elif domain == "granty_ogloszenia":
            text = grant_full(idx, d.get("url") or "")
        elif domain == "ocr_prasa" and did.startswith("polona-"):
            text = polona_full(idx, did[len("polona-"):])
        elif domain == "samorzad_uchwaly":
            text = uchwala_html(idx, d.get("url") or "")
        if text is None:
            stats["missing"] += 1
            continue
        text = clean_text(text)
        stored = d["text"]
        stats["rebuilt"] += 1
        stats["stored_chars"] += len(stored)
        stats["full_chars"] += len(text)
        if len(stored) >= 20000:
            stats["stored_at_cap"] += 1
        if text.startswith(stored) or stored == text[:20000] or stored == text:
            stats["prefix_ok"] += 1
        full_docs.append({**{k: d[k] for k in d if k != "text"}, "text": text,
                          "stored_chars": len(stored), "full_chars": len(text)})
    return full_docs, stats


def summarize(enc, docs: list[dict]) -> dict:
    toks = words = byts = chars = 0
    ferts = []
    bpts = []
    for d in docs:
        t = d["text"]
        n = len(enc.ids(t))
        w = max(1, len(t.split()))
        b = len(t.encode("utf-8"))
        toks += n
        words += len(t.split())
        byts += b
        chars += len(t)
        ferts.append(n / w)
        bpts.append(b / n if n else 0.0)
    return {
        "docs": len(docs),
        "tokens": int(toks),
        "words": int(words),
        "chars": int(chars),
        "bytes": int(byts),
        "fertility": (toks / words) if words else None,
        "bytes_per_token": (byts / toks) if toks else None,
        "chars_per_token": (chars / toks) if toks else None,
        "macro_fertility": float(np.mean(ferts)) if ferts else None,
        "macro_bytes_per_token": float(np.mean(bpts)) if bpts else None,
    }


def rank_map(rows: dict[str, dict], key: str, higher_better: bool = False) -> list[str]:
    items = [(k, v[key]) for k, v in rows.items() if v.get(key) is not None]
    items.sort(key=lambda x: x[1], reverse=higher_better)
    return [k for k, _ in items]


def measure_set(encoders, docs_by_dom: dict[str, list[dict]], labels: list[str]) -> dict:
    out = {"domains": {}, "aggregate": {}}
    agg_docs = [d for dom in docs_by_dom for d in docs_by_dom[dom]]
    for dom, docs in docs_by_dom.items():
        rows = {}
        for lab in labels:
            rows[lab] = summarize(encoders[lab], docs)
        out["domains"][dom] = {
            "rows": rows,
            "rank_fertility": rank_map(rows, "fertility"),
            "rank_bytes_per_token": rank_map(rows, "bytes_per_token", higher_better=True),
            "winner_fertility": rank_map(rows, "fertility")[0] if rows else None,
        }
    rows = {lab: summarize(encoders[lab], agg_docs) for lab in labels}
    out["aggregate"] = {
        "rows": rows,
        "rank_fertility": rank_map(rows, "fertility"),
        "rank_bytes_per_token": rank_map(rows, "bytes_per_token", higher_better=True),
        "docs": len(agg_docs),
    }
    return out


def _bucket(ch: str) -> str:
    if ch == " ":
        return "space"
    if ch == "\n":
        return "newline"
    if ch.isspace():
        return "other_space"
    if ch.isdigit():
        return "digit"
    if ord(ch) > 127:
        return "nonascii"
    return "ascii"


def diff_kinds(a: str, b: str) -> dict:
    """Różnica liczników klas znaków. Liniowa; nie szuka wyrównania (to byłoby kwadratowe)."""
    ca, cb = Counter(), Counter()
    for ch in a:
        ca[_bucket(ch)] += 1
    for ch in b:
        cb[_bucket(ch)] += 1
    lost, gained = {}, {}
    for k in set(ca) | set(cb):
        delta = cb[k] - ca[k]
        if delta < 0:
            lost[k] = -delta
        elif delta > 0:
            gained[k] = delta
    return {"chars_lost": sum(lost.values()), "chars_gained": sum(gained.values()),
            "lost": lost, "gained": gained}


def roundtrip(encoders, docs: list[dict], labels: list[str]) -> dict:
    out = {"docs": len(docs), "tokenizers": {}}
    for lab in labels:
        enc = encoders[lab]
        n_ok = 0
        n_len = 0
        kinds = Counter()
        gained = Counter()
        char_delta = 0
        token_src = token_dec = 0
        examples = 0
        for d in docs:
            text = d["text"]
            ids = enc.ids(text)
            try:
                dec = enc.decode(ids)
            except Exception as ex:  # noqa: BLE001
                kinds["decode_error"] += 1
                continue
            token_src += len(ids)
            if dec == text:
                n_ok += 1
                token_dec += len(ids)
                continue
            n_len += 1
            char_delta += len(dec) - len(text)
            info = diff_kinds(text, dec)
            for k, v in info["lost"].items():
                kinds[k] += v
            for k, v in info["gained"].items():
                gained[k] += v
            # tokeny na tekście po decode — czy „mniej tokenów” znika po utracie znaków
            token_dec += len(enc.ids(dec))
            examples += 1
        out["tokenizers"][lab] = {
            "exact_ok": n_ok,
            "exact_rate": n_ok / len(docs) if docs else None,
            "mismatch": n_len,
            "net_char_delta_on_mismatch": char_delta,
            "tokens_on_source": token_src,
            "tokens_on_decoded": token_dec,
            "lost_char_buckets": dict(kinds),
            "gained_char_buckets": dict(gained),
        }
        print(f"  roundtrip {lab}: {n_ok}/{len(docs)} exact")
    return out


def renyi_both(counts: np.ndarray, vocab: int, alpha: float = ALPHA) -> dict:
    c = counts[counts > 0].astype(np.float64)
    total = c.sum()
    p = c / total
    h = (1.0 / (1.0 - alpha)) * np.log(np.sum(p ** alpha))
    return {
        "H_alpha": float(h),
        "log_base": "natural (ln); stosunek H/log|V| nie zależy od podstawy",
        "vocab": int(vocab),
        "used_types": int(len(c)),
        "eff_zouhar_H_over_logV": float(h / np.log(vocab)),
        "audit_expH_over_V": float(np.exp(h) / vocab),
        "identity": "exp(H)/|V| = |V|^(eff-1), więc to nie jest Eff_α",
    }


def renyi_on(encoders, docs: list[dict], labels: list[str]) -> dict:
    out = {}
    for lab in labels:
        enc = encoders[lab]
        counter = Counter()
        n_tokens = 0
        for d in docs:
            ids = enc.ids(d["text"])
            counter.update(ids)
            n_tokens += len(ids)
        counts = np.array(list(counter.values()), dtype=np.float64)
        row = renyi_both(counts, encoders[lab].vocab)
        row["tokens"] = n_tokens
        row["dead"] = encoders[lab].vocab - row["used_types"]
        out[lab] = row
        print(f"  renyi {lab}: audit {row['audit_expH_over_V']:.6f}  zouhar {row['eff_zouhar_H_over_logV']:.4f}")
    order_a = sorted(out, key=lambda k: out[k]["audit_expH_over_V"], reverse=True)
    order_z = sorted(out, key=lambda k: out[k]["eff_zouhar_H_over_logV"], reverse=True)
    return {"alpha": ALPHA, "tokenizers": out,
            "rank_audit_desc": order_a, "rank_zouhar_desc": order_z,
            "rank_changed": order_a != order_z}


def token_strings(enc) -> list[str]:
    """Napis tokenu po decode([id]) — tak, jak widać cyfry w tekście."""
    n = enc.vocab
    # dekoduj paczkami tam, gdzie się da
    strings = [""] * n
    dec = enc.decode
    # pojedynczo: 32k–200k; HF decode jednego id jest tanie, ale 200k wolne.
    # Dla GPT-4o pomijamy rozbicie cyfr (nie jest TKX).
    if n > 60000:
        return strings
    for i in range(n):
        try:
            strings[i] = dec([i])
        except Exception:  # noqa: BLE001
            strings[i] = ""
    return strings


def digit_lengths(enc, docs, strings: list[str]) -> dict:
    cur, upper, lower = [], [], []
    for d in docs:
        ids = enc.ids(d["text"])
        base = len(ids)
        up = 0
        extra = 0
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
    def pack(xs):
        return {
            "median": percentile(xs, 0.5),
            "p90": percentile(xs, 0.9),
            "mean": float(np.mean(xs)) if xs else None,
            "max": max(xs) if xs else None,
            "fit_2048": sum(1 for x in xs if x <= 2048) / len(xs) if xs else None,
            "fit_4096": sum(1 for x in xs if x <= 4096) / len(xs) if xs else None,
            "docs": len(xs),
        }
    return {"current": pack(cur), "digits_upper": pack(upper), "digits_lower": pack(lower)}


def load_extra() -> dict[str, list[dict]]:
    root = os.path.join(HERE, "raw_extra")
    out = {}
    if not os.path.isdir(root):
        return out
    for dom in os.listdir(root):
        d = os.path.join(root, dom)
        if not os.path.isdir(d):
            continue
        docs = []
        for name in sorted(os.listdir(d)):
            if name.endswith(".json"):
                docs.append(json.load(open(os.path.join(d, name), encoding="utf-8")))
        if docs:
            out[dom] = docs
    return out


def apt_loss(enc, docs: list[dict]) -> dict:
    """Ile znaków APT gubi: len(decode(encode(x))) vs len(x), i fertility na tekście po decode."""
    src_chars = dec_chars = src_tok = dec_tok = src_words = 0
    n_ok = 0
    for d in docs:
        t = d["text"]
        ids = enc.ids(t)
        dec = enc.decode(ids)
        src_chars += len(t)
        dec_chars += len(dec)
        src_tok += len(ids)
        dec_tok += len(enc.ids(dec))
        src_words += len(t.split())
        if dec == t:
            n_ok += 1
    return {
        "docs": len(docs),
        "exact_rate": n_ok / len(docs) if docs else None,
        "source_chars": src_chars,
        "decoded_chars": dec_chars,
        "char_retention": (dec_chars / src_chars) if src_chars else None,
        "tokens": src_tok,
        "fertility_on_source_words": (src_tok / src_words) if src_words else None,
        "bytes_per_token_source": None,
    }


def main() -> None:
    print("ładowanie tokenizerów…")
    encoders = build_encoders()
    labels_all = list(encoders)
    print("tokenizery:", labels_all)

    # --- zamrożony test, dziedziny urzędowe ---
    stored = {}
    for dom in OFFICIAL:
        docs = load_domain(dom, "test")
        stored[dom] = docs
        print(f"  test {dom}: {len(docs)}")

    print("== fertility na zamrożonym teście (5 tokenizerów) ==")
    frozen_core = measure_set(encoders, stored, CORE)
    write_json(os.path.join(HERE, "r3_frozen_core.json"), frozen_core)

    print("== ranking HF: wszystkie tokenizery, dziedziny urzędowe, test ==")
    frozen_all = measure_set(encoders, stored, labels_all)
    # bez APT3
    no_apt_labels = [l for l in labels_all if l != "APT3-1B"]
    frozen_no_apt = measure_set(encoders, stored, no_apt_labels)
    fairness = {
        "with_apt3_rank_fertility": frozen_all["aggregate"]["rank_fertility"],
        "with_apt3_rank_bytes": frozen_all["aggregate"]["rank_bytes_per_token"],
        "without_apt3_rank_fertility": frozen_no_apt["aggregate"]["rank_fertility"],
        "without_apt3_rank_bytes": frozen_no_apt["aggregate"]["rank_bytes_per_token"],
        "aggregate_all": frozen_all["aggregate"]["rows"],
        "per_domain_winner_all": {d: frozen_all["domains"][d]["winner_fertility"] for d in OFFICIAL},
        "per_domain_winner_no_apt": {d: frozen_no_apt["domains"][d]["winner_fertility"] for d in OFFICIAL},
        "per_domain_rank_bytes": {d: frozen_all["domains"][d]["rank_bytes_per_token"] for d in OFFICIAL},
        "note": "Na tym samym tekście suma_bajtów jest stała, więc ranking bajtów/token jest odwrotnością rankingu liczby tokenów (i fertility, bo suma słów też jest stała). To tożsamość, nie osobny eksperyment.",
    }
    # strata APT3
    official_test_docs = [d for dom in OFFICIAL for d in stored[dom]]
    fairness["apt3_loss_official_test"] = apt_loss(encoders["APT3-1B"], official_test_docs)
    b = fairness["apt3_loss_official_test"]
    # bytes of SOURCE / tokens  vs bytes of DECODED / tokens
    src_bytes = sum(len(d["text"].encode("utf-8")) for d in official_test_docs)
    b["source_bytes"] = src_bytes
    b["bytes_per_token_on_source"] = src_bytes / b["tokens"] if b["tokens"] else None
    write_json(os.path.join(HERE, "r3_fairness.json"), fairness)
    print("fairness zapisany, zwycięzca agregatu", fairness["with_apt3_rank_fertility"][:4])

    # --- round-trip, wszystkie dokumenty urzędowe (dev+test) + uzupełnienie do opisu ---
    print("== round-trip ==")
    rt_docs = []
    for dom in OFFICIAL:
        rt_docs.extend(load_domain(dom, None))
    # dołóż web/test aż przekroczymy 1000, ale i tak liczymy całe urzędowe
    if len(rt_docs) < 1000:
        rt_docs.extend(load_domain("web", "test"))
    rt = roundtrip(encoders, rt_docs, labels_all)
    rt["composition"] = {
        "official_all_splits": sum(len(load_domain(d, None)) for d in OFFICIAL),
        "measured": len(rt_docs),
    }
    write_json(os.path.join(HERE, "r3_roundtrip.json"), rt)

    # --- Rényi na tym samym zbiorze co vocab_usage (test, 15 dziedzin) ---
    print("== Rényi ==")
    vu_domains = ["przetargi_ogloszenia", "przetargi_kio", "samorzad_uchwaly",
                  "granty_ogloszenia", "prawo_eli", "ocr_prasa", "tabele_json",
                  "web", "wikipedia", "literatura", "prawo", "sejm", "nauka",
                  "dyskusje", "angielski"]
    vu_docs = [d for dom in vu_domains for d in load_domain(dom, "test")]
    renyi = renyi_on(encoders, vu_docs, labels_all)
    renyi["docs"] = len(vu_docs)
    renyi["domains"] = vu_domains
    write_json(os.path.join(HERE, "r3_renyi.json"), renyi)

    # --- kontekst 2048 na zamrożonym teście (TKX HF) + wariant cyfr ---
    print("== kontekst (to może potrwać: tablica napisów tokenów) ==")
    strings = token_strings(encoders["TOKENIZATOREX-HF"])
    ctx = {"tokenizer": "TOKENIZATOREX-HF", "on": "zamrożony test (przycięty do 20 tys. znaków)",
           "digit_estimate": {
               "upper": "każda cyfra = 1 token, reszta znaków tego samego tokenu = 1 token jeśli jest",
               "lower": "do obecnej liczby tokenów dodać max(0, cyfry_w_tokenie-1)",
           },
           "domains": {}}
    for dom, docs in stored.items():
        ctx["domains"][dom] = digit_lengths(encoders["TOKENIZATOREX-HF"], docs, strings)
        c = ctx["domains"][dom]["current"]
        print(f"  {dom}: mediana {c['median']:.0f} p90 {c['p90']:.0f} fit2048 {c['fit_2048']:.1%}")
    write_json(os.path.join(HERE, "r3_context_truncated.json"), ctx)

    # --- odbudowa pełnych tekstów z cache ---
    print("== odbudowa pełnych tekstów ==")
    idx = cache_index()
    print("  cache urls", len(idx))
    bzp = bzp_maps(idx)
    print("  bzp notices", len(bzp))
    titles = eli_titles(idx)
    full_by = {}
    rebuild_stats = {}
    for dom in OFFICIAL:
        docs = load_domain(dom, "test")
        full_docs, st = rebuild_domain(dom, docs, idx, bzp, titles)
        full_by[dom] = full_docs
        rebuild_stats[dom] = st
        print(f"  {dom}: rebuilt {st['rebuilt']}/{st['docs']} prefix_ok {st['prefix_ok']} "
              f"chars {st['stored_chars']} -> {st['full_chars']}")
    write_json(os.path.join(HERE, "r3_rebuild_stats.json"), rebuild_stats)

    # fertility pełnych, tylko dokumenty udanie odbudowane, porównanie z ich wersją przyciętą
    print("== fertility pełny vs przycięty ==")
    paired = {}
    for dom, full_docs in full_by.items():
        if not full_docs:
            continue
        ids = {d["id"] for d in full_docs}
        trunc = [d for d in stored[dom] if d["id"] in ids]
        # ta sama kolejność
        trunc_map = {d["id"]: d for d in trunc}
        full_aligned = [d for d in full_docs if d["id"] in trunc_map]
        trunc_aligned = [trunc_map[d["id"]] for d in full_aligned]
        paired[dom] = {
            "truncated": {lab: summarize(encoders[lab], trunc_aligned) for lab in CORE},
            "full": {lab: summarize(encoders[lab], full_aligned) for lab in CORE},
        }
        paired[dom]["rank_trunc"] = rank_map(paired[dom]["truncated"], "fertility")
        paired[dom]["rank_full"] = rank_map(paired[dom]["full"], "fertility")
        paired[dom]["n"] = len(full_aligned)
    # agregat dziedzin, w których przycięcie realnie coś zmienia (nie samorzad html = już pełne)
    write_json(os.path.join(HERE, "r3_full_vs_trunc.json"), paired)

    # kontekst na pełnych tekstach (TKX HF), tam gdzie odbudowa się udała
    ctx_full = {"tokenizer": "TOKENIZATOREX-HF", "on": "pełny tekst tej samej ekstrakcji, bez [:20000]",
                "domains": {}}
    for dom, docs in full_by.items():
        if not docs:
            continue
        ctx_full["domains"][dom] = digit_lengths(encoders["TOKENIZATOREX-HF"], docs, strings)
    write_json(os.path.join(HERE, "r3_context_full.json"), ctx_full)

    # --- R3-extra ---
    print("== R3-extra ==")
    extra = load_extra()
    if extra:
        # tylko dziedziny, które zebraliśmy; porównanie z core
        extra_m = measure_set(encoders, extra, CORE)
        write_json(os.path.join(HERE, "r3_extra_fertility.json"), extra_m)
        for dom, row in extra_m["domains"].items():
            print(f"  extra {dom}: {row['rank_fertility'][:3]} fert "
                  f"{row['rows'][row['rank_fertility'][0]]['fertility']:.4f}")
    else:
        print("  brak raw_extra")

    print("GOTOWE pomiary")


if __name__ == "__main__":
    main()
