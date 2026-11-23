"""Aktualizuje MANIFEST_DANYCH.json o SHA danych JSON (Poprawka 1).

  python tkx_v21/manifest_r2.py
"""
from __future__ import annotations

import hashlib
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "tkx_v21", "dane")
P = os.path.join(REPO, "tkx_v21", "MANIFEST_DANYCH.json")


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    m = json.load(open(P, encoding="utf-8"))
    m["json_train_sha256"] = sha(os.path.join(DATA, "json_train.txt"))
    m["json_generic"]["dev_sha256"] = sha(os.path.join(DATA, "json_generic_heldout_dev.jsonl"))
    m["json_generic"]["test_sha256"] = sha(os.path.join(DATA, "json_generic_heldout_test.jsonl"))
    m["json_generic"]["heldout_change"] = {
        "when": "2026-11-23 15:23",
        "why": "pierwsza wersja miala 98/100 dokumentow >50% pokrycia 13-gramow; "
               "dodano osobne slownictwo held-out",
        "training_data_unchanged": True,
        "json_train_sha256": m["json_train_sha256"],
        "variants_retrained": False,
    }
    with open(P, "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(m["json_train_sha256"])
    print(m["json_generic"]["dev_sha256"], m["json_generic"]["test_sha256"])


if __name__ == "__main__":
    main()
