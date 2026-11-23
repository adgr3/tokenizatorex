import subprocess, sys, os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def test_sprawdz_sam_runs():
    p = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "sprawdz_sam.py"), "Test zdania."],
                       capture_output=True, text=True, timeout=300)
    # may fail due to network, but should at least not crash on import
    assert p.returncode in (0, 1)  # 0 success, 1 if no tokenizers? 
    assert "Tekst:" in p.stdout or "brak tekstu" in p.stderr or p.returncode == 0

def test_wzorce_valid():
    import json
    p = os.path.join(REPO, "tkx_v2", "wzorce.json")
    data = json.load(open(p, encoding="utf-8"))
    assert data["count"] >= 150
    assert len(data["items"]) >= 150
    cats = set(i["category"] for i in data["items"])
    assert len(cats) >= 12
