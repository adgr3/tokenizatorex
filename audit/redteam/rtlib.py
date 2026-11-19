"""Round-3 red team: shared loading utilities.

H9 trap handled explicitly: the Hugging Face ``tokenizers`` package is imported
BEFORE the repository root is appended to ``sys.path``; the repository root is
never inserted at position 0.  Bytecode writing is disabled so that importing
``superbpe`` does not touch files outside ``audit/redteam``.
"""
from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import json
import os
import re

import regex  # Unicode regex module required by the task definition

import tokenizers  # noqa: F401,E402  (H9: must come before sys.path.append(repo))
from tokenizers import Tokenizer  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIT = os.path.dirname(HERE)
REPO = os.path.dirname(AUDIT)
if REPO not in sys.path:
    sys.path.append(REPO)  # append, never insert(0) -- H9

from superbpe import SuperBPETokenizer  # noqa: E402

RAW = os.path.join(AUDIT, "data", "raw")
TOKFILES = os.path.join(AUDIT, "data", "tokenizer_files")

OFFICIAL7 = [
    "przetargi_ogloszenia",
    "przetargi_kio",
    "samorzad_uchwaly",
    "granty_ogloszenia",
    "prawo_eli",
    "ocr_prasa",
    "tabele_json",
]
EXTRA3 = ["web", "wikipedia", "nauka"]
ALL10 = OFFICIAL7 + EXTRA3

LABELS = ["TOKENIZATOREX", "TOKENIZATOREX-HF", "Slayer1B", "Pollock-2.0", "APT3-1B"]

PATHS = {
    "TOKENIZATOREX-HF": os.path.join(REPO, "hf", "tokenizatorex-32k", "tokenizer.json"),
    "Slayer1B": os.path.join(TOKFILES, "SlayerLab__Slayer1B-1.08.json"),
    "Pollock-2.0": os.path.join(TOKFILES, "SlayerLab__pollock-2.0-polishdynaword-150m.json"),
    "APT3-1B": os.path.join(TOKFILES, "Azurro__APT3-1B-Base.json"),
}


def load_docs(domain: str, split: str = "test") -> list[dict]:
    d = os.path.join(RAW, domain)
    docs = []
    for name in sorted(os.listdir(d)):
        if not name.endswith(".json"):
            continue
        with open(os.path.join(d, name), encoding="utf-8") as f:
            doc = json.load(f)
        if doc.get("split") == split and doc.get("domain") == domain:
            docs.append(doc)
    docs.sort(key=lambda x: x["id"])
    return docs


def load_domain_docs(domains, split: str = "test") -> dict[str, list[dict]]:
    return {dom: load_docs(dom, split) for dom in domains}


class RefTok:
    label = "TOKENIZATOREX"

    def __init__(self) -> None:
        self.tok = SuperBPETokenizer.load(
            os.path.join(REPO, "tokenizers", "tokenizatorex-32k.json")
        )

    def encode(self, text: str) -> list[int]:
        return self.tok.encode_ordinary(text)


class HFTok:
    def __init__(self, label: str, path: str) -> None:
        self.label = label
        self.tok = Tokenizer.from_file(path)

    def encode(self, text: str) -> list[int]:
        return self.tok.encode(text, add_special_tokens=False).ids


def get_tokenizers(labels: list[str] | None = None) -> dict:
    labels = labels or LABELS
    out = {}
    for label in labels:
        if label == "TOKENIZATOREX":
            out[label] = RefTok()
        else:
            out[label] = HFTok(label, PATHS[label])
    return out


def n_tokens(tok, text: str) -> int:
    return len(tok.encode(text))


def write_json(name: str, obj) -> str:
    path = os.path.join(HERE, name)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return path


def pct(x: float, digits: int = 3) -> str:
    return f"{100.0 * x:.{digits}f}%"


WORD_RE = regex.compile(r"[^\W\d_]+", regex.UNICODE)


def words_split(text: str) -> int:
    return len(text.split())


def words_letters(text: str) -> int:
    return len(WORD_RE.findall(text))


def utf8_bytes(text: str) -> int:
    return len(text.encode("utf-8"))
