"""sprawdz_liczby_v2.py — bramka spójności liczb w raportach z results/*.json.

Zasady:
- Liczby w raportach muszą pochodzić z results/*.json (z tolerancją zaokrąglenia).
- Liczba nieobecna w danych i poza wyjątkami w pliku konfiguracyjnym => exit 1.
- Ostrzeżenia też kończą się błędem.
"""
from __future__ import annotations

import json
import math
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "results"
EXC_PATH = REPO / "scripts" / "sprawdz_liczby_v2_exceptions.json"
DEFAULT_REPORTS = [
    "RELEASE_NOTES_v2.0.md",
    "tkx_v2/RAPORT_TEST_DOMENOWY.md",
    "tkx_v2/RAPORT_PROSTY_V2.md",
    "tkx_v2/ZNANE_WADY.md",
    "tkx_v2/KARTA_WYMAGAN.md",
    "tkx_v2/KORPUS_DOMENOWY.md",
    "tkx_v21/RAPORT.md",
    "tkx_v21/RAPORT_PROSTY.md",
]


def load_json_numbers():
    vals = set()
    raw = []
    for p in sorted(RESULTS.glob("*.json")):
        try:
            obj = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        collect(obj, raw)
    # also include formatted forms
    for n in raw:
        add_number_forms(vals, n)
    return vals, raw


def collect(obj, out):
    if isinstance(obj, (int, float)) and not isinstance(obj, bool):
        if math.isfinite(float(obj)):
            out.append(float(obj))
    elif isinstance(obj, dict):
        for v in obj.values():
            collect(v, out)
    elif isinstance(obj, list):
        for v in obj:
            collect(v, out)


def add_number_forms(vals: set[str], n: float):
    # canonical
    if abs(n - round(n)) < 1e-9:
        i = int(round(n))
        vals.add(str(i))
        # polish thousands
        s = f"{i:,}".replace(",", " ")
        vals.add(s)
    else:
        # add common decimal representations
        for dp in range(0, 7):
            s = f"{n:.{dp}f}"
            vals.add(s)
            vals.add(s.replace(".", ","))
            # trim trailing zeros
            t = s.rstrip("0").rstrip(".")
            vals.add(t)
            vals.add(t.replace(".", ","))
    # percent-like base values may appear; keep raw string
    vals.add(str(n))


def load_exceptions():
    if not EXC_PATH.exists():
        return {"allowed_numbers": [], "allowed_context_patterns": []}
    return json.load(open(EXC_PATH, encoding="utf-8"))


def is_allowed(num_str: str, context: str, exc: dict) -> bool:
    norm = num_str.strip()
    norm_simple = norm.replace(" ", "").replace("\u00a0", "")
    for a in list(exc.get("allowed_numbers", [])) + list(exc.get("generated_derived_numbers", [])):
        if norm == str(a) or norm_simple == str(a).replace(" ", ""):
            return True
    # year-like 4 digits in dates/ranges often allowed by context patterns
    for pat in exc.get("allowed_context_patterns", []):
        try:
            if re.search(pat, context):
                # only allow if the number itself appears in that matched context? be conservative:
                # allow when the specific number is inside match
                m = re.search(pat, context)
                if m and norm_simple in m.group(0).replace(" ", ""):
                    return True
        except re.error:
            if pat in context and norm_simple in pat.replace(" ", ""):
                return True
    return False


NUM_RE = re.compile(
    r"(?<![A-Za-z0-9_./-])"  # not part of identifier/path
    r"([+-]?\d{1,3}(?:[ \u00a0]\d{3})+(?:[.,]\d+)?%?"  # 1 010 000 or 1 234,56
    r"|[+-]?\d+(?:[.,]\d+)?%?)"
    r"(?![A-Za-z0-9_/-])"
)


def normalize_number(s: str):
    t = s.strip().replace("\u00a0", " ").replace("%", "")
    # thousands spaces
    if re.fullmatch(r"[+-]?\d{1,3}(?: \d{3})+(?:[.,]\d+)?", t):
        t = t.replace(" ", "")
    # polish decimal comma
    if re.fullmatch(r"[+-]?\d+,\d+", t):
        t = t.replace(",", ".")
    # mixed like 1.234,56 not expected; ignore
    try:
        return float(t)
    except Exception:
        return None


def number_in_data(num_str: str, data_vals: set[str], data_raw: list[float]) -> bool:
    n = normalize_number(num_str)
    norm = num_str.strip().replace("\u00a0", " ")
    if norm in data_vals or norm.replace(" ", "") in data_vals or norm.replace(".", ",") in data_vals or norm.replace(",", ".") in data_vals:
        return True
    if n is None:
        return False
    # integer exact
    if abs(n - round(n)) < 1e-9 and str(int(round(n))) in data_vals:
        return True
    # tolerance by displayed precision
    decimals = 0
    m = re.search(r"[.,](\d+)", num_str.replace("%", ""))
    if m:
        decimals = len(m.group(1))
    tol = 0.5 * (10 ** (-decimals)) + 1e-9
    for v in data_raw:
        if abs(v - n) <= tol:
            return True
        # percent: allow if value is percent form or fraction
        if abs(v * 100 - n) <= tol or abs(v - n / 100.0) <= 1e-9:
            return True
    return False


def scan_file(path: Path, data_vals, data_raw, exc):
    text = path.read_text(encoding="utf-8")
    errors = []
    warnings = []
    for i, line in enumerate(text.splitlines(), 1):
        # Liczby w kodzie inline (np. tokeny `202|6|-01|-02`) nie są twierdzeniami
        # raportowymi; maskujemy je, żeby nie robić fałszywych błędów.
        line = re.sub(r"`[^`]*`", lambda m: " " * len(m.group(0)), line)
        for m in NUM_RE.finditer(line):
            num_str = m.group(0)
            # ignore obvious version-like in identifiers handled poorly? keep general
            ctx_start = max(0, m.start() - 40)
            ctx_end = min(len(line), m.end() + 40)
            context = line[ctx_start:ctx_end]
            # skip hex-like 0x...
            if "0x" in context.lower() and re.fullmatch(r"[0-9A-Fa-f]+", num_str):
                continue
            if is_allowed(num_str, context, exc):
                continue
            if not number_in_data(num_str, data_vals, data_raw):
                try:
                    rel = path.relative_to(REPO)
                except Exception:
                    rel = path
                errors.append(f"{rel}:{i}: liczba {num_str!r} nieznaleziona w results/*.json (kontekst: {context.strip()!r})")
    return errors, warnings


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    reports = [REPO / a for a in args] if args else [REPO / r for r in DEFAULT_REPORTS]
    # Post jest lokalny i nie wchodzi do repo. Sprawdzamy go, jeśli istnieje;
    # w CI (brak pliku) pomijamy z jasnym komunikatem.
    post = REPO / "DISCORD_TKX_V2.md"
    if not args:
        if post.exists():
            reports.append(post)
        else:
            print("INFO: pomijam DISCORD_TKX_V2.md (brak pliku lokalnego; w CI to normalne)")
    data_vals, data_raw = load_json_numbers()
    exc = load_exceptions()

    missing_files = [str(p.relative_to(REPO)) for p in reports if not p.exists()]
    all_errors = []
    all_warnings = []
    for mf in missing_files:
        all_errors.append(f"BRAK_PLIKU: {mf}")
    for p in reports:
        if not p.exists():
            continue
        e, w = scan_file(p, data_vals, data_raw, exc)
        all_errors.extend(e)
        all_warnings.extend(w)

    for w in all_warnings:
        print(f"WARN: {w}")
    for e in all_errors:
        print(f"ERR: {e}")
    if all_warnings:
        print(f"STATUS=BLOKER: {len(all_warnings)} ostrzeżeń")
        return 1
    if all_errors:
        print(f"STATUS=BLOKER: {len(all_errors)} błędów")
        return 1
    print("STATUS=OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
