"""Test: raporty w repo muszą być dokładnie wynikiem generatora.

Uruchamiany w CI bez danych zewnętrznych; generator czyta tylko results/*.json.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "generuj_raporty_v2", REPO / "scripts" / "generuj_raporty_v2.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_generator_check_clean():
    p = subprocess.run([sys.executable, str(REPO / "scripts" / "generuj_raporty_v2.py"),
                        "--check"], cwd=REPO, capture_output=True, text=True, encoding="utf-8")
    assert p.returncode == 0, p.stdout + p.stderr
    assert "STATUS=OK" in p.stdout


def test_generator_check_detects_injected_number():
    g = _load_generator()
    files = g.build_all()
    key = "tkx_v2/RAPORT_PROSTY_V2.md"
    assert "8,12" in files[key]
    files[key] = files[key].replace("8,12", "7,83", 1)
    assert g.check(files) == 1
