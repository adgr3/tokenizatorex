"""Part B: niezalezna weryfikacja metryki spójnosci (H3/H4) wykonawcy.

Wlasna implementacja specyfikacji: ten sam zapis w 7 kontekstach, sygnatura
podzialu = (start_mid, end_mid, wewnetrzne granice),udzial par z podzialem
innym niz najczestszy. Probe wyciagamy z raw/test wlasnym kodem.
"""
import tokenizers as hf  # HF pierwszy
from tokenizers import Tokenizer
import json, pathlib, re, collections

REPO = pathlib.Path(__file__).resolve().parents[2]
RAW = REPO / "audit" / "data" / "raw"
OFFICIAL = ["przetargi_ogloszenia", "przetargi_kio", "samorzad_uchwaly",
            "granty_ogloszenia", "prawo_eli", "ocr_prasa", "tabele_json"]
MAX_STRINGS = 100
VARIANTS = ["V0-32k", "V1-32k", "V2-32k", "V2b-32k", "V3-32k"]

PATTERNS = {
    "kwota": r"(?<![\d,])\d{1,3}(?:[ \u00a0]\d{3})*(?:,\d{1,2})?\s*(?:zł|PLN)\b",
    "data_slowna": (r"\b\d{1,2}\s+(?:stycznia|lutego|marca|kwietnia|maja|czerwca|lipca|"
                    r"sierpnia|września|października|listopada|grudnia)\s+\d{4}(?:\s*r\.)?"),
    "data_cyfrowa": r"\b\d{1,2}[./-]\d{1,2}[./-]\d{4}\b",
    "rok": r"(?<!\d)(?:19|20)\d{2}(?!\d)",
    "rok_z_r": r"(?<!\d)(?:19|20)\d{2}\s*r\.",
    "godzina": r"\b\d{1,2}[:.]\d{2}\b",
    "przepis": (r"\bart\.\s*\d+[a-z]?(?:\s*ust\.\s*\d+[a-z]?)?"
                r"(?:\s*pkt\s*\d+)?(?:\s*lit\.\s*[a-z])?"),
    "publikator": r"\b(?:Dz\.\s?U\.|M\.\s?P\.)",
    "poz": r"\bpoz\.\s*\d+\b",
    "cpv": r"\b\d{8}-\d\b",
    "znak_sprawy": r"\b[A-Z]{1,4}[./-]\d{1,4}(?:[./-]\d{1,4}){1,3}\b",
    "sygnatura_kio": r"\bKIO\s+\d+/\d{2}\b",
    "sygnatura_sadu": r"\b(?:II|III|IV|I|V|VI|VII|VIII|IX|X)\s+[A-Z]{2}(?:/[A-Z]{2,3})?\s+\d+/\d{2}\b",
    "uchwala": r"(?i)\buchwała\s+nr\s+[IVXLCDM]+/\d+/\d{2,4}\b",
    "procent": r"(?<![\d,])\d+(?:[.,]\d+)?\s?%",
    "kod_pocztowy": r"\b\d{2}-\d{3}\b",
    "email": r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b",
    "url": r"https?://[^\s<>\")\]]+",
    "nip": r"\bNIP[:\s]*\d{3}-?\d{3}-?\d{2}-?\d{2}\b",
}
COMPILED = {k: re.compile(v) for k, v in PATTERNS.items()}

ctx_fn = lambda s: {
    "bare": s,
    "start": f"{s} jest przedmiotem postępowania.",
    "srodek": f"W dniu {s} podpisano umowę.",
    "przed_kropka": f"Informacja: {s}.",
    "nawias": f"Dokument ({s}) jest dostępny.",
    "po_spacji": f" wartość {s} brutto",
    "bez_spacji": f"wartość:{s}",
}


def docs(dom):
    out = []
    for f in sorted((RAW / dom).glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        if d.get("split") == "test":
            out.append(d["text"])
    return out


def extract_samples(cat):
    found = []
    for dom in OFFICIAL + ["web"]:
        for text in docs(dom):
            for m in COMPILED[cat].finditer(text):
                found.append(m.group(0).strip())
                if len(found) > 3000:
                    break
            if len(found) > 3000:
                break
        if len(found) > 3000:
            break
    return sorted(set(s for s in found if 2 <= len(s) <= 60 and "\n" not in s and "\t" not in s))[:MAX_STRINGS]


def signature(tok, ctx, s):
    """Wlasna implementacja sygnatury podzialu fragmentu s w kontekscie ctx."""
    a = ctx.find(s)
    if a < 0:
        return None
    b = a + len(s)
    ids = tok.encode(ctx, add_special_tokens=False).ids
    bounds = []
    pos = 0
    start_mid = end_mid = False
    for tid in ids:
        piece = tok.decode([tid], skip_special_tokens=False)
        start, end = pos, pos + len(piece)
        pos = end
        if end <= a or start >= b:
            continue
        if start < a < end and piece[:a-start].strip():
            start_mid = True
        if start < b < end and piece[b-start:].strip():
            end_mid = True
        for q in (start, end):
            if a < q < b:
                bounds.append(q - a)
    return (start_mid, end_mid, tuple(sorted(set(bounds))))


def analyse(tok, strings):
    total = diff = 0
    for s in strings:
        sigs = {}
        for name, ctx in ctx_fn(s).items():
            sig = signature(tok, ctx, s)
            if sig is not None:
                sigs[name] = sig
        if not sigs:
            continue
        c = collections.Counter(sigs.values())
        top = c.most_common(1)[0][1]
        total += len(sigs)
        diff += len(sigs) - top
    return {"pairs": total, "share_other": diff / total if total else None}


def main():
    toks = {v: Tokenizer.from_file(str(REPO / "hf" / "variants" / v / "tokenizer.json")) for v in VARIANTS}
    mine = {}
    for cat in PATTERNS:
        strings = extract_samples(cat)
        mine[cat] = {v: analyse(toks[v], strings) for v in VARIANTS}
    theirs = json.loads((REPO / "tkx_c" / "results" / "consistency.json").read_text(encoding="utf-8"))
    print("kategoria".ljust(18), "wariant".ljust(9), "moje", "ich", "roznica")
    diffs = []
    for cat in ["kwota", "data_cyfrowa", "przepis", "cpv", "znak_sprawy",
                "publikator", "poz", "rok", "rok_z_r"]:
        for v in VARIANTS:
            m = mine[cat][v]["share_other"]
            t = theirs["categories"][cat][v]["share_other"]
            d = None if (m is None or t is None) else round(m - t, 6)
            print(cat.ljust(18), v.ljust(9), f"{m}", f"{t}", d)
            if d is not None:
                diffs.append(abs(d))
    print("max |diff| =", max(diffs))
    dest = REPO / "tkx_c" / "review_codex" / "verify_consistency.json"
    dest.write_text(json.dumps({"mine": mine, "theirs": theirs["categories"],
                                "max_abs_diff": max(diffs)}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", dest)


if __name__ == "__main__":
    main()
