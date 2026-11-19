"""Runda 1.3 — spójność podziału w kontekstach (H3, H4; część H2).

Dla tych samych łańcuchów w 7 kontekstach sprawdza, czy segmentacja fragmentu
obejmującego zapis jest taka sama. Segmentację wyznaczamy przez dekodowanie
kolejnych tokenów i mapowanie na pozycje znakowe.

Wynik: audit/results/consistency.json (+ consistency.md)
"""
from __future__ import annotations

import os
import sys
from collections import Counter

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common import RESULTS_DIR, build_encoders, load_domain, write_json
from notation_patterns import ABBREVIATIONS, CODE_CATEGORIES, PATTERNS, extract

DOMAINS = ["przetargi_ogloszenia", "przetargi_kio", "samorzad_uchwaly",
           "granty_ogloszenia", "prawo_eli", "ocr_prasa", "tabele_json", "web"]
MAX_STRINGS = 150
SENSITIVE = {"nip", "email", "url"}


def contexts(s: str) -> dict[str, str]:
    return {
        "bare": s,
        "start": f"{s} jest przedmiotem postępowania.",
        "srodek": f"W dniu {s} podpisano umowę.",
        "przed_kropka": f"Informacja: {s}.",
        "nawias": f"Dokument ({s}) jest dostępny.",
        "po_spacji": f" wartość {s} brutto",
        "bez_spacji": f"wartość:{s}",
    }


def abbr_contexts(a: str) -> dict[str, str]:
    return {
        "bare": a,
        "start": f"{a} 5 stanowi podstawę.",
        "srodek": f"Zgodnie z {a} 5 ustawy.",
        "przed_kropka": f"Zobacz {a}",
        "nawias": f"({a} 5)",
        "po_spacji": f" {a} 5",
        "bez_spacji": f"x{a}5",
    }


def span_signature(enc, ctx: str, s: str):
    """Sygnatura podziału *samego zapisu*, bez przyklejonej spacji z kontekstu.

    (start_mid, end_mid, wewnętrzne granice tokenów). ``start_mid`` = przed
    zapisem w tym samym tokenie jest nie-biały znak (zapis zaczyna się w środku
    tokenu); ``end_mid`` analogicznie po zapisie. Białe znaki z kontekstu nie
    zmieniają sygnatury.
    """
    start = ctx.find(s)
    if start < 0:
        return None
    end = start + len(s)
    ids = enc.ids(ctx)
    pos = 0
    pieces = []
    for i in ids:
        piece = enc.decode([i])
        pieces.append((pos, pos + len(piece), piece))
        pos += len(piece)
    start_mid = end_mid = False
    internal = []
    for a, b, piece in pieces:
        if b <= start or a >= end:
            continue
        if a < start and piece[:start - a].strip():
            start_mid = True
        if b > end and piece[end - a:].strip():
            end_mid = True
        for boundary in (a, b):
            if start < boundary < end:
                internal.append(boundary - start)
    return (start_mid, end_mid, tuple(sorted(set(internal))))


def _tokens_for(enc, ctx: str, s: str):
    start = ctx.find(s)
    if start < 0:
        return []
    end = start + len(s)
    ids = enc.ids(ctx)
    pos = 0
    out = []
    for i in ids:
        piece = enc.decode([i])
        a, b = pos, pos + len(piece)
        if b > start and a < end:
            out.append(piece)
        pos = b
    return out


def analyse(encoders, samples: dict[str, list[str]], ctx_fn) -> dict:
    out = {}
    for cat, strings in samples.items():
        if not strings:
            continue
        per_tok = {}
        for label, enc in encoders.items():
            total = diff = 0
            varying_strings = 0
            examples = []
            for s in strings:
                sigs = {}
                for name, ctx in ctx_fn(s).items():
                    sig = span_signature(enc, ctx, s)
                    if sig is not None:
                        sigs[name] = sig
                if not sigs:
                    continue
                c = Counter(sigs.values())
                best, best_n = c.most_common(1)[0]
                d = len(sigs) - best_n
                total += len(sigs)
                diff += d
                if len(c) > 1:
                    varying_strings += 1
                    if len(examples) < 3 and cat not in SENSITIVE:
                        alt = {k: {"signature": list(v),
                                   "tokens": _tokens_for(enc, ctx_fn(s)[k], s)}
                               for k, v in sigs.items() if v != best}
                        examples.append({"string": s,
                                         "most_common": {"signature": list(best),
                                                         "tokens": _tokens_for(enc, ctx_fn(s)[
                                                             max(sigs, key=lambda k: 1 if sigs[k] == best else 0)], s)},
                                         "alternatives": alt})
            per_tok[label] = {
                "pairs": total,
                "share_other_segmentation": (diff / total) if total else float("nan"),
                "strings_with_variation_share": (varying_strings / len(strings)) if strings else float("nan"),
                "examples": examples,
            }
        out[cat] = {"strings": len(strings), "tokenizers": per_tok}
    return out


def main() -> None:
    encoders = build_encoders()
    samples: dict[str, list[str]] = {}
    for cat in PATTERNS:
        found = []
        for dom in DOMAINS:
            for d in load_domain(dom, "test"):
                for s in extract(d["text"], cat, 500):
                    s = s.strip()
                    if 2 <= len(s) <= 60 and "\n" not in s and "\t" not in s:
                        found.append(s)
                if len(found) > 5000:
                    break
        uniq = sorted(set(found))[:MAX_STRINGS]
        samples[cat] = uniq

    out = {"meta": {"max_strings": MAX_STRINGS, "contexts": list(contexts("X")),
                    "split": "test"},
           "categories": analyse(encoders, samples, contexts),
           "abbreviations": analyse(encoders, {a: [a] for a in ABBREVIATIONS}, abbr_contexts)}

    # werdykty H3/H4 na TOKENIZATOREX
    ref = "TOKENIZATOREX"
    h3_cats = [a for a in ABBREVIATIONS
               if out["abbreviations"][a]["tokenizers"][ref]["share_other_segmentation"] >= 0.05]
    h4_cats = [c for c, r in out["categories"].items()
               if r["tokenizers"][ref]["share_other_segmentation"] >= 0.05]
    out["verdict"] = {
        "H3_abbreviations_with_variation_ge_5pct": h3_cats,
        "H3_confirmed": len(h3_cats) >= 2,
        "H4_categories_with_variation_ge_5pct": h4_cats,
        "H4_confirmed": len(h4_cats) >= 1,
        "H2_code_categories_with_variation_ge_5pct": [c for c in CODE_CATEGORIES
                                                      if c in h4_cats],
    }
    write_json(os.path.join(RESULTS_DIR, "consistency.json"), out)
    write_md(out)
    print("H3", out["verdict"]["H3_confirmed"], h3_cats)
    print("H4", out["verdict"]["H4_confirmed"], h4_cats)


def write_md(out: dict) -> None:
    ref = "TOKENIZATOREX"
    lines = ["# Spójność podziału w kontekstach (test)", "",
             "Udział (string, kontekst), gdzie segmentacja zapisu różni się od "
             "najczęstszej dla tego stringu. Mniej = lepiej.", "",
             "| kategoria | stringów | TOKENIZATOREX | HF | Slayer1B | Pollock |",
             "|---|---:|---:|---:|---:|---:|"]
    for cat, r in out["categories"].items():
        row = [f"{r['tokenizers'][l]['share_other_segmentation']:.1%}"
               for l in (ref, "TOKENIZATOREX-HF", "Slayer1B", "Pollock-2.0")]
        lines.append(f"| {cat} | {r['strings']} | " + " | ".join(row) + " |")
    lines += ["", "## Skróty urzędowe", "",
              "| skrót | TOKENIZATOREX | HF | Slayer1B | przykłady różnych podziałów |",
              "|---|---:|---:|---:|---|"]
    for a, r in out["abbreviations"].items():
        t = r["tokenizers"][ref]
        ex = ""
        if t["examples"]:
            e = t["examples"][0]
            ex = " / ".join(["·".join(e["most_common"]["tokens"])] +
                            ["·".join(v["tokens"]) for v in list(e["alternatives"].values())[:2]])
        lines.append(f"| `{a}` | {t['share_other_segmentation']:.1%} | "
                     f"{r['tokenizers']['TOKENIZATOREX-HF']['share_other_segmentation']:.1%} | "
                     f"{r['tokenizers']['Slayer1B']['share_other_segmentation']:.1%} | {ex} |")
    lines += ["", "## Werdykt", ""]
    v = out["verdict"]
    lines.append(f"* H3: {'POTWIERDZONA' if v['H3_confirmed'] else 'OBALONA'} "
                 f"(skróty z ≥5%: {', '.join(v['H3_abbreviations_with_variation_ge_5pct']) or 'brak'})")
    lines.append(f"* H4: {'POTWIERDZONA' if v['H4_confirmed'] else 'OBALONA'} "
                 f"(kategorie z ≥5%: {', '.join(v['H4_categories_with_variation_ge_5pct']) or 'brak'})")
    path = os.path.join(RESULTS_DIR, "consistency.md")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("zapisano", path)


if __name__ == "__main__":
    main()
