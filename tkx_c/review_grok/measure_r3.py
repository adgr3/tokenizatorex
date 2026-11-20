"""Ataki 1–4 i pomiary pomocnicze TKX-C runda 3.

Tokenizer = eksport HF (hf/variants/*/tokenizer.json).
Tekst testu: audit/data/raw, split test. Wyniki: tkx_c/review_grok/*.json.
"""
from __future__ import annotations

import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict

from tokenizers import Tokenizer  # HF przed dopisaniem repo (katalog tokenizers/)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(ROOT, "audit"))
sys.path.append(ROOT)

import numpy as np  # noqa: E402

from common import bootstrap_indices, load_domain  # noqa: E402

OUT = os.path.dirname(os.path.abspath(__file__))
HF = os.path.join(ROOT, "hf", "variants")

DOMAINS = ["przetargi_ogloszenia", "przetargi_kio", "samorzad_uchwaly",
           "granty_ogloszenia", "prawo_eli", "ocr_prasa", "tabele_json",
           "web", "wikipedia", "literatura", "prawo", "sejm", "nauka",
           "dyskusje", "angielski"]
OFFICIAL = DOMAINS[:7]
FOCUS = ["V0-32k", "V2-32k", "V2b-32k", "V3-32k"]
SIZES = ["V2-32k", "V2-24k", "V2-16k", "V3-32k", "V3-24k", "V3-16k"]

CPV_RE = re.compile(r"\b\d{8}-\d\b")
DATE_RE = re.compile(r"\b(\d{1,2})([./-])(\d{1,2})([./-])(\d{4})\b")
CASE_RE = re.compile(r"\b[A-Z]{1,4}[./-]\d{1,4}(?:[./-]\d{1,4}){1,3}\b")
POSTAL_RE = re.compile(r"\b(\d{2})-(\d{3})\b")
YEAR_RE = re.compile(r"(?<!\d)((?:19|20)\d{2})(?!\d)")
RUN_RE = re.compile(r"\d+")
KWOTA_RE = re.compile(r"(?<![\d,])\d{1,3}(?:[ \u00a0]\d{3})+(?:,\d{1,2})?\s*(?:zł|PLN)\b")
NR_RE = re.compile(r"(?i)nr$")
POZ_RE = re.compile(r"(?i)poz\.$")


def write(name: str, obj) -> None:
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("wrote", name, flush=True)


def load(name: str) -> Tokenizer:
    return Tokenizer.from_file(os.path.join(HF, name, "tokenizer.json"))


def right_lengths(n: int) -> list[int]:
    """Długości grup od prawej: 8 -> [2,3,3], 4 -> [1,3], 3 -> [3]."""
    if n <= 0:
        return []
    rem = n % 3
    if rem == 0:
        return [3] * (n // 3)
    return [rem] + [3] * (n // 3)


def spans_of(enc) -> list[tuple[int, int]]:
    return [(a, b) for a, b in enc.offsets if b > a]


def overlapping(spans, start: int, end: int) -> list[tuple[int, int]]:
    return [(a, b) for a, b in spans if a < end and b > start]


def piece_lengths(spans, start: int, end: int) -> list[int] | None:
    """Długości pokrycia [start, end) kolejnymi tokenami. None przy luce lub nakładce."""
    hit = overlapping(spans, start, end)
    if not hit:
        return None
    hit = sorted(hit)
    lengths = []
    cursor = start
    for a, b in hit:
        lo, hi = max(a, start), min(b, end)
        if lo > cursor:
            return None
        if lo < cursor:
            return None
        if hi > lo:
            lengths.append(hi - lo)
            cursor = hi
    if cursor != end:
        return None
    return lengths


def crossed(spans, pos: int) -> bool:
    return any(a < pos < b for a, b in spans)


def shape_label(lengths: list[int] | None) -> str:
    if lengths is None:
        return "GAP"
    return "+".join(str(x) for x in lengths)


def surface(tok: Tokenizer, idx: int) -> str:
    return tok.decode([idx])


def forced_kind(s: str) -> str | None:
    if re.fullmatch(r"\d{2}", s):
        return "bare2"
    if re.fullmatch(r"\d{3}", s):
        return "bare3"
    if re.fullmatch(r" \d", s):
        return "sp1"
    if re.fullmatch(r" \d{2}", s):
        return "sp2"
    if re.fullmatch(r" \d{3}", s):
        return "sp3"
    return None


def numberish(s: str) -> bool:
    return re.fullmatch(r"[ \u00a0]?\d+", s or "") is not None


def left_class(text: str, start: int) -> str:
    if start <= 0:
        return "start"
    ch = text[start - 1]
    if ch == " ":
        return "space"
    if ch == "\n":
        return "newline"
    if ch == "\t":
        return "tab"
    if ch == "\u00a0":
        return "nbsp"
    if ch in "([{":
        return "paren"
    if ch in "/\\":
        return "slash"
    if ch == ".":
        return "dot"
    if ch in "-–—":
        return "hyphen"
    if ch in "\"'„“«»‚‘":
        return "quote"
    if ch.isalpha():
        window = text[max(0, start - 8):start]
        if NR_RE.search(window):
            return "nr_no_space"
        if POZ_RE.search(window):
            return "poz_no_space"
        return "letter"
    return "other"


def ci_delta_pct(a: np.ndarray, b: np.ndarray, w: np.ndarray) -> dict:
    idx = bootstrap_indices(len(w))
    diff = (b[idx] - a[idx]).sum(1) / w[idx].sum(1)
    point = float((b.sum() - a.sum()) / a.sum()) if a.sum() else None
    fert_a = float(a.sum() / w.sum())
    lo, hi = np.percentile(diff, [2.5, 97.5])
    return {
        "docs": int(len(w)),
        "words": int(w.sum()),
        "tokens_a": int(a.sum()),
        "tokens_b": int(b.sum()),
        "delta_pct": point,
        "delta_pct_ci95": [float(lo / fert_a), float(hi / fert_a)] if fert_a else None,
        "fertility_a": fert_a,
        "fertility_b": float(b.sum() / w.sum()),
    }


def bump(box: dict, key: str, n: int = 1) -> None:
    box[key] = box.get(key, 0) + n


def check_offsets(tok: Tokenizer) -> None:
    text = "zażółć 2024 koniec"
    enc = tok.encode(text, add_special_tokens=False)
    start = text.find("2024")
    lens = piece_lengths(spans_of(enc), start, start + 4)
    if lens is None or sum(lens) != 4:
        raise SystemExit(f"offsety nie schodzą się ze znakami: {lens} {enc.offsets}")
    # grupa 452 wewnątrz kodu jest rozcięta, a sama „452” jest jednym tokenem
    alone = [tok.decode([i]) for i in tok.encode("452", add_special_tokens=False).ids]
    inside = [tok.decode([i]) for i in tok.encode("45233140", add_special_tokens=False).ids]
    if alone != ["452"] or inside[:1] == ["452"]:
        raise SystemExit(f"nieoczekiwany wzorzec CPV: alone={alone} inside={inside}")


def synthetic(toks: dict[str, Tokenizer]) -> dict:
    v3 = toks["V3-32k"]
    # Każdy zapis 000–999: czy HF składa go w jeden token?
    atomic3 = {"n": 1000, "one_token": 0, "shapes": Counter()}
    failures = []
    for n in range(1000):
        s = f"{n:03d}"
        ids = v3.encode(s, add_special_tokens=False).ids
        parts = [v3.decode([i]) for i in ids]
        atomic3["shapes"][shape_label([len(p) for p in parts])] += 1
        if parts == [s]:
            atomic3["one_token"] += 1
        elif len(failures) < 30:
            failures.append({"n": s, "pieces": parts})
    atomic3["shapes"] = dict(atomic3["shapes"])
    atomic3["not_one_token"] = 1000 - atomic3["one_token"]
    atomic3["failures_head"] = failures

    atomic2 = {"n": 100, "one_token": 0}
    for n in range(100):
        s = f"{n:02d}"
        parts = [v3.decode([i]) for i in v3.encode(s, add_special_tokens=False).ids]
        if parts == [s]:
            atomic2["one_token"] += 1
    atomic2["not_one_token"] = 100 - atomic2["one_token"]

    # Lata 1900–2099 w szablonie wykonawcy i gołe.
    years = {}
    for y in range(1900, 2100):
        row = {}
        for label, text in (
            ("template", f"w roku {y} r. zadanie"),
            ("bare", str(y)),
            ("iso", f"{y}-11-20"),
            ("dotted", f"20.11.{y}"),
            ("nospace", f"{y}r."),
        ):
            enc = v3.encode(text, add_special_tokens=False)
            if label == "template":
                # rok stoi po „w roku ”
                at = text.find(str(y))
                lens = piece_lengths(spans_of(enc), at, at + 4)
                row["template_tokens"] = len(enc.ids)
                row["template_year_shape"] = shape_label(lens)
                row["template_year_pieces"] = [
                    v3.decode([enc.ids[i]])
                    for i, (a, b) in enumerate(enc.offsets)
                    if b > a and a < at + 4 and b > at
                ]
            else:
                at = text.find(str(y))
                lens = piece_lengths(spans_of(enc), at, at + 4)
                row[label + "_shape"] = shape_label(lens)
                row[label + "_tokens_all"] = len(enc.ids)
        # V2/V2b: liczba tokenów szablonu i kształt roku (oczekiwane 1+1+1+1)
        for name in ("V2-32k", "V2b-32k", "V0-32k"):
            text = f"w roku {y} r. zadanie"
            enc = toks[name].encode(text, add_special_tokens=False)
            at = text.find(str(y))
            lens = piece_lengths(spans_of(enc), at, at + 4)
            row[name] = {"template_tokens": len(enc.ids), "year_shape": shape_label(lens)}
        years[str(y)] = row

    def band(lo, hi):
        shapes = Counter(years[str(y)]["template_year_shape"] for y in range(lo, hi + 1))
        counts = Counter(years[str(y)]["template_tokens"] for y in range(lo, hi + 1))
        v2_shapes = Counter(years[str(y)]["V2-32k"]["year_shape"] for y in range(lo, hi + 1))
        return {"n": hi - lo + 1, "v3_shapes": dict(shapes), "v3_template_token_counts": dict(counts),
                "v2_shapes": dict(v2_shapes)}

    # Ta sama kwota ze spacjami tysięcy i bez. Spacje są wstawiane od prawej.
    def spaced(digits: str) -> str:
        rev = digits[::-1]
        groups = [rev[i:i + 3][::-1] for i in range(0, len(rev), 3)]
        return " ".join(reversed(groups))

    amount_rows = []
    for digits in [
        "1234", "12345", "123456", "1234567", "12345678", "123456789",
        "2024", "1999", "950", "950950", "1000", "1000000", "45233140",
        "9876543210", "11111111", "2000", "2026",
    ]:
        comp = digits
        spa = spaced(digits)
        for name in ("V2-32k", "V2b-32k", "V3-32k"):
            tok = toks[name]
            ec = tok.encode(comp, add_special_tokens=False)
            es = tok.encode(spa, add_special_tokens=False)
            lc = piece_lengths(spans_of(ec), 0, len(comp))
            # w wersji ze spacjami bierzemy tylko pokrycie cyfr, po kolei
            digit_pos = [i for i, ch in enumerate(spa) if ch.isdigit()]
            # sklejone grupy cyfr oddzielone spacją — kształt każdej grupy i całości
            groups = []
            i = 0
            spans = spans_of(es)
            while i < len(spa):
                if spa[i] == " ":
                    i += 1
                    continue
                j = i
                while j < len(spa) and spa[j].isdigit():
                    j += 1
                groups.append(shape_label(piece_lengths(spans, i, j)))
                i = j
            amount_rows.append({
                "digits": digits, "spaced": spa, "variant": name,
                "compact_shape": shape_label(lc),
                "spaced_group_shapes": groups,
                "compact_pieces": [tok.decode([i]) for i in ec.ids],
                "spaced_pieces": [tok.decode([i]) for i in es.ids],
                "same_digit_groups": shape_label(lc) == "+".join(
                    str(len(g)) for g in spa.split(" ")) if False else (
                    [len(p) for p in [tok.decode([i]) for i in ec.ids] if p.strip().isdigit()]
                    != [len(g) for g in spa.split(" ")]
                ),
            })

    # Czytelniejsza flaga: czy grupy cyfr kompaktu (same cyfry, bez spacji) 
    # są tymi samymi ciągami co grupy w zapisie ze spacjami.
    cleaned = []
    for row in amount_rows:
        compact_groups = [p.strip() for p in row["compact_pieces"] if any(ch.isdigit() for ch in p)]
        spaced_groups = [p.strip() for p in row["spaced_pieces"] if any(ch.isdigit() for ch in p)]
        cleaned.append({
            "digits": row["digits"],
            "spaced": row["spaced"],
            "variant": row["variant"],
            "compact_digit_pieces": compact_groups,
            "spaced_digit_pieces": spaced_groups,
            "same_digit_pieces": compact_groups == spaced_groups,
        })

    return {
        "atomic3": atomic3,
        "atomic2": atomic2,
        "year_bands": {
            "1990_1999": band(1990, 1999),
            "2000_2014": band(2000, 2014),
            "2015_2035": band(2015, 2035),
            "2036_2040": band(2036, 2040),
            "1900_2099": band(1900, 2099),
        },
        "year_examples": {y: years[y] for y in
                          ["1990", "1999", "2000", "2015", "2019", "2020", "2024",
                           "2025", "2026", "2027", "2030", "2035"]
                          if y in years},
        "amounts": cleaned,
    }


def main() -> None:
    print("load", flush=True)
    names = list(dict.fromkeys(FOCUS + SIZES))
    toks = {n: load(n) for n in names}
    check_offsets(toks["V3-32k"])
    print("offsets ok", flush=True)
    syn = synthetic(toks)
    # przykłady lat trzymamy osobno, pełna siatka jest duża — zostawiamy pasma i przykłady
    write("attack2_synthetic.json", {
        "meta": {
            "tokenizer": "hf/variants/V3-32k/tokenizer.json (+ V2/V2b/V0 dla szablonu)",
            "definition_right_groups": "długości od prawej, reszta z lewej (8->2+3+3, 4->1+3)",
            "atomic3": "czy ciąg 000–999 jest dokładnie jednym tokenem HF",
        },
        **syn,
    })

    # Słowniki powierzchniowe do ataku 4.
    surf = {}
    forced_ids = {}
    for name in SIZES:
        tok = toks[name]
        n = tok.get_vocab_size()
        table = [surface(tok, i) for i in range(n)]
        surf[name] = table
        forced_ids[name] = {}
        for i, s in enumerate(table):
            k = forced_kind(s)
            if k:
                forced_ids[name].setdefault(k, []).append(i)
        print(name, "vocab", n, {k: len(v) for k, v in forced_ids[name].items()}, flush=True)
    v3_set = set(surf["V3-32k"])
    v2_set = set(surf["V2-32k"])
    surf["V2b-32k"] = [surface(toks["V2b-32k"], i)
                       for i in range(toks["V2b-32k"].get_vocab_size())]

    used = {name: Counter() for name in SIZES}
    # koszty: listy tokenów i słów per dokument
    bucket_names = OFFICIAL + ["web", "wikipedia", "literatura"]
    doc_tok = {b: {name: [] for name in FOCUS} for b in bucket_names}
    doc_words = {b: [] for b in bucket_names}
    # też per dziedzina urzędowa
    per_dom = {d: {name: [] for name in FOCUS} for d in OFFICIAL}
    per_words = {d: [] for d in OFFICIAL}

    # atak 1 i 3 — liczniki
    cpv = Counter()
    dates = Counter()
    cases = Counter()
    postal = Counter()
    years_real = Counter()
    runs = Counter()
    first_tok = defaultdict(Counter)  # digit_string -> first token -> count, tylko V2b
    v2_first = defaultdict(Counter)
    examples = defaultdict(list)

    def add_ex(key, item, limit=6):
        if len(examples[key]) < limit:
            examples[key].append(item)

    def consider_body(name, spans, start, end, counter, prefix):
        lens = piece_lengths(spans, start, end)
        label = shape_label(lens)
        counter[f"{prefix}{name}_shape_{label}"] += 1
        n = end - start
        counter[f"{prefix}{name}_n"] += 1
        if lens == right_lengths(n):
            counter[f"{prefix}{name}_equals_right"] += 1
        # granice wewnętrzne: czy każda pozycja 1..n-1 jest granicą tokenu
        internal_boundaries = sum(1 for k in range(1, n) if not crossed(spans, start + k))
        counter[f"{prefix}{name}_internal_boundaries"] += internal_boundaries
        counter[f"{prefix}{name}_internal_possible"] += max(n - 1, 0)
        if n > 1 and internal_boundaries == n - 1:
            counter[f"{prefix}{name}_every_digit_boundary"] += 1
        if lens is not None and len(lens) > 1:
            counter[f"{prefix}{name}_internally_split"] += 1
        return lens

    n_docs = 0
    for dom in DOMAINS:
        docs = load_domain(dom, "test")
        print("domain", dom, len(docs), flush=True)
        for doc in docs:
            raw = doc["text"]
            text = unicodedata.normalize("NFC", raw)
            n_docs += 1
            words = len(raw.split())
            encs = {}
            for name in names:
                enc = toks[name].encode(raw, add_special_tokens=False)
                encs[name] = enc
                if name in used:
                    used[name].update(enc.ids)
            if dom in OFFICIAL or dom in ("web", "wikipedia", "literatura"):
                key = dom if dom in ("web", "wikipedia", "literatura") else None
                targets = []
                if dom in OFFICIAL:
                    targets.append(dom)  # per domain handled below
                    for name in FOCUS:
                        per_dom[dom][name].append(len(encs[name].ids))
                    per_words[dom].append(words)
                    # official aggregate uses the same lists via per_dom
                if dom in ("web", "wikipedia", "literatura"):
                    doc_words[dom].append(words)
                    for name in FOCUS:
                        doc_tok[dom][name].append(len(encs[name].ids))

            # Struktura na NFC. Gdy tekst już jest NFC, offsety encode(raw) wskazują ten sam napis.
            if text == raw:
                enc_nfc = {name: encs[name] for name in ("V2-32k", "V2b-32k", "V3-32k")}
            else:
                enc_nfc = {name: toks[name].encode(text, add_special_tokens=False)
                           for name in ("V2-32k", "V2b-32k", "V3-32k")}
            sp = {name: spans_of(enc_nfc[name]) for name in enc_nfc}
            indexed = {}
            for name in enc_nfc:
                indexed[name] = [(a, b, i) for i, (a, b) in enumerate(enc_nfc[name].offsets) if b > a]

            scope = "official" if dom in OFFICIAL else "other"

            for m in CPV_RE.finditer(text):
                body_s, body_e = m.start(), m.start() + 8
                near = text[max(0, m.start() - 12):m.start()].upper()
                tagged = "cpv_near" if "CPV" in near else "cpv_any"
                for tag in ("cpv_any", tagged):
                    cpv[f"{scope}_{tag}_n"] += 1
                    for name in ("V2-32k", "V2b-32k", "V3-32k"):
                        lens = piece_lengths(sp[name], body_s, body_e)
                        cpv[f"{scope}_{tag}_{name}_shape_{shape_label(lens)}"] += 1
                        if lens == [2, 3, 3]:
                            cpv[f"{scope}_{tag}_{name}_shape_2_3_3"] += 1
                        # granice hierarchii od lewej
                        for cut, cname in ((2, "dzial"), (3, "grupa"), (4, "klasa"), (5, "kategoria")):
                            if crossed(sp[name], body_s + cut):
                                cpv[f"{scope}_{tag}_{name}_cross_{cname}"] += 1
                            else:
                                cpv[f"{scope}_{tag}_{name}_keep_{cname}"] += 1
                        if lens is not None and all(x == 1 for x in lens):
                            cpv[f"{scope}_{tag}_{name}_all_single_digits"] += 1
                if len(examples["cpv"]) < 8 and scope == "official":
                    examples["cpv"].append({
                        "code": m.group(0),
                        "v3": shape_label(piece_lengths(sp["V3-32k"], body_s, body_e)),
                        "v2_single": piece_lengths(sp["V2-32k"], body_s, body_e) == [1] * 8,
                        "v2b_single": piece_lengths(sp["V2b-32k"], body_s, body_e) == [1] * 8,
                    })

            for m in DATE_RE.finditer(text):
                dates[f"{scope}_n"] += 1
                # grupy: day, sep, month, sep, year
                day_s, day_e = m.start(1), m.end(1)
                mon_s, mon_e = m.start(3), m.end(3)
                yr_s, yr_e = m.start(5), m.end(5)
                for name in ("V2-32k", "V2b-32k", "V3-32k"):
                    yl = piece_lengths(sp[name], yr_s, yr_e)
                    dates[f"{scope}_{name}_year_{shape_label(yl)}"] += 1
                    if piece_lengths(sp[name], day_s, day_e) not in ([1], [2], [len(m.group(1))]):
                        dates[f"{scope}_{name}_day_split_odd"] += 1
                    dl = piece_lengths(sp[name], day_s, day_e)
                    ml = piece_lengths(sp[name], mon_s, mon_e)
                    if dl is not None and len(dl) > 1:
                        dates[f"{scope}_{name}_day_internal_split"] += 1
                    if ml is not None and len(ml) > 1:
                        dates[f"{scope}_{name}_month_internal_split"] += 1
                    if yl is not None and len(yl) > 1:
                        dates[f"{scope}_{name}_year_internal_split"] += 1
                if len(examples["date"]) < 8 and scope == "official":
                    examples["date"].append({
                        "date": m.group(0),
                        "v3_year": shape_label(piece_lengths(sp["V3-32k"], yr_s, yr_e)),
                        "v2_year": shape_label(piece_lengths(sp["V2-32k"], yr_s, yr_e)),
                    })

            for m in CASE_RE.finditer(text):
                cases[f"{scope}_n"] += 1
                # segmenty cyfrowe
                bad = {name: False for name in ("V2-32k", "V2b-32k", "V3-32k")}
                bad4 = {name: False for name in bad}
                segs = list(re.finditer(r"\d+", m.group(0)))
                cases[f"{scope}_segments"] += len(segs)
                for seg in segs:
                    ss, ee = m.start() + seg.start(), m.start() + seg.end()
                    for name in bad:
                        lens = piece_lengths(sp[name], ss, ee)
                        if lens is not None and len(lens) > 1:
                            bad[name] = True
                            cases[f"{scope}_{name}_segments_split"] += 1
                            if len(seg.group(0)) == 4:
                                bad4[name] = True
                                cases[f"{scope}_{name}_yearseg_{shape_label(lens)}"] += 1
                        elif len(seg.group(0)) == 4:
                            cases[f"{scope}_{name}_yearseg_{shape_label(lens)}"] += 1
                        cases[f"{scope}_{name}_segments"] += 1
                for name in bad:
                    if bad[name]:
                        cases[f"{scope}_{name}_case_has_split_segment"] += 1
                    if bad4[name]:
                        cases[f"{scope}_{name}_case_has_split_4digit"] += 1
                if len(examples["case"]) < 8 and scope == "official":
                    examples["case"].append({
                        "case": m.group(0)[:40],
                        "v3_split": bad["V3-32k"],
                        "v2_split": bad["V2-32k"],
                        "v2b_split": bad["V2b-32k"],
                    })

            for m in POSTAL_RE.finditer(text):
                postal[f"{scope}_n"] += 1
                a, b = m.start(2), m.end(2)
                for name in ("V2-32k", "V2b-32k", "V3-32k"):
                    lens = piece_lengths(sp[name], a, b)
                    postal[f"{scope}_{name}_tail_{shape_label(lens)}"] += 1
                    if lens != [3]:
                        postal[f"{scope}_{name}_tail_not_atomic"] += 1

            for m in YEAR_RE.finditer(text):
                years_real[f"{scope}_n"] += 1
                a, b = m.start(1), m.end(1)
                for name in ("V3-32k", "V2-32k", "V2b-32k"):
                    lens = piece_lengths(sp[name], a, b)
                    years_real[f"{scope}_{name}_{shape_label(lens)}"] += 1
                    if lens == right_lengths(4):
                        years_real[f"{scope}_{name}_equals_right"] += 1

            # atak 3: ciągi cyfr, tylko dziedziny urzędowe + web (żeby nie dublować literackich milionów)
            if dom in OFFICIAL or dom == "web":
                where = "official" if dom in OFFICIAL else "web"
                cursor = {name: 0 for name in ("V2b-32k", "V2-32k")}
                for m in RUN_RE.finditer(text):
                    runs[f"{where}_n"] += 1
                    cls = left_class(text, m.start())
                    runs[f"{where}_left_{cls}"] += 1
                    v2b_piece = None
                    for name in ("V2b-32k", "V2-32k"):
                        arr = indexed[name]
                        c = cursor[name]
                        while c < len(arr) and arr[c][1] <= m.start():
                            c += 1
                        cursor[name] = c
                        if c >= len(arr) or arr[c][0] >= m.end():
                            runs[f"{where}_{name}_no_token"] += 1
                            continue
                        piece = surf[name][enc_nfc[name].ids[arr[c][2]]]
                        if name == "V2b-32k":
                            v2b_piece = piece
                        runs[f"{where}_{name}_first"] += 1
                        glued = piece.startswith(" ") or piece.startswith("\u00a0")
                        if glued:
                            runs[f"{where}_{name}_glued_space"] += 1
                        else:
                            runs[f"{where}_{name}_not_glued"] += 1
                        if where == "official" and name == "V2b-32k":
                            first_tok[m.group(0)][piece] += 1
                            runs[f"official_v2b_left_{cls}"] += 1
                            if glued:
                                runs[f"official_v2b_glued_when_{cls}"] += 1
                        if where == "official" and name == "V2-32k":
                            v2_first[m.group(0)][piece] += 1
                    if v2b_piece and cls in (
                        "paren", "slash", "dot", "hyphen", "nr_no_space", "poz_no_space",
                        "quote", "newline", "start", "nbsp") and len(examples["left_" + cls]) < 4:
                        examples["left_" + cls].append({
                            "digits": m.group(0)[:12],
                            "left": cls,
                            "v2b_first": v2b_piece,
                        })

    # agregat urzędowy z dziedzin
    for name in FOCUS:
        doc_tok["official_" ] = None
    official_words = np.concatenate([np.array(per_words[d], dtype=float) for d in OFFICIAL])
    def stack(name):
        return np.concatenate([np.array(per_dom[d][name], dtype=float) for d in OFFICIAL])

    cost = {"per_domain": {}, "official": {}, "web": {}, "wikipedia": {}, "literatura": {}}
    for d in OFFICIAL:
        w = np.array(per_words[d], dtype=float)
        a = np.array(per_dom[d]["V0-32k"], dtype=float)
        cost["per_domain"][d] = {}
        for name in ("V2-32k", "V2b-32k", "V3-32k"):
            b = np.array(per_dom[d][name], dtype=float)
            cost["per_domain"][d][name] = ci_delta_pct(a, b, w)
    a = stack("V0-32k")
    for name in ("V2-32k", "V2b-32k", "V3-32k"):
        cost["official"][name] = ci_delta_pct(a, stack(name), official_words)
    for dom in ("web", "wikipedia", "literatura"):
        w = np.array(doc_words[dom], dtype=float)
        aa = np.array(doc_tok[dom]["V0-32k"], dtype=float)
        cost[dom] = {}
        for name in ("V2-32k", "V2b-32k", "V3-32k"):
            bb = np.array(doc_tok[dom][name], dtype=float)
            cost[dom][name + "_vs_V0"] = ci_delta_pct(aa, bb, w)
        # V3 vs V2 — cena braku tokenów V2
        cost[dom]["V3-32k_vs_V2-32k"] = ci_delta_pct(
            np.array(doc_tok[dom]["V2-32k"], dtype=float),
            np.array(doc_tok[dom]["V3-32k"], dtype=float),
            w,
        )
        cost[dom]["V3-32k_vs_V2b-32k"] = ci_delta_pct(
            np.array(doc_tok[dom]["V2b-32k"], dtype=float),
            np.array(doc_tok[dom]["V3-32k"], dtype=float),
            w,
        )

    # atak 4: martwe, wymuszone, tokeny które wypadły
    vocab_report = {}
    for name in SIZES:
        tok = toks[name]
        n = tok.get_vocab_size()
        seen = used[name]
        dead = n - len(seen)
        kinds = {}
        for kind, ids in forced_ids[name].items():
            alive = sum(1 for i in ids if seen[i] > 0)
            rare = sum(1 for i in ids if 0 < seen[i] < 5)
            uses = sum(seen[i] for i in ids)
            kinds[kind] = {"in_vocab": len(ids), "used": alive, "dead": len(ids) - alive,
                           "rare_lt5": rare, "uses": int(uses)}
        bare = kinds.get("bare2", {}).get("in_vocab", 0) + kinds.get("bare3", {}).get("in_vocab", 0)
        bare_dead = kinds.get("bare2", {}).get("dead", 0) + kinds.get("bare3", {}).get("dead", 0)
        all_forced = sum(v["in_vocab"] for v in kinds.values())
        all_forced_dead = sum(v["dead"] for v in kinds.values())
        vocab_report[name] = {
            "vocab": n,
            "used_types": len(seen),
            "dead": dead,
            "dead_share": dead / n,
            "forced_kinds": kinds,
            "bare_00_99_and_000_999": bare,
            "bare_share_of_vocab": bare / n,
            "bare_dead": bare_dead,
            "bare_dead_share_of_vocab": bare_dead / n,
            "all_forced_incl_space": all_forced,
            "all_forced_share_of_vocab": all_forced / n,
            "all_forced_dead": all_forced_dead,
            "all_forced_dead_share_of_vocab": all_forced_dead / n,
        }

    # tokeny V2 nieobecne w V3
    missing = []
    v2_counts = used["V2-32k"]
    total_v2 = sum(v2_counts.values())
    missing_uses = 0
    dup_uses = 0
    ordinary_missing = []
    for i, c in v2_counts.items():
        s = surf["V2-32k"][i]
        if s in v3_set:
            continue
        missing_uses += c
        is_dup = s.endswith(" ") and s[:-1] in v3_set
        if is_dup:
            dup_uses += c
        rec = {"surface": s, "uses_test": int(c), "trailing_space_dup": is_dup,
               "numberish": numberish(s)}
        missing.append(rec)
        if not numberish(s):
            ordinary_missing.append(rec)
    missing.sort(key=lambda r: -r["uses_test"])
    ordinary_missing.sort(key=lambda r: -r["uses_test"])
    ordinary_nodup = [r for r in ordinary_missing if not r["trailing_space_dup"]]

    # koszt izolowany: brakujące tokeny V2 na web/wikipedia nie mamy per-domena id.
    # Mamy globalne użycia na całym teście. Dołożymy osobny przebieg? 
    # Użycia per web zebraliśmy tylko długości. Policzmy udział brakujących
    # typów w całym teście i dodatkowo przeliczymy web/wikipedia z zapisanych? 
    # Nie zapisaliśmy id per domena. Dopiszemy szacunek z całego testu oraz
    # izolowane rozbicie top tokenów.
    v3 = toks["V3-32k"]
    top50 = ordinary_missing[:50]
    top50_nodup = ordinary_nodup[:50]
    for rec in top50 + top50_nodup:
        ids = v3.encode(rec["surface"], add_special_tokens=False).ids
        rec["v3_pieces"] = [v3.decode([i]) for i in ids]
        rec["v3_len"] = len(ids)
        rec["extra_per_use"] = len(ids) - 1

    # Ile użyć V2 na web/wikipedia przypada na typy spoza V3 — drugi, wąski przebieg.
    print("recount web/wikipedia missing", flush=True)
    recount = {}
    for dom in ("web", "wikipedia", "literatura"):
        miss_u = dup_u = num_u = ord_u = tot = 0
        for doc in load_domain(dom, "test"):
            ids = toks["V2-32k"].encode(doc["text"], add_special_tokens=False).ids
            tot += len(ids)
            for i in ids:
                s = surf["V2-32k"][i]
                if s in v3_set:
                    continue
                miss_u += 1
                if numberish(s):
                    num_u += 1
                elif s.endswith(" ") and s[:-1] in v3_set:
                    dup_u += 1
                else:
                    ord_u += 1
        recount[dom] = {"v2_tokens": tot, "uses_of_types_missing_in_v3": miss_u,
                        "share_missing": miss_u / tot if tot else None,
                        "missing_numberish": num_u, "missing_trailing_space_dup": dup_u,
                        "missing_other_ordinary": ord_u}

    # różnorodność pierwszego tokenu V2b
    div_hist = Counter()
    multi = 0
    considered = 0
    examples_div = []
    for digits, ctr in first_tok.items():
        if sum(ctr.values()) < 2:
            continue
        considered += 1
        k = len(ctr)
        div_hist[str(k)] += 1
        if k > 1:
            multi += 1
            if len(examples_div) < 15:
                examples_div.append({"digits": digits[:16], "first_tokens": ctr.most_common(6),
                                     "n": int(sum(ctr.values()))})
    v2_div_hist = Counter()
    v2_multi = v2_considered = 0
    for digits, ctr in v2_first.items():
        if sum(ctr.values()) < 2:
            continue
        v2_considered += 1
        k = len(ctr)
        v2_div_hist[str(k)] += 1
        if k > 1:
            v2_multi += 1

    write("attack1_hierarchy.json", {
        "meta": {
            "split": "test",
            "text": "NFC przed dopasowaniem wzorca; encode(NFC), offsety znakowe",
            "cpv": r"\b\d{8}-\d\b ; ciało = 8 cyfr; granice od lewej: 2 dział, 3 grupa, 4 klasa, 5 kategoria",
            "niezgodny_cpv": "token przecina granicę grupy (pozycja 3) albo klasy (pozycja 4)",
            "prefiks_cyfra": "każda z 8 cyfr jest osobnym tokenem (granica po każdej cyfrze)",
            "data": r"\b\d{1,2}[./-]\d{1,2}[./-]\d{4}\b",
            "znak_sprawy": "wzorzec z audit/notation_patterns.py; segment cyfrowy rozcięty = >1 tokenu w środku",
            "kod_pocztowy": r"\b\d{2}-\d{3}\b ; ogon 3-cyfrowy powinien być atomowy, jeśli obietnica 000–999 działa",
            "docs_test": n_docs,
        },
        "cpv": dict(cpv),
        "dates": dict(dates),
        "cases": dict(cases),
        "postal": dict(postal),
        "years_in_test": dict(years_real),
        "examples": {"cpv": examples["cpv"], "date": examples["date"], "case": examples["case"]},
    })

    write("attack3_v2b_context.json", {
        "meta": {
            "split": "test",
            "domains": "7 urzędowych + web",
            "run": "maksymalny ciąg \\d+",
            "glued": "pierwszy token V2b zaczyna się od spacji (projekt: ·0…·9)",
            "distinct": "ile różnych pierwszych tokenów ma ten sam ciąg cyfr, gdy występuje ≥2 razy",
        },
        "counts": dict(runs),
        "v2b_digit_strings_with_ge2": considered,
        "v2b_digit_strings_with_gt1_first_token": multi,
        "v2b_share_inconsistent": (multi / considered) if considered else None,
        "v2b_distinct_first_hist": dict(div_hist),
        "v2_digit_strings_with_ge2": v2_considered,
        "v2_digit_strings_with_gt1_first_token": v2_multi,
        "v2_distinct_first_hist": dict(v2_div_hist),
        "examples_inconsistent": examples_div,
        "examples_left": {k: v for k, v in examples.items() if k.startswith("left_")},
    })

    write("attack4_vocab.json", {
        "meta": {
            "split": "test",
            "dead": "rozmiar słownika minus liczba typów zaobserwowanych w encode(test), jak tkx_c/measure.py",
            "bare1100": "00–99 oraz 000–999 (1100), bez wersji ze spacją",
            "forced2210": "bare + spacja+cyfra + spacja+00–99 + spacja+000–999",
            "ordinary": "token V2, którego powierzchni nie ma w V3 i który nie jest samymi cyframi",
            "trailing_space_dup": "kończy się spacją, a ten sam napis bez ostatniej spacji jest w V3",
        },
        "variants": vocab_report,
        "v2_tokens_test": int(total_v2),
        "v2_uses_missing_from_v3": int(missing_uses),
        "v2_uses_missing_share": missing_uses / total_v2 if total_v2 else None,
        "v2_uses_trailing_space_dup": int(dup_uses),
        "top50_ordinary_missing_incl_space_dups": top50,
        "top50_ordinary_missing_excl_space_dups": top50_nodup,
        "web_wiki_lit_missing_uses": recount,
        "cost_vs_v0_and_v2": cost,
    })
    print("DONE", n_docs, flush=True)


if __name__ == "__main__":
    main()
