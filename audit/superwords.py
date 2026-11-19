"""Runda 1.6 — artefakty SuperBPE (H6, H7).

* superwordy zaczynające się w środku słowa (w słowniku i ważone użyciem),
* podział na sensowne (końcówka + się/by/że) i podejrzane,
* boilerplate sieciowy w słowniku i jego użycie,
* rozbijanie częstych słów (top 2000) w kontekście,
* 100 najdziwniejszych tokenów do ręcznego przeglądu.

Wynik: audit/results/superwords.json, audit/results/dziwne_tokeny.md
"""
from __future__ import annotations

import bisect
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common import RESULTS_DIR, REPO_ROOT, load_domain, load_superbpe, write_json

DOMAINS = ["przetargi_ogloszenia", "przetargi_kio", "samorzad_uchwaly",
           "granty_ogloszenia", "prawo_eli", "ocr_prasa", "tabele_json",
           "web", "wikipedia", "literatura", "prawo", "sejm", "nauka",
           "dyskusje", "angielski"]
SENSIBLE_ENDINGS = (" się", " by", " że", " nie", " to", " w", " z", " i", " na",
                    " do", " od", " po", " za", " pod", " nad", " jak", " czy")
BOILERPLATE = ["Czytaj więcej", "Zobacz także", "Zobacz też", "Dowiedz się więcej",
               "Polityka prywatności", "cookies", "Strona główna", "Menu",
               "Szukaj", "Kliknij", "Pobierz", "Wróć", "Czytaj dalej",
               "Więcej", "Reklama", "Newsletter", "Zaloguj", "Kontakt"]
WORD_RE = re.compile(r"[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż]+")


def tok_text(tok, tid: int) -> str:
    return tok.vocab[tid].decode("utf-8", errors="replace")


def main() -> None:
    tok = load_superbpe("tokenizers/tokenizatorex-32k.json")
    vocab = tok.vocab
    texts = [tok_text(tok, i) for i in range(len(vocab))]

    # częstości użycia na korpusie (test)
    freq = Counter()
    doc_tokenized = []
    for dom in DOMAINS:
        for d in load_domain(dom, "test"):
            ids = tok.encode_ordinary(d["text"])
            freq.update(ids)
            doc_tokenized.append((d, ids))
    total_uses = sum(freq.values())

    # top 2000 słów korpusu
    word_freq = Counter()
    for d, _ids in doc_tokenized:
        for m in WORD_RE.finditer(d["text"]):
            word_freq[m.group(0).lower()] += 1
    top_words = {w for w, _ in word_freq.most_common(2000)}
    lexicon = {w for w, c in word_freq.items() if c >= 5}
    all_forms = set(word_freq)

    super_ids = [i for i in range(len(vocab)) if tok.is_superword(i)]
    sensible, suspect, midword = [], [], []
    mid_sets = {"strict_lex5": [], "any_lex1": [], "loose_top2000": []}
    for i in super_ids:
        raw = texts[i]
        starts_with_space = raw.startswith(" ")
        s = raw.lstrip(" ")
        first = s.split(" ", 1)[0]
        has_letter = bool(re.search(r"[^\W\d_]", first))
        is_boiler = any(b.lower() in s.lower() for b in BOILERPLATE)
        base = (not starts_with_space and bool(first) and has_letter and not is_boiler)
        if not base:
            continue
        if first.lower() not in lexicon:
            mid_sets["strict_lex5"].append(i)
        if first.lower() not in all_forms:
            mid_sets["any_lex1"].append(i)
        if first.lower() not in top_words:
            mid_sets["loose_top2000"].append(i)
        # kryterium główne (zapisane w protokole): strict_lex5
        is_mid = first.lower() not in lexicon
        if is_mid:
            midword.append(i)
            if any(texts[i].endswith(e) for e in SENSIBLE_ENDINGS):
                sensible.append(i)
            else:
                suspect.append(i)

    def use(ids):
        return sum(freq.get(i, 0) for i in ids)

    sw_uses = use(super_ids)
    mid_uses = use(midword)
    sensible_uses = use(sensible)
    suspect_uses = use(suspect)

    # boilerplate
    boiler_ids = {}
    for pat in BOILERPLATE:
        for i in super_ids:
            if pat.lower() in texts[i].lower():
                boiler_ids.setdefault(pat, []).append(i)
    boiler_all = {i for ids in boiler_ids.values() for i in ids}
    boiler_uses = use(boiler_all)

    # rozbijanie top 2000 w kontekście
    frag = {"occurrences": 0, "split_any": 0, "split_superword": 0}
    examples = []
    for d, ids in doc_tokenized:
        text = d["text"]
        starts, pos, pieces = [], 0, []
        for i in ids:
            p = tok_text(tok, i)
            pieces.append((pos, pos + len(p), i))
            starts.append(pos)
            pos += len(p)
        for m in WORD_RE.finditer(text):
            w = m.group(0)
            if len(w) < 3 or w.lower() not in top_words:
                continue
            a, b = m.start(), m.end()
            i0 = bisect.bisect_right(starts, a) - 1
            if i0 < 0:
                continue
            # tokeny pokrywające zakres
            j = i0
            covering = []
            while j < len(pieces) and pieces[j][0] < b:
                if pieces[j][1] > a:
                    covering.append(pieces[j])
                j += 1
            frag["occurrences"] += 1
            if len(covering) > 1:
                frag["split_any"] += 1
                if any(tok.is_superword(p[2]) for p in covering):
                    frag["split_superword"] += 1
                    if len(examples) < 8:
                        examples.append({"word": w, "domain": d["domain"],
                                         "tokens": [tok_text(tok, p[2]) for p in covering]})

    # 100 dziwnych tokenów
    def weird_score(i: int) -> float:
        s = texts[i]
        f = freq.get(i, 0)
        rare = 0 if f == 0 else (1 if f < 5 else 2 if f < 50 else 3)
        digits = sum(c.isdigit() for c in s)
        punct = sum(not c.isalnum() and not c.isspace() for c in s)
        mixed_case = int(any(c.islower() for c in s) and any(c.isupper() for c in s))
        nonascii = sum(ord(c) > 127 for c in s)
        return (4 - rare) * 5 + min(digits, 5) + min(punct, 5) + mixed_case * 3 + \
            (5 if tok.is_superword(i) else 0) + min(len(s), 30) / 10 + nonascii / 10

    weird = sorted(range(len(vocab)), key=weird_score, reverse=True)[:100]
    weird_rows = [{"id": i, "token": texts[i], "repr": repr(texts[i]),
                   "freq": freq.get(i, 0), "superword": tok.is_superword(i),
                   "chars": "".join(f"U+{ord(c):04X} " for c in texts[i])[:120]}
                  for i in weird]

    out = {"meta": {"tokenizer": "tokenizers/tokenizatorex-32k.json",
                    "vocab": len(vocab), "corpus_uses": total_uses,
                    "domains": DOMAINS, "split": "test",
                    "top_words": len(top_words),
                    "midword_criterion": "token nie zaczyna się spacją; pierwszy "
                                         "segment przed spacją zawiera literę i nie jest "
                                         "formą występującą w korpusie testowym ≥ 5 razy "
                                         "(słownik frekwencyjny); boilerplate wyłączony"},
           "vocab": {
               "superwords": len(super_ids),
               "superwords_share": len(super_ids) / len(vocab),
               "midword_start": len(midword),
               "midword_share_of_superwords": len(midword) / len(super_ids) if super_ids else None,
               "sensible": len(sensible),
               "suspect": len(suspect),
               "suspect_share_of_superwords": len(suspect) / len(super_ids) if super_ids else None,
               "suspect_examples": [texts[i] for i in suspect[:40]],
           },
           "vocab_sensitivity": {
               k: {"count": len(v), "share_of_superwords": len(v) / len(super_ids) if super_ids else None,
                   "usage_share": use(v) / total_uses if total_uses else None}
               for k, v in mid_sets.items()
           },
           "usage": {
               "superword_uses_share": sw_uses / total_uses if total_uses else None,
               "midword_uses_share": mid_uses / total_uses if total_uses else None,
               "sensible_uses_share": sensible_uses / total_uses if total_uses else None,
               "suspect_uses_share": suspect_uses / total_uses if total_uses else None,
               "boilerplate_tokens": len(boiler_all),
               "boilerplate_uses_share": boiler_uses / total_uses if total_uses else None,
               "boilerplate_by_phrase": {k: {"tokens": [texts[i] for i in v],
                                             "uses": use(v)} for k, v in boiler_ids.items()},
           },
           "fragmentation": {
               **frag,
               "split_any_share": frag["split_any"] / frag["occurrences"] if frag["occurrences"] else None,
               "split_superword_share": frag["split_superword"] / frag["occurrences"] if frag["occurrences"] else None,
               "examples": examples,
           },
           "weird_tokens": weird_rows,
           "h6": None, "h7": None}

    dshare = out["vocab"]["midword_share_of_superwords"] or 0
    ushare = out["usage"]["midword_uses_share"] or 0
    if dshare >= 0.10 and ushare >= 0.05:
        status = "potwierdzona"
    elif dshare < 0.05 or ushare < 0.01:
        status = "obalona"           # próg obalenia z protokołu
    else:
        status = "niejasna"
    out["h6"] = {
        "confirmed": status == "potwierdzona",
        "status": status,
        "midword_share_of_superwords": dshare,
        "midword_uses_share": ushare,
    }
    out["h7"] = {
        "top1000_with_own_token": _top_words_own_token(tok, word_freq, 1000),
        "split_superword_share": out["fragmentation"]["split_superword_share"],
        "confirmed": (_top_words_own_token(tok, word_freq, 1000) >= 0.90 and
                      (out["fragmentation"]["split_superword_share"] or 0) >= 0.01),
    }

    write_json(os.path.join(RESULTS_DIR, "superwords.json"), out)
    write_weird(out)
    write_md(out)
    print("superwords", out["vocab"]["superwords"], "mid", out["vocab"]["midword_start"],
          f"{out['vocab']['midword_share_of_superwords']:.1%}",
          "uses", f"{out['usage']['midword_uses_share']:.2%}")
    print("H6", out["h6"]["confirmed"], "H7", out["h7"])


def _top_words_own_token(tok, word_freq: Counter, k: int) -> float:
    hits = 0
    words = [w for w, _ in word_freq.most_common(k)]
    for w in words:
        if tok._cache1.get(w) is not None and len(tok._cache1[w]) == 1:
            hits += 1
            continue
        ids = tok._encode_pretoken(" " + w)
        if len(ids) == 1:
            hits += 1
    return hits / len(words) if words else 0.0


def write_weird(out: dict) -> None:
    lines = ["# 100 najdziwniejszych tokenów TOKENIZATOREX", "",
             "Kryterium: rzadkie użycie, cyfry/interpunkcja, mieszana wielkość liter, "
             "superword, długość. Do ręcznego przeglądu — nie jest to ranking jakości.", "",
             "| # | id | token (repr) | użyć | superword | znaki |", "|---:|---:|---|---:|---:|---|"]
    for n, r in enumerate(out["weird_tokens"], 1):
        rep = r["repr"].replace("|", "\\|")
        lines.append(f"| {n} | {r['id']} | `{rep}` | {r['freq']} | "
                     f"{'tak' if r['superword'] else 'nie'} | `{r['chars']}` |")
    path = os.path.join(RESULTS_DIR, "dziwne_tokeny.md")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def write_md(out: dict) -> None:
    v, u, fr = out["vocab"], out["usage"], out["fragmentation"]
    lines = ["# Artefakty SuperBPE", "",
             f"* superwordów w słowniku: **{v['superwords']}** ({v['superwords_share']:.1%} słownika)",
             f"* zaczyna się w środku słowa: **{v['midword_start']}** "
             f"({v['midword_share_of_superwords']:.1%} superwordów)",
             f"* podejrzanych: {v['suspect']} ({v['suspect_share_of_superwords']:.1%} superwordów)",
             f"* użycie superwordów w korpusie: {u['superword_uses_share']:.1%} tokenów; "
             f"od środka słowa: {u['midword_uses_share']:.2%}; podejrzanych: {u['suspect_uses_share']:.2%}",
             f"* boilerplate: {u['boilerplate_tokens']} tokenów, {u['boilerplate_uses_share']:.2%} użyć",
             f"* top 2000 słów rozbite (jakikolwiek podział): "
             f"{fr['split_any_share']:.2%}; z superwordem: {fr['split_superword_share']:.2%}", "",
             "## Przykłady superwordów od środka słowa", ""]
    lines += [f"* `{x}`" for x in v["suspect_examples"][:25]]
    lines += ["", "## Przykłady rozbitych częstych słów", ""]
    for e in fr["examples"]:
        lines.append(f"* `{e['word']}` → " + "·".join(t.replace(" ", "·") for t in e["tokens"]) +
                     f" ({e['domain']})")
    lines += ["", "## Werdykt", "",
              f"* H6: {out['h6'].get('status', 'niejasna').upper()} "
              f"(słownik: {out['h6']['midword_share_of_superwords']:.1%}, "
              f"użycie: {out['h6']['midword_uses_share']:.2%})",
              f"* H7: {'POTWIERDZONA' if out['h7']['confirmed'] else 'OBALONA'} "
              f"(top 1000 z własnym tokenem: {out['h7']['top1000_with_own_token']:.1%})"]
    path = os.path.join(RESULTS_DIR, "superwords.md")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
