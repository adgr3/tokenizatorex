"""Runda 1.10 — stabilność: tymczasowy retrening na innym shardzie HPLT.

Etap 1: 300 MB, etap 2: 100 MB, te same ustawienia (t=20k, vocab=32k, max 4 słowa).
Tokenizer ląduje w `audit/tmp/` — NIE zastępuje plików w `tokenizers/`.

Wynik: audit/results/stability.json (albo UNKNOWN z powodem)
"""
from __future__ import annotations

import os
import sys
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common import (AUDIT_DIR, REPO_ROOT, RESULTS_DIR, load_domain, load_superbpe,
                    write_json)

HPLT_P2 = ("https://huggingface.co/datasets/SlayerLab/hplt-v3-pl-cleaned/resolve/main/"
           "data/european_hplt_v3_pl_bin8_5_p2.parquet")
TMP = os.path.join(AUDIT_DIR, "tmp")
DATA = os.path.join(TMP, "stability_train.txt")
OUT_TOK = os.path.join(TMP, "stability-tokenizer-32k.json")
SPECIALS = ["<|endoftext|>"]
DOMAINS = ["przetargi_ogloszenia", "przetargi_kio", "prawo_eli", "web"]


def prepare_data(target_bytes: int = 400_000_000) -> int:
    if os.path.exists(DATA) and os.path.getsize(DATA) >= target_bytes * 0.95:
        return os.path.getsize(DATA)
    import polars as pl
    os.makedirs(TMP, exist_ok=True)
    df = pl.scan_parquet(HPLT_P2).select("text").head(200_000).collect()
    total = 0
    with open(DATA, "w", encoding="utf-8", newline="\n") as f:
        for t in df["text"].to_list():
            t = (t or "").replace("\r\n", "\n").strip()
            if not t:
                continue
            f.write(t + "\n")
            total += len(t.encode("utf-8"))
            if total >= target_bytes:
                break
    return os.path.getsize(DATA)


def main() -> None:
    out = {"meta": {"shard": HPLT_P2, "stage1_mb": 300, "stage2_mb": 100,
                    "transition": 20000, "vocab": 32000, "max_words": 4,
                    "note": "trening tymczasowy w audit/tmp, nie zastępuje repo"},
           "status": "UNKNOWN", "reason": ""}
    t0 = time.time()
    try:
        size = prepare_data()
        out["train_bytes_available"] = size
        from superbpe import SuperBPETokenizer
        from train import _count_chunks, _count_pretokens, parallel_count

        t1 = time.time()
        cnt1 = parallel_count(DATA, _count_pretokens, 300_000_000)
        out["stage1_pretokens"] = {"unique": len(cnt1), "total": int(sum(cnt1.values())),
                                   "seconds": round(time.time() - t1, 1)}
        tok = SuperBPETokenizer()
        t2 = time.time()
        tok.train_stage1(cnt1, 20000, log=None)
        out["stage1_seconds"] = round(time.time() - t2, 1)
        del cnt1

        t3 = time.time()
        cnt2 = parallel_count(DATA, _count_chunks, 100_000_000)
        out["stage2_chunks"] = {"unique": len(cnt2), "total": int(sum(cnt2.values())),
                                "seconds": round(time.time() - t3, 1)}
        t4 = time.time()
        tok.train_stage2(cnt2, 32000, max_words=4, log=None)
        out["stage2_seconds"] = round(time.time() - t4, 1)
        tok.add_specials(SPECIALS)
        tok.save(OUT_TOK)
        out["tokenizer_file"] = os.path.relpath(OUT_TOK, REPO_ROOT)
        out["vocab"] = tok.vocab_size
        out["transition"] = tok.transition
        out["train_seconds"] = round(time.time() - t0, 1)

        # porównanie ze słownikiem referencyjnym
        ref = load_superbpe("tokenizers/tokenizatorex-32k.json")
        ref_set = {bytes(b) for b in ref.vocab}
        new_set = {bytes(b) for b in tok.vocab}
        out["vocab_coverage"] = {
            "common_tokens": len(ref_set & new_set),
            "share_of_reference": len(ref_set & new_set) / len(ref_set),
            "share_of_new": len(ref_set & new_set) / len(new_set),
        }
        stage1_ref = {bytes(b) for b in ref.vocab[:ref.transition]}
        stage1_new = {bytes(b) for b in tok.vocab[:tok.transition]}
        out["stage1_coverage"] = {
            "common_tokens": len(stage1_ref & stage1_new),
            "share_of_reference": len(stage1_ref & stage1_new) / len(stage1_ref),
        }
        # fertility na testach
        fert = {}
        import numpy as np
        for dom in DOMAINS:
            docs = load_domain(dom, "test")[:25]
            if not docs:
                continue
            words = sum(len(d["text"].split()) for d in docs)
            a = sum(len(ref.encode_ordinary(d["text"])) for d in docs)
            b = sum(len(tok.encode_ordinary(d["text"])) for d in docs)
            fert[dom] = {"documents": len(docs), "words": words,
                         "tokens_reference": a, "tokens_new": b,
                         "fertility_reference": a / words, "fertility_new": b / words,
                         "delta_pct": (b - a) / a}
        out["fertility"] = fert
        out["status"] = "OK"
    except Exception as ex:  # noqa: BLE001
        out["status"] = "UNKNOWN"
        out["reason"] = f"{type(ex).__name__}: {str(ex)[:500]}"
        out["seconds_elapsed"] = round(time.time() - t0, 1)
    write_json(os.path.join(RESULTS_DIR, "stability.json"), out)
    print("stability:", out["status"], out.get("reason", ""))
    if out["status"] == "OK":
        print(json_dumps(out["vocab_coverage"]))


def json_dumps(obj) -> str:
    import json
    return json.dumps(obj, ensure_ascii=False)


if __name__ == "__main__":
    main()
