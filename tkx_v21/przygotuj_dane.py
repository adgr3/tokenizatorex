"""Przygotowanie danych TKX-V21-JSON.

1. Odtworzenie `stability_train.txt` (HPLT p2, 400 MB) — dokładnie tak, jak
   zrobił to `audit/stability.py`; weryfikacja SHA-256.
2. Wyciągnięcie tekstów tur asystenta/narzędzia z `tc1/dane/train.jsonl`.
3. Wygenerowanie syntetycznego JSON-a (`generuj_json.py`).
4. Zbudowanie korpusów mieszanych V0J2/V0J5/V0J10: 300 MB HPLT + JSON
   wstawiony równomiernie, tak by JSON stanowił 2/5/10% bajtów całości.

Pełne teksty zostają poza gitem (`data/`), w repo tylko metadane i hash.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

HPLT_P2 = ("https://huggingface.co/datasets/SlayerLab/hplt-v3-pl-cleaned/resolve/main/"
           "data/european_hplt_v3_pl_bin8_5_p2.parquet")
STABILITY_SHA = "b0e7447cf94f8e0fa03edfeb3f6f10a2e63c9e32037f086cf5a434709ae6e558"
STABILITY_BYTES = 400_160_750
TC1_TRAIN = r"D:\VPS\fabryka\tc1\dane\train.jsonl"
SEED = 20261123


def sha256_file(path: str, buf: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(buf)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def prepare_stability(raw: str, out: str, target_bytes: int = 400_000_000) -> dict:
    """Odtwarza stability_train.txt (pierwsze 200k wierszy p2, strip, linia)."""
    if os.path.isfile(out) and os.path.getsize(out) == STABILITY_BYTES \
            and sha256_file(out) == STABILITY_SHA:
        return {"path": out, "bytes": STABILITY_BYTES, "sha256": STABILITY_SHA,
                "source": HPLT_P2, "reused": True}
    import polars as pl
    if not os.path.isfile(raw):
        raise FileNotFoundError(f"brak {raw} — pobierz: {HPLT_P2}")
    df = pl.scan_parquet(raw).select("text").head(200_000).collect()
    total = 0
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        for t in df["text"].to_list():
            t = (t or "").replace("\r\n", "\n").strip()
            if not t:
                continue
            f.write(t + "\n")
            total += len(t.encode("utf-8"))
            if total >= target_bytes:
                break
    return {"path": out, "bytes": os.path.getsize(out), "sha256": sha256_file(out),
            "source": HPLT_P2, "reused": False,
            "matches_expected": sha256_file(out) == STABILITY_SHA}


def extract_tc1_train(path: str, out: str) -> dict:
    docs = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            for m in obj.get("wiadomosci", []):
                role = m.get("rola")
                text = (m.get("tresc") or "").strip()
                if not text:
                    continue
                if role == "asystent" and "<tool_call>" in text:
                    docs.append(text)
                elif role == "narzedzie":
                    docs.append(text)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        for d in docs:
            f.write(d.replace("\r\n", "\n") + "\n\n")
    return {"path": out, "docs": len(docs), "bytes": os.path.getsize(out),
            "sha256": sha256_file(out), "source": path}


def _load_json_examples(path: str) -> list[str]:
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    return [x.strip() for x in raw.split("\n\n") if x.strip()]


def build_mixture(hplt: str, json_paths: list[str], out: str, fraction: float,
                  hplt_bytes: int = 300_000_000, chunks: int = 120,
                  seed: int = SEED) -> dict:
    """300 MB HPLT + JSON równomiernie; JSON = `fraction` bajtów całości."""
    target_json = int(hplt_bytes * fraction / (1.0 - fraction))
    examples: list[str] = []
    for p in json_paths:
        examples.extend(_load_json_examples(p))
    rng = random.Random(seed)
    rng.shuffle(examples)
    # wybierz przykłady do dokładnie ~target_json bajtów (całe przykłady)
    selected: list[str] = []
    selected_b = 0
    for ex in examples:
        ex_b = len(ex.encode("utf-8")) + 2
        if selected_b + ex_b > target_json:
            break
        selected.append(ex)
        selected_b += ex_b
    examples = selected
    chunk_target = max(1, target_json // chunks)
    blocks: list[list[str]] = []
    cur: list[str] = []
    cur_b = 0
    for ex in examples:
        ex_b = len(ex.encode("utf-8")) + 2
        cur.append(ex)
        cur_b += ex_b
        if cur_b >= chunk_target:
            blocks.append(cur)
            cur, cur_b = [], 0
    if cur:
        blocks.append(cur)
    if not blocks:
        raise ValueError("brak przykładów JSON")

    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    written_hplt = 0
    written_json = 0
    next_block = 0
    with open(hplt, encoding="utf-8") as src, \
            open(out, "w", encoding="utf-8", newline="\n") as dst:
        for line in src:
            dst.write(line)
            written_hplt += len(line.encode("utf-8"))
            checkpoint = int(hplt_bytes * (next_block + 1) / (chunks + 1))
            while next_block < len(blocks) and written_hplt >= checkpoint:
                for ex in blocks[next_block]:
                    dst.write(ex.replace("\r\n", "\n").strip() + "\n\n")
                    written_json += len(ex.encode("utf-8")) + 2
                next_block += 1
                checkpoint = int(hplt_bytes * (next_block + 1) / (chunks + 1))
            if written_hplt >= hplt_bytes:
                break
        while next_block < len(blocks):
            for ex in blocks[next_block]:
                dst.write(ex.replace("\r\n", "\n").strip() + "\n\n")
                written_json += len(ex.encode("utf-8")) + 2
            next_block += 1
    total = written_hplt + written_json
    return {"path": out, "hplt_bytes": written_hplt, "json_bytes": written_json,
            "bytes": os.path.getsize(out), "json_share_requested": fraction,
            "json_share_actual": written_json / total if total else None,
            "json_blocks": len(blocks), "sha256": sha256_file(out)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=os.path.join("data", "raw", "hplt_p2.parquet"))
    ap.add_argument("--data-dir", default=os.path.join("data"))
    ap.add_argument("--out", default=os.path.join("tkx_v21", "dane"))
    ap.add_argument("--train-examples", type=int, default=150000)
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    stab = prepare_stability(a.raw, os.path.join(a.data_dir, "stability_train.txt"))
    print("stability:", stab)

    tc1 = extract_tc1_train(TC1_TRAIN, os.path.join(a.out, "tc1_json_train.txt"))
    print("tc1 train:", tc1)

    from tkx_v21.generuj_json import generuj
    gen = generuj(a.out, a.train_examples)
    json_train_path = os.path.join(a.out, "json_train.txt")
    print("json_train:", os.path.getsize(json_train_path), "B")

    mixtures = {}
    for name, frac in (("V0J2-32k", 0.02), ("V0J5-32k", 0.05), ("V0J10-32k", 0.10)):
        m = build_mixture(os.path.join(a.data_dir, "stability_train.txt"),
                          [json_train_path, os.path.join(a.out, "tc1_json_train.txt")],
                          os.path.join(a.data_dir, "mixed", f"{name}.txt"), frac)
        mixtures[name] = m
        print(name, {k: m[k] for k in ("hplt_bytes", "json_bytes", "json_share_actual")})

    manifest = {
        "seed": SEED,
        "stability_train": stab,
        "tc1_json_train": tc1,
        "json_generic": {
            k: gen[k] for k in ("train_examples", "heldout_dev", "heldout_test",
                                "train_tools", "heldout_tools", "licencja")
        },
        "mixtures": mixtures,
        "note": "pełne teksty w data/ i tkx_v21/dane/ poza gitem; w repo metadane",
    }
    with open(os.path.join("tkx_v21", "MANIFEST_DANYCH.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print("zapisano", os.path.join("tkx_v21", "MANIFEST_DANYCH.json"))


if __name__ == "__main__":
    main()
