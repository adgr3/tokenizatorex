"""Wzorce zapisów urzędowych używane przez `notations.py` i `consistency.py`."""
from __future__ import annotations

import re

PATTERNS = {
    "kwota": r"(?<![\d,])\d{1,3}(?:[ \u00a0]\d{3})*(?:,\d{1,2})?\s*(?:zł|PLN)\b",
    "data_slowna": (r"\b\d{1,2}\s+(?:stycznia|lutego|marca|kwietnia|maja|czerwca|lipca|"
                    r"sierpnia|września|października|listopada|grudnia)\s+\d{4}(?:\s*r\.)?"),
    "data_cyfrowa": r"\b\d{1,2}[./-]\d{1,2}[./-]\d{4}\b",
    "rok": r"(?<!\d)(?:19|20)\d{2}(?!\d)",
    "rok_z_r": r"(?<!\d)(?:19|20)\d{2}\s*r\.",
    "godzina": r"\b\d{1,2}[:.]\d{2}\b",
    "przepis": (r"\bart\.\s*\d+[a-z]?(?:\s*ust\.\s*\d+[a-z]?)?"
                r"(?:\s*pkt\s*\d+)?(?:\s*lit\.\s*[a-z])?"),
    "publikator": r"\b(?:Dz\.\s?U\.|M\.\s?P\.)",
    "poz": r"\bpoz\.\s*\d+\b",
    "cpv": r"\b\d{8}-\d\b",
    "znak_sprawy": r"\b[A-Z]{1,4}[./-]\d{1,4}(?:[./-]\d{1,4}){1,3}\b",
    "sygnatura_kio": r"\bKIO\s+\d+/\d{2}\b",
    "sygnatura_sadu": r"\b(?:II|III|IV|I|V|VI|VII|VIII|IX|X)\s+[A-Z]{2}(?:/[A-Z]{2,3})?\s+\d+/\d{2}\b",
    "uchwala": r"(?i)\buchwała\s+nr\s+[IVXLCDM]+/\d+/\d{2,4}\b",
    "procent": r"(?<![\d,])\d+(?:[.,]\d+)?\s?%",
    "kod_pocztowy": r"\b\d{2}-\d{3}\b",
    "email": r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b",
    "url": r"https?://[^\s<>\")\]]+",
    "nip": r"\bNIP[:\s]*\d{3}-?\d{3}-?\d{2}-?\d{2}\b",
}
COMPILED = {k: re.compile(v) for k, v in PATTERNS.items()}
ABBREVIATIONS = ["art.", "lit.", "Dz.U.", "M.P.", "poz."]
CODE_CATEGORIES = ["cpv", "znak_sprawy", "sygnatura_kio", "uchwala", "nip", "kod_pocztowy"]


def extract(text: str, category: str, limit: int = 20000) -> list[str]:
    return [m.group(0) for m in COMPILED[category].finditer(text)][:limit]


def extract_all(text: str, categories=None, limit_per_cat: int = 20000) -> dict[str, list[str]]:
    cats = categories or list(PATTERNS)
    return {c: extract(text, c, limit_per_cat) for c in cats}
