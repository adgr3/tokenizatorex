"""Diagnostyka roznic R2 vs R1 (po policzeniu wszystkich pieciu liczb).

Nie zmienia wynikow R2; odtwarza wybory rundy 1, zeby wyjasnic roznice.
"""
from __future__ import annotations

import collections
import json
import os
import re
import unicodedata

import numpy as np

import r2lib

R1_YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")

R1 = r2lib.RESULTS
N_DEFAULT = 25
SEED = 20261119


def load_domain_filename_order(domain: str) -> list[dict]:
    d = os.path.join(r2lib.RAW, domain)
    docs = []
    for name in sorted(os.listdir(d)):
        if not name.endswith(".json"):
            continue
        with open(os.path.join(d, name), encoding="utf-8") as f:
            doc = json.load(f)
        if doc.get("split") == "test":
            docs.append(doc)
    return docs


def diag_h5() -> None:
    print("\n=== H5: odtworzenie wyboru dokumentow rundy 1 (rng.choice 25) ===")
    toks = r2lib.get_tokenizers()
    r1 = json.load(open(os.path.join(R1, "robustness.json"), encoding="utf-8"))
    out = {}
    for dom in r2lib.OFFICIAL7:
        docs = load_domain_filename_order(dom)
        rng = np.random.default_rng(SEED)
        if len(docs) > N_DEFAULT:
            idx = rng.choice(len(docs), size=N_DEFAULT, replace=False)
            docs = [docs[i] for i in sorted(idx)]
        row = {"docs": len(docs), "words": sum(len(d["text"].split()) for d in docs),
               "ids": [d["id"] for d in docs], "tokenizers": {}}
        for label, tok in toks.items():
            base = sum(len(tok.encode(d["text"])) for d in docs)
            nfd = sum(len(tok.encode(unicodedata.normalize("NFD", d["text"]))) for d in docs)
            row["tokenizers"][label] = {"base": base, "nfd": nfd, "inc": nfd / base - 1}
        out[dom] = row
        r1v = r1["domains"][dom]
        print(f"{dom}: docs={row['docs']} words={row['words']} (R1 words={r1v['words']})")
        for label in toks:
            r1inc = r1v["variants"]["nfd"]["tokenizers"][label]["relative_increase"]
            print(f"  {label:18s} R2repl={row['tokenizers'][label]['inc']:+.6f}  R1={r1inc:+.6f}  diff={row['tokenizers'][label]['inc']-r1inc:+.2e}")

    print("\n--- moj wybor: pierwsze 25 po id ---")
    for dom in r2lib.OFFICIAL7:
        docs = r2lib.load_docs(dom)[:25]
        print(f"{dom}: words={sum(len(d['text'].split()) for d in docs)} ids0={docs[0]['id']}")
    print("\n--- wybor R1 vs moj: wspolne id ---")
    for dom in r2lib.OFFICIAL7:
        mine = {d["id"] for d in r2lib.load_docs(dom)[:25]}
        theirs = set(out[dom]["ids"])
        print(f"{dom}: wspolne={len(mine & theirs)}/25")


def diag_h1() -> None:
    print("\n=== H1: regex roku R2 vs R1 ===")
    r2re = re.compile(r"(?<!\d)(20(?:1[5-9]|2[0-6]))(?!\d)")
    r1re = R1_YEAR_RE
    for dom in ("przetargi_ogloszenia", "prawo_eli"):
        docs = r2lib.load_docs(dom)
        c2 = collections.Counter()
        c1 = collections.Counter()
        only2 = collections.Counter()
        only1 = collections.Counter()
        examples = []
        for d in docs:
            t = d["text"]
            s2 = collections.Counter(m.group(1) for m in r2re.finditer(t))
            s1 = collections.Counter(m.group(0) for m in r1re.finditer(t) if 2015 <= int(m.group(0)) <= 2026)
            c2.update(s2)
            c1.update(s1)
            if s2 != s1:
                for y in (s2 - s1):
                    only2[y] += (s2 - s1)[y]
                    for m in re.finditer(r"(?<!\d)" + y + r"(?!\d)", t):
                        a, b = max(0, m.start() - 25), min(len(t), m.end() + 25)
                        examples.append((y, t[a:b].replace("\n", "\\n")))
        print(dom, "R2", dict(sorted(c2.items())))
        print(dom, "R1", dict(sorted(c1.items())))
        print("  tylko R2:", dict(sorted(only2.items())), " tylko R1:", dict(sorted(only1.items())))
        for y, ex in examples[:8]:
            print(f"   {y}: ...{ex}...")


def diag_h6() -> None:
    print("\n=== H6: kryterium R1 vs R2 ===")
    ref = r2lib.RefTok()
    vocab = ref.tok.vocab
    texts = [b.decode("utf-8", errors="replace") for b in vocab]
    docs = r2lib.load_all_docs(sorted(os.listdir(r2lib.RAW)))
    freq = collections.Counter()
    for d in docs:
        freq.update(ref.encode(d["text"]))
    total = sum(freq.values())

    word_freq = collections.Counter()
    WORD = re.compile(r"[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż]+")
    for d in docs:
        for m in WORD.finditer(d["text"]):
            word_freq[m.group(0).lower()] += 1
    top_words = {w for w, _ in word_freq.most_common(2000)}
    all_words = set()
    for d in docs:
        all_words.update(d["text"].split())

    BOILER = ["Czytaj więcej", "Zobacz także", "Zobacz też", "Dowiedz się więcej",
              "Polityka prywatności", "cookies", "Strona główna", "Menu", "Szukaj",
              "Kliknij", "Pobierz", "Wróć", "Czytaj dalej", "Więcej", "Reklama",
              "Newsletter", "Zaloguj", "Kontakt"]
    super_ids = [i for i in range(len(vocab)) if ref.tok.is_superword(i)]

    def first_has_letter(first):
        return bool(re.search(r"[^\W\d_]", first))

    sets = {"R1": set(), "R1_no_lead": set(), "R2": set(), "R2_no_lead": set(),
            "leading_space_super": set()}
    for i in super_ids:
        s = texts[i].lstrip(" ")
        first = s.split(" ", 1)[0]
        if not first or not first_has_letter(first):
            continue
        leads = texts[i].startswith(" ")
        if leads:
            sets["leading_space_super"].add(i)
        boiler = any(b.lower() in s.lower() for b in BOILER)
        r1mid = (not boiler) and first.lower() not in top_words
        r2mid = first not in all_words
        if r1mid:
            sets["R1"].add(i)
            if not leads:
                sets["R1_no_lead"].add(i)
        if r2mid:
            sets["R2"].add(i)
            if not leads:
                sets["R2_no_lead"].add(i)
    for k, s in sets.items():
        if k == "leading_space_super":
            print(f"  superwordy z wiodaca spacja: {len(s)}/{len(super_ids)} = {len(s)/len(super_ids):.4f}")
            continue
        u = sum(freq.get(i, 0) for i in s)
        print(f"  {k:14s} dict={len(s):5d} share_super={len(s)/len(super_ids):.6f} "
              f"uses={u:6d} use_share_all={u/total:.6f} use_share_super={u/sum(freq.get(i,0) for i in super_ids):.6f}")
    # ile z midword R1 zaczyna sie od spacji
    r1 = sets["R1"]
    lead_r1 = sum(1 for i in r1 if texts[i].startswith(" "))
    print(f"  R1 midword z wiodaca spacja: {lead_r1}/{len(r1)} = {lead_r1/len(r1):.4f}")


def main() -> None:
    diag_h5()
    diag_h1()
    diag_h6()


if __name__ == "__main__":
    main()
