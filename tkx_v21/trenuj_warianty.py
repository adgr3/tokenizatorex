"""Trening wariantów V0J2/V0J5/V0J10 i V0J5S (ten sam przepis co V0).

Użycie:
  python tkx_v21/trenuj_warianty.py [--skip-existing]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO not in sys.path:
    sys.path.insert(0, REPO)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

SPECIALS = ["<|system|>", "<|uzytkownik|>", "<|asystent|>", "<|narzedzie|>",
            "<tool_call>", "</tool_call>"]
VARIANTS = ["V0J2-32k", "V0J5-32k", "V0J10-32k"]
TMP = os.path.join(REPO, "tkx_v21", "tmp")
LOGS = os.path.join(REPO, "tkx_v21", "logs")
RESULTS = os.path.join(REPO, "results")


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def log_seconds(path):
    """Ostatnia liczba `... 123s` z logu treningu (albo None)."""
    if not os.path.isfile(path):
        return None
    text = open(path, encoding="utf-8", errors="replace").read()
    nums = re.findall(r"(\d+)s\b", text)
    return int(nums[-1]) if nums else None


def run(cmd, log_path):
    print("+", " ".join(cmd))
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = "0"
    env.setdefault("TKX_WORKERS", "8")
    with open(log_path, "w", encoding="utf-8") as log:
        p = subprocess.run(cmd, cwd=REPO, env=env, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                           errors="replace")
        log.write(p.stdout)
    if p.returncode != 0:
        raise RuntimeError(f"kod {p.returncode}; log: {log_path}\n{p.stdout[-3000:]}")
    print(p.stdout[-1200:])


def train_and_export(name, skip_existing=True):
    data = os.path.join(REPO, "data", "mixed", f"{name}.txt")
    base = os.path.join(TMP, f"{name}-base.json")
    out = os.path.join(REPO, "tokenizers", "variants", name, "superbpe.json")
    hf = os.path.join(REPO, "hf", "variants", name, "tokenizer.json")
    if skip_existing and os.path.isfile(out) and os.path.isfile(hf):
        print(f"# {name}: istnieje, pomijam trening")
        return
    if skip_existing and os.path.isfile(out):
        print(f"# {name}: tokenizer istnieje, tylko eksport HF")
        run([sys.executable, "export_hf.py", out, "--out-dir", os.path.join("hf", "variants"),
             "--name", name], os.path.join(LOGS, f"export_{name}.log"))
        return
    run([sys.executable, "train.py", "baseline", "--data", data, "--vocab", "32000",
         "--digits", "grouped", "--normalize", "none", "--out", base],
        os.path.join(LOGS, f"train_{name}_base.log"))
    run([sys.executable, "train.py", "superbpe", "--data", data, "--from", base,
         "--transition", "20000", "--vocab", "32000", "--stage2-mb", "100",
         "--max-words", "4", "--digits", "grouped", "--normalize", "none",
         "--out", out], os.path.join(LOGS, f"train_{name}.log"))
    run([sys.executable, "export_hf.py", out, "--out-dir", os.path.join("hf", "variants"),
         "--name", name], os.path.join(LOGS, f"export_{name}.log"))


def make_special_variant():
    from superbpe import SuperBPETokenizer
    src = os.path.join(REPO, "tokenizers", "variants", "V0J5-32k", "superbpe.json")
    out = os.path.join(REPO, "tokenizers", "variants", "V0J5S-32k", "superbpe.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    tok = SuperBPETokenizer.load(src)
    existing = {bytes(b): i for i, b in enumerate(tok.vocab)}
    next_id = len(tok.vocab)
    reused = []
    for name in SPECIALS:
        if name in tok.specials:
            continue
        b = name.encode("utf-8")
        if b in existing:                     # np. <tool_call> już jest zwykłym tokenem
            tok.specials[name] = existing[b]
            reused.append(name)
        else:
            while next_id in tok.specials.values():
                next_id += 1
            tok.specials[name] = next_id
            next_id += 1
    tok._rebuild()
    unique = len(tok.vocab) + len(set(tok.specials) - set(reused))
    tok.meta = {**tok.meta, "variant": "V0J5S-32k",
                "special_tokens": SPECIALS,
                "reused_existing_tokens": reused,
                "vocab_size_unique": unique,
                "note": "V0J5 + 6 atomowych tokenow specjalnych; <tool_call> i </tool_call> "
                        "to istniejące tokeny slownika, reszta ma nowe ID"}
    tok.save(out)
    run([sys.executable, "export_hf.py", out, "--out-dir", os.path.join("hf", "variants"),
         "--name", "V0J5S-32k"], os.path.join(LOGS, "export_V0J5S-32k.log"))
    print(f"# V0J5S: {out}; nowe ID: {next_id - len(tok.vocab)}; "
          f"użyte istniejące: {reused}; unikalne tokeny: {unique}")


def export_v0r():
    src = os.path.join(REPO, "tkx_v21", "warianty", "V0R-32k.json")
    hf = os.path.join(REPO, "tkx_v21", "hf", "V0R-32k", "tokenizer.json")
    if not os.path.isfile(src):
        print("# brak V0R-32k.json — pomijam eksport V0R")
        return
    if os.path.isfile(hf):
        print("# V0R: eksport istnieje")
        return
    run([sys.executable, "export_hf.py", src, "--out-dir", os.path.join("tkx_v21", "hf"),
         "--name", "V0R-32k"], os.path.join(LOGS, "export_V0R-32k.log"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-existing", action="store_true", default=True)
    a = ap.parse_args()
    os.makedirs(TMP, exist_ok=True)
    os.makedirs(LOGS, exist_ok=True)
    os.makedirs(RESULTS, exist_ok=True)
    export_v0r()
    manifest = {}
    for name in VARIANTS:
        t0 = time.time()
        train_and_export(name, a.skip_existing)
        out = os.path.join(REPO, "tokenizers", "variants", name, "superbpe.json")
        hf = os.path.join(REPO, "hf", "variants", name, "tokenizer.json")
        base_s = log_seconds(os.path.join(LOGS, f"train_{name}_base.log"))
        stage_s = log_seconds(os.path.join(LOGS, f"train_{name}.log"))
        manifest[name] = {"superbpe": os.path.relpath(out, REPO),
                          "hf": os.path.relpath(hf, REPO),
                          "sha256_superbpe": sha(out), "sha256_hf": sha(hf),
                          "train_data": f"data/mixed/{name}.txt",
                          "train_data_sha256": sha(os.path.join(REPO, "data", "mixed",
                                                                f"{name}.txt")),
                          "train_seconds": (base_s + stage_s)
                          if base_s is not None and stage_s is not None else None}
    make_special_variant()
    out = os.path.join(REPO, "tokenizers", "variants", "V0J5S-32k", "superbpe.json")
    hf = os.path.join(REPO, "hf", "variants", "V0J5S-32k", "tokenizer.json")
    manifest["V0J5S-32k"] = {"superbpe": os.path.relpath(out, REPO),
                             "hf": os.path.relpath(hf, REPO),
                             "sha256_superbpe": sha(out), "sha256_hf": sha(hf),
                             "train_data": "data/mixed/V0J5-32k.txt",
                             "special_tokens": SPECIALS,
                             "vocab_size_unique": 32004}
    data_manifest = json.load(open(os.path.join(REPO, "tkx_v21", "MANIFEST_DANYCH.json"),
                                   encoding="utf-8"))
    manifest["_data"] = {
        "stability_sha256": data_manifest["stability_train"]["sha256"],
        "stability_bytes": data_manifest["stability_train"]["bytes"],
        "mixtures": data_manifest["mixtures"],
        "recipe": "train.py baseline --vocab 32000 (stage1 300MB) -> superbpe "
                  "--transition 20000 --vocab 32000 --stage2-mb 100 --max-words 4",
        "seed": 20261123,
    }
    with open(os.path.join(RESULTS, "tkx_v21_variants.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("zapisano results/tkx_v21_variants.json")


if __name__ == "__main__":
    main()
