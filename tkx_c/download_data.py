"""Pobiera shard HPLT p0 i tworzy train.txt dokładnie jak prepare_data.py (seed 42)."""
from __future__ import annotations

import os
import sys

from huggingface_hub import hf_hub_download

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(ROOT)
sys.path.append(REPO)
from prepare_data import sample, write  # noqa: E402

RAW = os.path.join(ROOT, "tmp", "hplt")
DATA = os.path.join(ROOT, "data")
os.makedirs(RAW, exist_ok=True)
os.makedirs(DATA, exist_ok=True)
NAME = "data/european_hplt_v3_pl_bin8_5_p0.parquet"
path = hf_hub_download("SlayerLab/hplt-v3-pl-cleaned", NAME, repo_type="dataset",
                       local_dir=RAW)
print("pobrano", path, os.path.getsize(path) / 1e9, "GB")
out = os.path.join(DATA, "train.txt")
if not (os.path.exists(out) and os.path.getsize(out) >= 300_000_000):
    docs = sample(path, 300 * 10**6, 42)
    write(docs, out)
print("train.txt", os.path.getsize(out) / 1e6, "MB")
