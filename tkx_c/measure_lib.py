"""Wspólne ładowanie wariantów TKX-C (kanoniczny HF) i korpusu testowego."""
from __future__ import annotations

import os
import sys

# H9: HF przed repo
from tokenizers import Tokenizer  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(ROOT, "audit"))
sys.path.append(ROOT)

from common import load_domain  # noqa: E402

VARIANTS = ["V0-32k", "V1-32k", "V2-32k", "V2-24k", "V2-16k",
            "V2-base-32k", "V2-base-24k", "V2-base-16k",
            "V2b-32k", "V2b-24k", "V2b-16k",
            "V3-32k", "V3-24k", "V3-16k"]
COMPARE4 = ["V0-32k", "V2-32k", "V2b-32k", "V3-32k"]
DOMAINS = ["przetargi_ogloszenia", "przetargi_kio", "samorzad_uchwaly",
           "granty_ogloszenia", "prawo_eli", "ocr_prasa", "tabele_json",
           "web", "wikipedia", "literatura", "prawo", "sejm", "nauka",
           "dyskusje", "angielski"]
OFFICIAL = DOMAINS[:7]


def load_hf(name: str) -> Tokenizer:
    return Tokenizer.from_file(os.path.join(ROOT, "hf", "variants", name, "tokenizer.json"))


def hf_encode(tok: Tokenizer, text: str) -> list[int]:
    return tok.encode(text, add_special_tokens=False).ids


def docs(domain: str):
    return load_domain(domain, "test")
