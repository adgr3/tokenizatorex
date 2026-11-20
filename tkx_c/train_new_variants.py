"""Buduje tokenizery V2b i V3 (32k/24k/16k) na tej samej próbce co V0–V2.

Etap 1 (300 MB) -> baza 32k, potem etap 2 (100 MB) dla t=20k/15k/10k.
Wszystkie liczbyID idą do tkx_c/tmp/ (gitignored); finalize_variants.py
wkłada je do tokenizers/variants i hf/variants.
"""
from __future__ import annotations

import os
import sys
import time
from functools import partial

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)
from superbpe import SuperBPETokenizer  # noqa: E402
from train import _count_chunks, _count_pretokens, parallel_count  # noqa: E402

DATA = os.path.join(ROOT, "audit", "tmp", "stability_train.txt")
TMP = os.path.join(ROOT, "tkx_c", "tmp")
SPECIALS = ["<|endoftext|>"]
S1_BYTES = 300_000_000
S2_BYTES = 100_000_000

PLANS = {
    "V2b": ("space_first", [("V2b-32k", 32000, 20000),
                            ("V2b-24k", 24000, 15000),
                            ("V2b-16k", 16000, 10000)]),
    "V3": ("groups3", [("V3-32k", 32000, 20000),
                       ("V3-24k", 24000, 15000),
                       ("V3-16k", 16000, 10000)]),
}


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def build(prefix: str) -> None:
    mode, variants = PLANS[prefix]
    t0 = time.time()
    log(f"{prefix}: start (digits={mode}, normalize=nfc)")

    tok = SuperBPETokenizer(digits=mode, normalize="nfc")
    log(f"{prefix}: liczenie pretokenów etapu 1 ({S1_BYTES // 10**6} MB)")
    cnt1 = parallel_count(DATA, partial(_count_pretokens,
                                        word_pattern=tok.word_pattern,
                                        normalize=tok.normalize), S1_BYTES)
    log(f"{prefix}: pretokeny {len(cnt1):,} unikalnych, {sum(cnt1.values()):,} łącznie")
    tok.train_stage1(cnt1, 31999, log=log)
    tok.meta = {"kind": "baseline-bpe", "data": os.path.basename(DATA),
                "stage1_bytes": S1_BYTES, "digits": mode, "forced_merges": 2210 if mode == "groups3" else 10}
    tok.add_specials(SPECIALS)
    base_path = os.path.join(TMP, prefix + "-base-32k.json")
    tok.save(base_path)
    log(f"{prefix}: zapisano {base_path} vocab={tok.vocab_size} stage1={len(tok.stage1)} "
        f"({time.time()-t0:.0f}s)")

    for name, vocab, transition in variants:
        t1 = time.time()
        t = SuperBPETokenizer.load(base_path)
        t.specials = {}
        t.truncate_stage1(transition)
        log(f"{name}: liczenie fragmentów etapu 2 ({S2_BYTES // 10**6} MB), t={transition}")
        cnt2 = parallel_count(DATA, partial(_count_chunks, normalize=t.normalize), S2_BYTES)
        log(f"{name}: fragmenty {len(cnt2):,} unikalnych, {sum(cnt2.values()):,} łącznie")
        t.train_stage2(cnt2, vocab - 1, max_words=4, log=log)
        t.meta = {"kind": "superbpe", "data": os.path.basename(DATA),
                  "stage1_bytes": S1_BYTES, "stage2_bytes": S2_BYTES,
                  "from": os.path.basename(base_path), "digits": mode}
        t.add_specials(SPECIALS)
        out = os.path.join(TMP, name + ".json")
        t.save(out)
        log(f"{name}: zapisano vocab={t.vocab_size} t={t.transition} "
            f"stage2={len(t.stage2)} ({time.time()-t1:.0f}s)")
    log(f"{prefix}: GOTOWE ({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("prefix", choices=list(PLANS) + ["all"], nargs="?", default="all")
    a = ap.parse_args()
    for p in (PLANS if a.prefix == "all" else [a.prefix]):
        build(p)
