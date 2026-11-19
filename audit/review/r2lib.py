"""Wspolne ladowanie danych i tokenizerow dla niezaleznej rundy 2 (Codex).

H9: importujemy pakiet HF `tokenizers` PRZED dopisaniem korzenia repo do sys.path,
a korzen dodajemy przez append (nie insert(0, ...)), zeby katalog `tokenizers/`
w repo nie przeslanial pakietu.
"""
from __future__ import annotations

import json
import os
import sys

import tokenizers  # noqa: F401  (H9: musi byc przed sys.path.append(repo))
from tokenizers import Tokenizer

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO not in sys.path:
    sys.path.append(REPO)

from superbpe import SuperBPETokenizer  # noqa: E402

AUDIT = os.path.join(REPO, "audit")
RAW = os.path.join(AUDIT, "data", "raw")
RESULTS = os.path.join(AUDIT, "results")

OFFICIAL7 = [
    "przetargi_ogloszenia",
    "przetargi_kio",
    "samorzad_uchwaly",
    "granty_ogloszenia",
    "prawo_eli",
    "ocr_prasa",
    "tabele_json",
]
OFFICIAL3 = ["przetargi_ogloszenia", "przetargi_kio", "granty_ogloszenia"]

REF_PATH = os.path.join(REPO, "tokenizers", "tokenizatorex-32k.json")
HF_PATH = os.path.join(REPO, "hf", "tokenizatorex-32k", "tokenizer.json")
SLAYER_PATH = os.path.join(AUDIT, "data", "tokenizer_files", "SlayerLab__Slayer1B-1.08.json")


def load_docs(domain: str, split: str = "test") -> list[dict]:
    d = os.path.join(RAW, domain)
    docs = []
    for name in os.listdir(d):
        if not name.endswith(".json"):
            continue
        with open(os.path.join(d, name), encoding="utf-8") as f:
            doc = json.load(f)
        if doc.get("split") == split and doc.get("domain") == domain:
            docs.append(doc)
    docs.sort(key=lambda x: x["id"])
    return docs


def load_all_docs(domains, split: str = "test") -> list[dict]:
    out = []
    for dom in domains:
        out.extend(load_docs(dom, split))
    return out


class RefTok:
    label = "TOKENIZATOREX"

    def __init__(self, path: str = REF_PATH) -> None:
        self.tok = SuperBPETokenizer.load(path)

    def encode(self, text: str) -> list[int]:
        return self.tok.encode_ordinary(text)


class HFTok:
    def __init__(self, label: str, path: str) -> None:
        self.label = label
        self.tok = Tokenizer.from_file(path)

    def encode(self, text: str) -> list[int]:
        return self.tok.encode(text, add_special_tokens=False).ids


def get_tokenizers() -> dict:
    return {
        "TOKENIZATOREX": RefTok(),
        "TOKENIZATOREX-HF": HFTok("TOKENIZATOREX-HF", HF_PATH),
        "Slayer1B": HFTok("Slayer1B", SLAYER_PATH),
    }


def n_tokens(tok, text: str) -> int:
    return len(tok.encode(text))


def write_json(name: str, obj) -> str:
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    return path
