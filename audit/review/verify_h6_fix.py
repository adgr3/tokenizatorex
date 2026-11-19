"""Niezalezna weryfikacja poprawki H6 (petla 2).

Liczy od zera: superwordy, kryterium strict_lex5 (forma <5 w TEST), any_lex1,
loose_top2000, wylaczenie wiodacej spacji i boilerplate. Porownuje z
audit/results/superwords.json. Nie modyfikuje niczego poza audit/review/.
"""
from __future__ import annotations

import collections
import json
import os
import re

import r2lib

WORD_RE = re.compile(r"[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż]+")
LETTER_RE = re.compile(r"[^\W\d_]")
BOILERPLATE = ["Czytaj więcej", "Zobacz także", "Zobacz też", "Dowiedz się więcej",
               "Polityka prywatności", "cookies", "Strona główna", "Menu",
               "Szukaj", "Kliknij", "Pobierz", "Wróć", "Czytaj dalej",
               "Więcej", "Reklama", "Newsletter", "Zaloguj", "Kontakt"]


def main() -> None:
    r1 = json.load(open(os.path.join(r2lib.RESULTS, "superwords.json"), encoding="utf-8"))
    ref = r2lib.RefTok()
    vocab = ref.tok.vocab
    docs = r2lib.load_all_docs(sorted(os.listdir(r2lib.RAW)))

    freq = collections.Counter()
    word_freq = collections.Counter()
    for d in docs:
        freq.update(ref.encode(d["text"]))
        for m in WORD_RE.finditer(d["text"]):
            word_freq[m.group(0).lower()] += 1
    total = sum(freq.values())
    lexicon = {w for w, c in word_freq.items() if c >= 5}
    all_forms = set(word_freq)
    top_words = {w for w, _ in word_freq.most_common(2000)}

    super_ids = [i for i in range(len(vocab)) if ref.tok.is_superword(i)]
    sets = {"strict_lex5": [], "any_lex1": [], "loose_top2000": []}
    leading_in_strict = 0
    for i in super_ids:
        raw = vocab[i].decode("utf-8", errors="replace")
        if raw.startswith(" "):
            continue
        s = raw.lstrip(" ")
        first = s.split(" ", 1)[0]
        if not (first and LETTER_RE.search(first)):
            continue
        if any(b.lower() in s.lower() for b in BOILERPLATE):
            continue
        if first.lower() not in lexicon:
            sets["strict_lex5"].append(i)
            if raw.startswith(" "):
                leading_in_strict += 1
        if first.lower() not in all_forms:
            sets["any_lex1"].append(i)
        if first.lower() not in top_words:
            sets["loose_top2000"].append(i)

    def usage(ids):
        return sum(freq.get(i, 0) for i in ids)

    print("docs", len(docs), "total_uses", total, "unique_forms", len(all_forms),
          "lex5", len(lexicon), "superwords", len(super_ids))
    print("leading-space in strict:", leading_in_strict)
    for name, ids in sets.items():
        calc = {"count": len(ids),
                "share": len(ids) / len(super_ids),
                "usage": usage(ids) / total}
        j = r1["vocab_sensitivity"][name]
        print(f"{name:14s} R2calc count={calc['count']:4d} share={calc['share']:.9f} usage={calc['usage']:.9f}")
        print(f"{'':14s} JSON   count={j['count']:4d} share={j['share_of_superwords']:.9f} usage={j['usage_share']:.9f}")
        print(f"{'':14s} diff   count={calc['count']-j['count']} share={calc['share']-j['share_of_superwords']:+.2e} usage={calc['usage']-j['usage_share']:+.2e}")

    primary = sets["strict_lex5"]
    dshare = len(primary) / len(super_ids)
    ushare = usage(primary) / total
    if dshare >= 0.10 and ushare >= 0.05:
        status = "potwierdzona"
    elif dshare < 0.05 or ushare < 0.01:
        status = "obalona"
    else:
        status = "niejasna"
    print(f"primary dshare={dshare:.9f} ushare={ushare:.9f} status={status}")
    print("JSON h6", r1["h6"])
    print("top strict examples:",
          [vocab[i].decode("utf-8", errors="replace") for i in primary[:15]])


if __name__ == "__main__":
    main()
