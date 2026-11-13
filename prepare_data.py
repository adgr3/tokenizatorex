"""
Przygotowanie danych z SlayerLab/hplt-v3-pl-cleaned.

  train.txt   — losowa próbka dokumentów z shardu bin8_5_p0 (domyślnie 300 MB)
  heldout.txt — losowa próbka z INNEGO shardu (bin8_6_p0), 10 MB — tekst, którego
                tokenizer nigdy nie widział w treningu

Czytamy przez polars (pyarrow.parquet bywa blokowany przez Smart App Control na Windows).

Użycie:
  python prepare_data.py --raw ../data/raw/data --out ../data
"""
import argparse
import os

import polars as pl


def sample(path: str, target_bytes: int, seed: int) -> list[str]:
    texts = pl.read_parquet(path, columns=["text"]).get_column("text")
    texts = texts.sample(fraction=1.0, shuffle=True, seed=seed).to_list()
    docs, total = [], 0
    for t in texts:
        if not t:
            continue
        docs.append(t)
        total += len(t.encode("utf-8"))
        if total >= target_bytes:
            break
    return docs


def write(docs: list[str], path: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for d in docs:
            f.write(d.replace("\r\n", "\n").strip())
            f.write("\n\n")
    print(f"{path}: {len(docs):,} dokumentów, {os.path.getsize(path) / 1e6:.1f} MB")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="../data/raw/data")
    ap.add_argument("--out", default="../data")
    ap.add_argument("--train-mb", type=int, default=300)
    ap.add_argument("--heldout-mb", type=int, default=10)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()

    tr = sample(os.path.join(a.raw, "european_hplt_v3_pl_bin8_5_p0.parquet"), a.train_mb * 10**6, a.seed)
    write(tr, os.path.join(a.out, "train.txt"))
    ho = sample(os.path.join(a.raw, "european_hplt_v3_pl_bin8_6_p0.parquet"), a.heldout_mb * 10**6, a.seed + 1)
    write(ho, os.path.join(a.out, "heldout.txt"))


if __name__ == "__main__":
    main()
