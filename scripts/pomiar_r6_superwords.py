"""R6: przelicz artefakty SuperBPE na bieżących wariantach V0-32k i V0J2-32k.

Ta sama definicja co `audit/superwords.py` (H6): superword zaczyna się w środku
słowa, gdy nie zaczyna się spacją, pierwszy segment przed spacją zawiera literę
i nie jest formą występującą w korpusie testowym >= 5 razy; boilerplate wyłączony.

Wynik: results/tkx_v2_r6_superwords.json
"""
from __future__ import annotations

import bisect
import json
import os
import re
import sys
from collections import Counter

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (REPO, os.path.join(REPO, "audit")):
    if p not in sys.path:
        sys.path.append(p)

from common import load_domain  # noqa: E402
from superbpe import SuperBPETokenizer  # noqa: E402

RESULTS = os.path.join(REPO, "results")
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
TOKENIZERS = {
    "V0-32k": os.path.join(REPO, "tokenizers", "variants", "V0-32k", "superbpe.json"),
    "V0J2-32k": os.path.join(REPO, "tokenizers", "variants", "V0J2-32k", "superbpe.json"),
}


def tok_text(tok: SuperBPETokenizer, tid: int) -> str:
    return tok.vocab[tid].decode("utf-8", errors="replace")


def analyse(name: str, path: str) -> dict:
    tok = SuperBPETokenizer.load(path)
    texts = [tok_text(tok, i) for i in range(len(tok.vocab))]

    freq: Counter[int] = Counter()
    doc_tokenized = []
    loaded_domains = []
    for dom in DOMAINS:
        docs = load_domain(dom, "test")
        if docs:
            loaded_domains.append(dom)
        for d in docs:
            ids = tok.encode_ordinary(d["text"])
            freq.update(ids)
            doc_tokenized.append((d, ids))
    total_uses = sum(freq.values())

    word_freq: Counter[str] = Counter()
    for d, _ids in doc_tokenized:
        for m in WORD_RE.finditer(d["text"]):
            word_freq[m.group(0).lower()] += 1
    lexicon = {w for w, c in word_freq.items() if c >= 5}

    super_ids = [i for i in range(len(tok.vocab)) if tok.is_superword(i)]
    midword, sensible, suspect = [], [], []
    for i in super_ids:
        raw = texts[i]
        if raw.startswith(" "):
            continue
        first = raw.split(" ", 1)[0]
        if not first or not re.search(r"[^\W\d_]", first):
            continue
        if any(b.lower() in raw.lower() for b in BOILERPLATE):
            continue
        if first.lower() in lexicon:
            continue
        midword.append(i)
        if any(raw.endswith(e) for e in SENSIBLE_ENDINGS):
            sensible.append(i)
        else:
            suspect.append(i)

    def use(ids) -> int:
        return sum(freq.get(i, 0) for i in ids)

    out = {
        "tokenizer": os.path.relpath(path, REPO).replace("\\", "/"),
        "vocab": len(tok.vocab),
        "corpus_uses": total_uses,
        "domains": loaded_domains,
        "domains_missing": [d for d in DOMAINS if d not in loaded_domains],
        "split": "test",
        "vocab_stats": {
            "superwords": len(super_ids),
            "superwords_share": len(super_ids) / len(tok.vocab),
            "midword_start": len(midword),
            "midword_share_of_superwords": len(midword) / len(super_ids) if super_ids else None,
            "sensible": len(sensible),
            "suspect": len(suspect),
            "suspect_share_of_superwords": len(suspect) / len(super_ids) if super_ids else None,
            "suspect_examples": [texts[i] for i in suspect[:12]],
        },
        "usage": {
            "superword_uses_share": use(super_ids) / total_uses if total_uses else None,
            "midword_uses_share": use(midword) / total_uses if total_uses else None,
            "sensible_uses_share": use(sensible) / total_uses if total_uses else None,
            "suspect_uses_share": use(suspect) / total_uses if total_uses else None,
        },
    }
    return out


def main() -> None:
    os.makedirs(RESULTS, exist_ok=True)
    out = {
        "meta": {
            "script": "scripts/pomiar_r6_superwords.py",
            "definition": "audit/superwords.py H6: token nie zaczyna się spacją; pierwszy "
                          "segment przed spacją zawiera literę i nie jest formą występującą "
                          "w korpusie testowym >= 5 razy; boilerplate wyłączony",
            "note": "Liczby na bieżących wariantach V0-32k i V0J2-32k (nie na starym TKX-A).",
        },
        "tokenizers": {},
    }
    for name, path in TOKENIZERS.items():
        print("liczę", name, flush=True)
        out["tokenizers"][name] = analyse(name, path)
        v = out["tokenizers"][name]["vocab_stats"]
        u = out["tokenizers"][name]["usage"]
        print(f"  superwords {v['superwords']} ({v['superwords_share']:.3%}), "
              f"midword {v['midword_start']} ({v['midword_share_of_superwords']:.3%}), "
              f"użycie midword {u['midword_uses_share']:.4%}", flush=True)
    with open(os.path.join(RESULTS, "tkx_v2_r6_superwords.json"), "w",
              encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("zapisano results/tkx_v2_r6_superwords.json")


if __name__ == "__main__":
    main()
