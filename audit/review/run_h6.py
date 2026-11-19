"""R2 #4: H6 superwordy "od srodka slowa".

DEFINICJA (jawna):
  * superword = token, ktorego bajty po usunieciu wiodacych spacji zawieraja
    spacje (dokladnie `is_superword` z superbpe.py: b" " in vocab[t].lstrip(b" ")).
  * "zaczyna sie w srodku slowa" = pierwszy segment tokenu (bajty po usunieciu
    wiodacych spacji, do pierwszej spacji) zawiera co najmniej jedna literę
    Unicode (regex \\p{L}) ORAZ nie jest samodzielnym slowem wystepujacym
    w korpusie TEST (zbior = wszystkie unikalne elementy text.split() ze
    wszystkich dokumentow TEST; bez zmiany wielkosci liter).
  * share_slownik = podejrzane superwordy / wszystkie superwordy.
  * share_uzycie = suma czestosci podejrzanych tokenow / wszystkie wystapienia
    tokenow w TEST (raportujemy tez udzial w wystapieniach superwordow).
Korpus TEST = wszystkie dziedziny (15) albo oficjalne 7 (raportujemy oba).
"""
from __future__ import annotations

import collections
import json
import os

import regex as re
import tokenizers as _hf_pkg  # noqa: F401  (H9)
from tokenizers import Tokenizer

import r2lib

LETTER_RE = re.compile(r"\p{L}")


def main() -> None:
    ref = r2lib.RefTok()
    vocab = ref.tok.vocab
    print("vocab size", len(vocab), "specials", ref.tok.specials, "transition", ref.tok.transition)

    all_domains = sorted(
        d for d in os.listdir(r2lib.RAW) if os.path.isdir(os.path.join(r2lib.RAW, d))
    )
    word_set: set[str] = set()
    docs_by_domain: dict[str, list[dict]] = {}
    for dom in all_domains:
        docs = r2lib.load_docs(dom)
        docs_by_domain[dom] = docs
        for d in docs:
            word_set.update(d["text"].split())
    print("test docs", sum(len(v) for v in docs_by_domain.values()), "unique split-words", len(word_set))

    is_super = [False] * len(vocab)
    first_seg: list[bytes | None] = [None] * len(vocab)
    suspicious = [False] * len(vocab)
    for tid, b in enumerate(vocab):
        stripped = b.lstrip(b" ")
        if b" " not in stripped:
            continue
        is_super[tid] = True
        seg = stripped.split(b" ", 1)[0]
        first_seg[tid] = seg
        text = seg.decode("utf-8", errors="replace")
        suspicious[tid] = bool(LETTER_RE.search(text)) and text not in word_set

    n_super = sum(is_super)
    n_susp = sum(1 for t in range(len(vocab)) if is_super[t] and suspicious[t])
    print(f"superwords={n_super} suspicious={n_susp} dict_share={n_susp/n_super:.6f}")

    freq = collections.Counter()
    freq7 = collections.Counter()
    freq_dom: dict[str, collections.Counter] = {}
    for dom, docs in docs_by_domain.items():
        c: collections.Counter = collections.Counter()
        for d in docs:
            c.update(ref.encode(d["text"]))
        freq_dom[dom] = c
        freq.update(c)
        if dom in r2lib.OFFICIAL7:
            freq7.update(c)

    def stats(f: collections.Counter) -> dict:
        total = sum(f.values())
        sup = sum(v for t, v in f.items() if t < len(vocab) and is_super[t])
        susp = sum(v for t, v in f.items() if t < len(vocab) and suspicious[t])
        return {
            "total_token_occurrences": total,
            "superword_occurrences": sup,
            "suspicious_occurrences": susp,
            "share_of_all_occurrences": susp / total,
            "share_of_superword_occurrences": susp / sup if sup else None,
        }

    out = {
        "definition": {
            "superword": "b' ' in vocab[t].lstrip(b' ')",
            "starts_mid_word": "first segment (before first space, leading spaces stripped) "
            "contains a Unicode letter and is not a standalone text.split() word in the TEST corpus",
            "dict_share": "suspicious superwords / all superwords",
            "usage_share": "freq(suspicious) / all token occurrences",
        },
        "vocab_bytes": len(vocab),
        "n_superwords": n_super,
        "n_suspicious_superwords": n_susp,
        "dict_share": n_susp / n_super,
        "unique_split_words_test": len(word_set),
        "usage_all_test": stats(freq),
        "usage_official7": stats(freq7),
        "per_domain_suspicious_occurrences": {
            dom: sum(v for t, v in f.items() if t < len(vocab) and suspicious[t])
            for dom, f in freq_dom.items()
        },
    }
    top = [(t, v, vocab[t]) for t, v in freq.most_common() if t < len(vocab) and suspicious[t]][:20]
    out["top20_suspicious"] = [
        {"id": t, "freq": v, "token": b.decode("utf-8", errors="replace")} for t, v, b in top
    ]
    for name in ("usage_all_test", "usage_official7"):
        s = out[name]
        print(name, {k: (round(v, 6) if isinstance(v, float) else v) for k, v in s.items()})
    print("top20:")
    for t, v, b in top:
        print(f"  {v:6d}  {b!r}")
    path = r2lib.write_json("r2_h6_superwords.json", out)
    print("WROTE", path)


if __name__ == "__main__":
    main()
