"""Koszt wariantu „każda cyfra osobnym tokenem” — brakujący pomiar z rundy 2.

Metoda dolnej granicy za `audit/independent/codex/compute_codex.py` (A7, Codex):
dla każdego tokenu z cyframi dokładamy `max(0, liczba_cyfr - 1)` tokenów.
Metoda górnej granicy (Grok, `audit/independent/grok/`): każda cyfra to osobny token,
a niecyfrowa reszta tego samego tokenu to jeden token.

To **szacunek**, nie tokenizer po retreningu. Wynik: audit/results/digits_cost.json
"""
from __future__ import annotations

import json
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common import RESULTS_DIR, load_domain, load_superbpe, write_json

DOMAINS = ["przetargi_ogloszenia", "przetargi_kio", "samorzad_uchwaly",
           "granty_ogloszenia", "prawo_eli", "ocr_prasa", "tabele_json",
           "web", "wikipedia", "literatura", "prawo", "sejm", "nauka",
           "dyskusje", "angielski"]
OFFICIAL = DOMAINS[:7]
GROK_FULL = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "independent", "grok", "r3_context_full.json")


def main() -> None:
    tok = load_superbpe("tokenizers/tokenizatorex-32k.json")
    out = {"meta": {"tokenizer": "TOKENIZATOREX",
                    "method_lower": "Codex A7: sum(max(0, cyfry_w_tokenie - 1))",
                    "method_upper": "Grok: każda cyfra osobno + niecyfrowa reszta jako 1 token",
                    "scope": "test, dokumenty przycięte do 20 tys. znaków",
                    "note": "szacunek, nie wynik po retreningu; prawdziwy koszt zmierzy TKX-C"},
           "domains": {}}
    pooled = {"tokens": 0, "digits": 0, "lower": 0, "upper": 0, "words": 0}
    for dom in DOMAINS:
        docs = load_domain(dom, "test")
        if not docs:
            continue
        tokens = digits = words = chars = lower = upper = tokens_digit = 0
        words_digit = 0
        for d in docs:
            text = d["text"]
            chars += len(text)
            ws = text.split()
            words += len(ws)
            digits += sum(c.isdigit() for c in text)
            words_digit += sum(1 for w in ws if any(c.isdigit() for c in w))
            ids = tok.encode_ordinary(text)
            tokens += len(ids)
            for i in ids:
                piece = tok.decode([i])
                k = sum(c.isdigit() for c in piece)
                if not k:
                    continue
                tokens_digit += 1
                lower += max(0, k - 1)
                rest = len(piece) - k
                upper += (k + (1 if rest else 0)) - 1
        row = {"docs": len(docs), "chars": chars, "words": words,
               "digits": digits, "digit_char_share": digits / chars if chars else None,
               "words_with_digit": words_digit,
               "number_word_share": words_digit / words if words else None,
               "tokens": tokens, "tokens_with_digit": tokens_digit,
               "lower_extra_tokens": lower,
               "lower_pct_of_tokens": lower / tokens if tokens else None,
               "upper_extra_tokens": upper,
               "upper_pct_of_tokens": upper / tokens if tokens else None}
        out["domains"][dom] = row
        if dom in OFFICIAL:
            for k in pooled:
                pooled[k] += {"tokens": tokens, "digits": digits, "lower": lower,
                              "upper": upper, "words": words}[k]
        print(f"{dom:<22} cyfry {row['digit_char_share']:.2%}  lower +{row['lower_pct_of_tokens']:.2%}  "
              f"upper +{row['upper_pct_of_tokens']:.2%}")

    out["official_pooled"] = {
        **pooled,
        "docs": sum(load_domain(d, "test").__len__() for d in OFFICIAL),
        "digit_char_share": pooled["digits"] / sum(len(d["text"]) for d in
                                                   [x for dom in OFFICIAL for x in load_domain(dom, "test")]),
        "lower_pct_of_tokens": pooled["lower"] / pooled["tokens"],
        "upper_pct_of_tokens": pooled["upper"] / pooled["tokens"],
    }
    # pełne ogłoszenie z rundy 3 (Grok) — tylko odczyt cudzego JSON-a
    if os.path.exists(GROK_FULL):
        g = json.load(open(GROK_FULL, encoding="utf-8"))["domains"]["przetargi_ogloszenia"]
        cur, up = g["current"]["median"], g["digits_upper"]["median"]
        out["grok_full_notice"] = {
            "source": "audit/independent/grok/r3_context_full.json",
            "median_current": cur, "median_upper": up,
            "delta_pct": (up - cur) / cur,
            "fit_2048_current": g["current"]["fit_2048"],
            "fit_4096_current": g["current"]["fit_4096"],
            "fit_4096_upper": g["digits_upper"]["fit_4096"],
        }
    write_json(os.path.join(RESULTS_DIR, "digits_cost.json"), out)
    write_md(out)


def write_md(out: dict) -> None:
    lines = ["# Koszt „każda cyfra osobno” (szacunek)", "",
             "Dolna granica: metoda Codex A7 (`sum(max(0, cyfry_w_tokenie − 1))`).",
             "Górna granica: każda cyfra osobno + niecyfrowa reszta jako jeden token (Grok).",
             "", "| dziedzina | udział cyfr w znakach | dolna [% tokenów] | górna [% tokenów] |",
             "|---|---:|---:|---:|"]
    for d, r in out["domains"].items():
        lines.append(f"| {d} | {r['digit_char_share']:.2%} | +{r['lower_pct_of_tokens']:.2%} | "
                     f"+{r['upper_pct_of_tokens']:.2%} |")
    p = out["official_pooled"]
    lines += ["", f"Razem 7 dziedzin urzędowych: dolna +{p['lower_pct_of_tokens']:.2%}, "
                  f"górna +{p['upper_pct_of_tokens']:.2%} tokenów."]
    if "grok_full_notice" in out:
        g = out["grok_full_notice"]
        lines += ["", f"Pełne ogłoszenie (Grok, bez cięcia 20k): mediana {g['median_current']:.0f} → "
                      f"{g['median_upper']:.0f} tokenów (+{g['delta_pct']:.1%}); "
                      f"w 4096 mieści się {g['fit_4096_current']:.1%} dziś i "
                      f"{g['fit_4096_upper']:.1%} po rozbiciu cyfr."]
    lines += ["", "To jest szacunek, nie tokenizer po retreningu; prawdziwy koszt zmierzy TKX-C.",
              "Liczby różnią się między źródłami, bo Codex liczy na tekście przyciętym do 20 tys.",
              "znaków, a Grok odbudował pełne dokumenty; metody dolna/górna też są różne."]
    path = os.path.join(RESULTS_DIR, "digits_cost.md")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
