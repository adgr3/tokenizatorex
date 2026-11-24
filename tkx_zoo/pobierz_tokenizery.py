"""Odtwarza lokalne tkx_zoo/hf/ na podstawie tkx_zoo/MANIFEST.json.

Pliki nie są w repo (licencje / repozytoria gated) — pozostają na dysku po
`git rm --cached tkx_zoo/hf`. Skrypt pobiera wyłącznie pliki tokenizera
(tokenizer.json / tokenizer_config.json) z przypiętych rewizji i sprawdza
SHA-256 z MANIFEST.json. Token HF jest brany z lokalnego logowania i nigdy
nie jest wypisywany.

    python tkx_zoo/pobierz_tokenizery.py
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(REPO, "tkx_zoo", "MANIFEST.json")
PREFIX = "tkx_zoo/hf/"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_bytes(entry, fname):
    """Zwraca bajty pliku z przypiętej rewizji (HF albo PR na GitHubie)."""
    repo, rev = entry.get("repo"), entry.get("revision")
    if not repo or not rev:
        raise RuntimeError("brak repo lub rewizji w MANIFEST")
    if repo.startswith("https://github.com/"):
        source = next((f.get("source_path") for f in entry["files"]
                       if f["name"] == fname), None)
        if not source:
            raise RuntimeError("brak source_path dla pliku z PR")
        try:
            subprocess.run(["git", "fetch", repo, rev], cwd=REPO, check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            subprocess.run(["git", "fetch", repo, "pull/29/head"], cwd=REPO, check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        got = subprocess.check_output(["git", "rev-parse", "FETCH_HEAD"], cwd=REPO, text=True).strip()
        if got != rev:
            print(f"  UWAGA: FETCH_HEAD={got[:12]} ≠ manifest {rev[:12]} "
                  "(decyduje SHA-256 pliku)")
        return subprocess.check_output(["git", "show", f"FETCH_HEAD:{source}"], cwd=REPO)
    from huggingface_hub import get_token, hf_hub_download
    cached = hf_hub_download(repo_id=repo, filename=fname, revision=rev, token=get_token())
    with open(cached, "rb") as f:
        return f.read()


def main():
    with open(MANIFEST, encoding="utf-8") as f:
        manifest = json.load(f)
    ok = missing = bad = 0
    for label, entry in manifest.items():
        if not isinstance(entry, dict) or "files" not in entry:
            continue
        local = [f for f in entry["files"] if f.get("path", "").startswith(PREFIX)]
        if not local:
            continue
        for f in local:
            dest = os.path.join(REPO, f["path"].replace("/", os.sep))
            if os.path.isfile(dest):
                h = sha256(dest)
                if h == f["sha256"]:
                    print(f"OK       {label}: {f['name']} ({h[:12]})")
                    ok += 1
                else:
                    print(f"SHA-BAD  {label}: {f['name']} lokalny {h[:12]} "
                          f"≠ manifest {f['sha256'][:12]}")
                    bad += 1
                continue
            try:
                data = fetch_bytes(entry, f["name"])
            except Exception as e:  # noqa: BLE001
                print(f"BRAK     {label}: {f['name']} — {type(e).__name__}: "
                      f"{str(e).splitlines()[0][:100]}")
                missing += 1
                continue
            h = hashlib.sha256(data).hexdigest()
            if h != f["sha256"]:
                print(f"SHA-BAD  {label}: {f['name']} pobrany {h[:12]} "
                      f"≠ manifest {f['sha256'][:12]}")
                bad += 1
                continue
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as out:
                out.write(data)
            print(f"POBRANO  {label}: {f['name']} ({h[:12]})")
            ok += 1
    for label, entry in manifest.items():
        if isinstance(entry, dict) and entry.get("status") == "unavailable":
            print(f"POMINIETO {label}: {entry.get('note')}")
    print(f"podsumowanie: OK={ok} BRAK={missing} SHA-BAD={bad}")
    return 1 if (missing or bad) else 0


if __name__ == "__main__":
    sys.exit(main())
