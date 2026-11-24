"""Test formatów dat, kwot i „§” (metoda z formaty_dat_kwot_PM.py).

12 zapisów dat, 9 zapisów kwot, 9 form z „§”; średnia po 40 wygenerowanych
przykładach na format; seed 20261123 (ten sam co w całym TKX-ZOO).
"""
from __future__ import annotations

import random
import statistics

SEED = 20261123

MIES = [
    "stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca",
    "lipca", "sierpnia", "września", "października", "listopada", "grudnia",
]
RZYM = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]

DATY = {
    "RRRR.MM.DD": lambda y, m, d: f"{y}.{m:02d}.{d:02d}",
    "RRRR-MM-DD": lambda y, m, d: f"{y}-{m:02d}-{d:02d}",
    "DD.MM.RRRR": lambda y, m, d: f"{d:02d}.{m:02d}.{y}",
    "D.MM.RRRR": lambda y, m, d: f"{d}.{m:02d}.{y}",
    "DD.MM.RRRR r.": lambda y, m, d: f"{d:02d}.{m:02d}.{y} r.",
    "D.MM.RRRRr.": lambda y, m, d: f"{d}.{m:02d}.{y}r.",
    "DD/MM/RRRR": lambda y, m, d: f"{d:02d}/{m:02d}/{y}",
    "D miesiąca RRRR r.": lambda y, m, d: f"{d} {MIES[m - 1]} {y} r.",
    "D miesiąca RRRRr.": lambda y, m, d: f"{d} {MIES[m - 1]} {y}r.",
    "z dnia D miesiąca RRRR r.": lambda y, m, d: f"z dnia {d} {MIES[m - 1]} {y} r.",
    "D RZYM RRRR": lambda y, m, d: f"{d} {RZYM[m - 1]} {y}",
    "D.RZYM.RRRR": lambda y, m, d: f"{d}.{RZYM[m - 1]}.{y}",
}


def _sp(x):
    return f"{int(x):,}".replace(",", " ")


KWOTY = {
    "1 234,56 zł": lambda a: f"{_sp(a)},{round(a % 1 * 100):02d} zł",
    "1234,56 zł": lambda a: f"{int(a)},{round(a % 1 * 100):02d} zł",
    "1.234,56 zł": lambda a: f"{int(a):,}".replace(",", ".") + f",{round(a % 1 * 100):02d} zł",
    "1234.56 PLN": lambda a: f"{a:.2f} PLN",
    "1 234,56 PLN": lambda a: f"{_sp(a)},{round(a % 1 * 100):02d} PLN",
    "1 234 zł": lambda a: f"{_sp(a)} zł",
    "kwota brutto: 1 234,56 zł": lambda a: f"kwota brutto: {_sp(a)},{round(a % 1 * 100):02d} zł",
    "1,2 mln zł": lambda a: f"{a / 1e6:.1f}".replace(".", ",") + " mln zł",
    "123 tys. zł": lambda a: f"{int(a / 1000)} tys. zł",
}

PARAGRAFY = [
    "§", "§ 5", "§ 12 ust. 3", "§ 12 ust. 3 pkt 4 lit. a", "§5",
    "§§ 3–5", "w § 2", "zgodnie z § 14 ust. 1", "art. 5 § 2",
]

PRZYKZADY = [
    "2 stycznia 2026 r.",
    "1 234 567,89 zł",
    "§ 12 ust. 3 pkt 4 lit. a",
]


def cases():
    """Dokładnie ta sama kolejność rng co w formaty_dat_kwot_PM.py."""
    rng = random.Random(SEED)
    dates = [(rng.randint(2019, 2027), rng.randint(1, 12), rng.randint(1, 28)) for _ in range(40)]
    amts = [
        rng.choice([rng.randint(100, 999), rng.randint(1000, 99999), rng.randint(100000, 9999999)])
        + rng.randint(0, 99) / 100
        for _ in range(40)
    ]
    return dates, amts


def token_text(enc):
    """Teksty tokenów; HF daje .tokens, tiktoken wrapper daje decoded ids."""
    toks = getattr(enc, "tokens", None)
    if toks:
        return [str(t) for t in toks]
    return []


def segment(tok, text):
    enc = tok.encode(text, add_special_tokens=False)
    texts = token_text(enc)
    if not texts:
        texts = [tok.decode([i]) for i in enc.ids]
    return list(texts), len(enc.ids)


def clean_digit_token(t):
    for prefix in ("Ġ", "▁", "##", " ", "Ċ"):
        if t.startswith(prefix):
            t = t[len(prefix):]
            break
    return t


def digit_style(tok):
    """Jak tokenizer tnie długi ciąg cyfr."""
    tokens, _ = segment(tok, "1234567890")
    ds = [clean_digit_token(t) for t in tokens if clean_digit_token(t)]
    only_digits = all(x.isdigit() for x in ds) and ds
    if only_digits and all(len(x) == 1 for x in ds):
        style = "pojedynczo"
    elif only_digits and all(len(x) in (1, 2, 3) for x in ds) and any(len(x) == 3 for x in ds):
        style = "grupy 1–3 (zwykle po 3)"
    elif only_digits and any(len(x) > 3 for x in ds):
        style = "inaczej: długie grupy"
    else:
        style = "inaczej"
    return {"style": style, "tokens_1234567890": tokens}


def measure_all(toks, ids_fn):
    """ids_fn(tok, text) -> lista id; używamy jej dla liczb, segmentacji dla tekstów."""
    dates, amts = cases()
    out = {"seed": SEED, "n_cases": len(dates), "date_formats": {}, "amount_formats": {},
           "paragraph_forms": {}, "segmentation": {}, "digit_split": {}}
    for label, tok in toks.items():
        dmeans, ameans, pcounts = {}, {}, {}
        for name, fn in DATY.items():
            dmeans[name] = statistics.mean(len(ids_fn(tok, fn(*d))) for d in dates)
        for name, fn in KWOTY.items():
            ameans[name] = statistics.mean(len(ids_fn(tok, fn(a))) for a in amts)
        for p in PARAGRAFY:
            pcounts[p] = len(ids_fn(tok, p))
        out["date_formats"][label] = dmeans
        out["amount_formats"][label] = ameans
        out["paragraph_forms"][label] = pcounts
        out["segmentation"][label] = {ex: segment(tok, ex)[0] for ex in PRZYKZADY}
        out["digit_split"][label] = digit_style(tok)
    return out
