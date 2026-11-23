import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
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
}
SYNTHETIC_PHONE_FILES = {
    "tests/test_no_pii_tracked.py",
    "tkx_c/review_grok/attack2_synthetic.json",
    "tkx_c/review_codex/REVIEW_CODEX_R2.md",
}
ALLOW_EMAIL_FILES = {
    "tkx_v2/wzorce.json", "tkx_v2/gen_wzorce.py", "results/tkx_v2_patterns.json",
    "audit/notations.py", "audit/results/notations.json",
    "tkx_c/make_golden_dataset.py", "tkx_c/results/consistency.json",
    "tkx_c/review_codex/verify_consistency.json", "tkx_c/review_grok/attack2_synthetic.json",
    "tests/test_no_pii_tracked.py", "scripts/sprawdz_liczby_v2.py",
}


def tracked_files():
    out = subprocess.check_output(["git", "ls-files"], cwd=REPO, text=True)
    return [line.strip() for line in out.splitlines() if line.strip()]


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
        if rel in SYNTHETIC_PHONE_FILES:
            continue
        for rx in PHONE_RES:
            for m in rx.finditer(text):
                val = m.group(0)
                violations.append(f"{rel}: phone {val}")
    assert not violations, "PII found:\n" + "\n".join(violations)
