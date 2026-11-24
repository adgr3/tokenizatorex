import os
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
# Numer NIP: 10 cyfr, z separatorami lub bez; PESEL: 11 cyfr.
NIP_RE = re.compile(r"(?<!\d)\d{2}-\d{3}-\d{2}-\d{2}(?!\d)|(?<!\d)\d{10}(?!\d)")
PESEL_RE = re.compile(r"(?<!\d)\d{11}(?!\d)")
# Długie ciągi hex to hashe/SHA w danych, nie numery identyfikacyjne.
HEX_RUN = re.compile(r"[0-9a-fA-F]{16,}")
# Phone patterns (Polish/international-ish), conservative to avoid dates/IDs.
PHONE_RES = [
    re.compile(r"\b(?:\+48[\s-]?)?(?:\d{3}[\s-]\d{3}[\s-]\d{3})\b"),
    re.compile(r"\b(?:\+48[\s-]?)?(?:\d{2}[\s-]\d{3}[\s-]\d{2}[\s-]\d{2})\b"),
    re.compile(r"\(\d{2,3}\)\s*\d{2,3}[-\s]\d{2}[-\s]\d{2}"),
]

# Known synthetic exceptions (not real PII) - wzorce testowe / syntetyczne artefakty.
SYNTHETIC_EMAILS = {
    "user@example.com", "biuro@urzad.gov.pl", "kontakt@firma.pl", "info@grant.org.pl", "a@b.pl",
    "przyklad@example.org", "sekretariat@urzad.gov.pl", "22wog.zamowienia@ron.mil.pl",
    "CWK@platformazakupowa.pl", "FIO@niw.gov.pl",
    "kontakt@example.org", "biuro@firma.example", "oferty@urzad.example",
    "odbiorca@example.net", "zespol@example.org", "kontakt@example.edu",
}
R6_SYNTHETIC_REDTEAM = {
    "results/tkx_v2_r6_redteam_a_a1_targeted.json",
    "results/tkx_v2_r6_redteam_a_a2_regression.json",
    "results/tkx_v2_r6_redteam_a_a5_extremes.json",
    "tests/redteam_cases.py",
}
SYNTHETIC_PHONE_FILES = {
    "tests/test_no_pii_tracked.py",
    "tkx_c/review_grok/attack2_synthetic.json",
    "tkx_c/review_codex/REVIEW_CODEX_R2.md",
    "tkx_v21/PROTOKOL.md",
} | R6_SYNTHETIC_REDTEAM
ALLOW_EMAIL_FILES = {
    "tkx_v2/wzorce.json", "tkx_v2/gen_wzorce.py", "results/tkx_v2_patterns.json",
    "audit/notations.py", "audit/results/notations.json",
    "tkx_c/make_golden_dataset.py", "tkx_c/results/consistency.json",
    "tkx_c/review_codex/verify_consistency.json", "tkx_c/review_grok/attack2_synthetic.json",
    "tests/test_no_pii_tracked.py", "scripts/sprawdz_liczby_v2.py",
    "tkx_v21/generuj_json.py",
} | R6_SYNTHETIC_REDTEAM

# Ten plik zawiera celowo syntetyczne PESEL/NIP do testu sum kontrolnych.
# Pliki R6 to kopie wyników red teamu A z syntetycznymi NIP/PESEL/telefonami.
ALLOW_PII_FILES = {"tests/test_no_pii_tracked.py"} | R6_SYNTHETIC_REDTEAM

# NIP instytucji publicznych (nie osoby prywatne): świadome wyjątki z uzasadnieniem.
# wartość -> (plik, uzasadnienie)
INSTITUTION_NIPS = {
    "5220003055": (
        "tkx_c/golden/dataset.json",
        "Krajowy Numer Identyfikacyjny instytucji (zamawiającego) w ogłoszeniu BZP; "
        "nie numer osoby prywatnej",
    ),
}

# Syntetyczne NIP-y ze wzorców i danych testowych albo przypadkowa zgodność sumy
# w danych liczbowych — nie numery osób prywatnych. wartość -> uzasadnienie
SYNTHETIC_NIPS = {
    "0000000000": "wzorzec testowy NIP (same zera)",
    "0123456789": "wzorzec testowy w skryptach audytu",
    "1111111111": "wzorzec syntetyczny",
    "2222222222": "wzorzec syntetyczny",
    "5260250274": "wzorzec testowy NIP",
    "9876543210": "wzorzec testowy NIP",
    "5482362660": "syntetyczny przykład „NIP ...” w danych testowych",
    "5871707828": "syntetyczny przykład „NIP ...” w danych testowych",
}

# Brak PESEL-i w repo. Każdy przyszły wyjątek musi tu trafić z uzasadnieniem.
SYNTHETIC_PESELS: dict[str, tuple[str, str]] = {}


def _digits(value: str) -> str:
    return re.sub(r"\D", "", value)


def nip_checksum_ok(value: str) -> bool:
    n = _digits(value)
    if len(n) != 10 or not n.isdigit():
        return False
    weights = [6, 5, 7, 2, 3, 4, 5, 6, 7]
    return sum(int(n[i]) * weights[i] for i in range(9)) % 11 == int(n[9])


def pesel_checksum_ok(value: str) -> bool:
    n = _digits(value)
    if len(n) != 11 or not n.isdigit():
        return False
    weights = [1, 3, 7, 9, 1, 3, 7, 9, 1, 3]
    return (10 - sum(int(n[i]) * weights[i] for i in range(10)) % 10) % 10 == int(n[10])


def _in_hex(text: str, pos: int) -> bool:
    start = max(0, pos - 40)
    end = min(len(text), pos + 40)
    for m in HEX_RUN.finditer(text[start:end]):
        if m.start() <= pos - start <= m.end():
            return True
    return False


def tracked_files():
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    out = subprocess.check_output(["git", "ls-files"], cwd=REPO, text=True,
                                  encoding="utf-8", errors="replace", env=env)
    return [line.strip() for line in out.splitlines() if line.strip()]


def test_checksum_validators():
    # Wartości syntetyczne o poprawnej sumie kontrolnej (nie dane osób).
    assert pesel_checksum_ok("99999999994")       # poprawna suma, data niemożliwa
    assert not pesel_checksum_ok("99999999993")
    assert nip_checksum_ok("0000000000")
    assert not nip_checksum_ok("0000000001")


def test_no_pii_in_tracked_files():
    violations = []
    for rel in tracked_files():
        p = REPO / rel
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        for m in EMAIL_RE.finditer(text):
            val = m.group(0)
            if val in SYNTHETIC_EMAILS or rel in ALLOW_EMAIL_FILES:
                continue
            if val.endswith("@example.com") and rel.startswith("tests/"):
                continue
            violations.append(f"{rel}: email {val}")
        if rel not in SYNTHETIC_PHONE_FILES:
            for rx in PHONE_RES:
                for m in rx.finditer(text):
                    val = m.group(0)
                    violations.append(f"{rel}: phone {val}")
        if rel in ALLOW_PII_FILES:
            continue
        for m in NIP_RE.finditer(text):
            val = m.group(0)
            key = _digits(val)
            if key in SYNTHETIC_NIPS:
                continue
            exception = INSTITUTION_NIPS.get(key)
            if exception and exception[0] == rel:
                continue
            if _in_hex(text, m.start()):
                continue
            if nip_checksum_ok(val):
                violations.append(f"{rel}: NIP {val}")
        for m in PESEL_RE.finditer(text):
            val = m.group(0)
            exception = SYNTHETIC_PESELS.get(val)
            if exception and exception[0] == rel:
                continue
            if _in_hex(text, m.start()):
                continue
            if pesel_checksum_ok(val):
                violations.append(f"{rel}: PESEL {val}")
    assert not violations, "PII found:\n" + "\n".join(violations)
