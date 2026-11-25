import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "wykresy.py"
PYTHON = sys.executable

EXPECTED_STATIC = [
    "fertility_bzp.png", "fertility_bzp.svg",
    "skad_przewaga.png", "skad_przewaga.svg",
    "osiem_zrodel.png", "osiem_zrodel.svg",
    "koszt_slownika.png", "koszt_slownika.svg",
    "daty_kwoty_paragraf.png", "daty_kwoty_paragraf.svg",
    "json_heldout.png", "json_heldout.svg",
    "znane_wady.png",
]


def _load_module():
    spec = importlib.util.spec_from_file_location("wykresy", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_wykresy_fast_generates_all():
    p = subprocess.run(
        [PYTHON, str(SCRIPT), "--szybko"],
        cwd=REPO, capture_output=True, text=True, encoding="utf-8",
        env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
    )
    assert p.returncode == 0, p.stdout + p.stderr
    out = REPO / "docs" / "wykresy"
    for name in EXPECTED_STATIC:
        assert (out / name).is_file(), name
    assert not (out / "anim").exists(), "animacje GIF usuniete decyzja wlasciciela"


def test_wykresy_numbers_match_json():
    w = _load_module()
    z = json.load(open(REPO / "results" / "tkx_zoo_fertility.json", encoding="utf-8"))
    src = z["sources"]["1_bzp"]["tokenizers"]
    rows = w.dane_fertility_bzp()
    v0 = next(r for r in rows if r["key"] == "V0-32k")
    assert abs(v0["fertility"] - src["V0-32k"]["fertility"]) < 1e-12

    j = w.dane_json_heldout()
    expected_delta = (j["heldout"]["V0J2"] - j["heldout"]["V0"]) / j["heldout"]["V0"] * 100
    h = json.load(open(REPO / "results" / "tkx_v21_heldout_forms.json", encoding="utf-8"))
    assert abs(expected_delta - h["overall"]["delta_pct"]) < 1e-9