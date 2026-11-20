"""POPRAWKA TKX-C-FIX: ponowny trening wyłącznie V3-32k.

Ta sama próbka p2 (pierwsze 300 MB etap 1 + 100 MB etap 2), ten sam seed,
ta sama procedura co w `train_new_variants.py`. Zmienia się tylko reguła
izolowania grup cyfr (regex z lookahead) i aliasy scalen, które wymuszają
jeden token na grupę niezależnie od kolejności par BPE.

V3-24k i V3-16k NIE są tu ruszane (odrzucone przed TKX-D).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from functools import partial

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)
from export_hf import to_hf  # noqa: E402
from superbpe import SuperBPETokenizer  # noqa: E402
from train import _count_chunks, _count_pretokens, parallel_count  # noqa: E402

DATA = os.path.join(ROOT, "audit", "tmp", "stability_train.txt")
TMP = os.path.join(ROOT, "tkx_c", "tmp")
SPECIALS = ["<|endoftext|>"]
S1_BYTES = 300_000_000
S2_BYTES = 100_000_000
BASE = os.path.join(TMP, "V3-base-32k-fixed.json")
OUT_PY = os.path.join(ROOT, "tokenizers", "variants", "V3-32k", "superbpe.json")
OUT_HF = os.path.join(ROOT, "hf", "variants", "V3-32k", "tokenizer.json")
MANIFEST = os.path.join(ROOT, "tkx_c", "results", "variant_manifest.json")


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def sha(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main() -> None:
    os.makedirs(TMP, exist_ok=True)
    os.environ.setdefault("TKX_WORKERS", "8")
    t0 = time.time()
    tok = SuperBPETokenizer(digits="groups3", normalize="nfc")
    log("etap 1: liczenie pretokenów (300 MB)")
    cnt1 = parallel_count(DATA, partial(_count_pretokens,
                                         word_pattern=tok.word_pattern,
                                         normalize=tok.normalize), S1_BYTES)
    log(f"etap 1: {len(cnt1):,} unikalnych pretokenów")
    tok.train_stage1(cnt1, 31999, log=log)
    tok.meta = {"kind": "baseline-bpe", "data": os.path.basename(DATA),
                "stage1_bytes": S1_BYTES, "digits": "groups3",
                "forced_merges": 2210, "alias_merges": len(tok.alias_merges),
                "fix": "groups-from-right in encode+HF; alias merges"}
    tok.add_specials(SPECIALS)
    tok.save(BASE)
    log(f"zapisano bazę: stage1={len(tok.stage1)} aliasy={len(tok.alias_merges)}")

    t = SuperBPETokenizer.load(BASE)
    t.specials = {}
    t.truncate_stage1(20000)
    log("etap 2: liczenie fragmentów (100 MB)")
    cnt2 = parallel_count(DATA, partial(_count_chunks, normalize=t.normalize), S2_BYTES)
    log(f"etap 2: {len(cnt2):,} unikalnych fragmentów")
    t.train_stage2(cnt2, 31999, max_words=4, log=log)
    t.meta["kind"] = "superbpe"
    t.meta["stage2_bytes"] = S2_BYTES
    t.add_specials(SPECIALS)

    os.makedirs(os.path.dirname(OUT_PY), exist_ok=True)
    os.makedirs(os.path.dirname(OUT_HF), exist_ok=True)
    t.save(OUT_PY)
    to_hf(t).save(OUT_HF)
    log(f"V3-32k: vocab={t.vocab_size} stage1={len(t.stage1)} "
        f"aliasy={len(t.alias_merges)} stage2={len(t.stage2)} "
        f"({time.time()-t0:.0f}s)")

    m = json.load(open(MANIFEST, encoding="utf-8"))
    e = m["V3-32k"]
    e["sha256_superbpe"] = sha(OUT_PY)
    e["sha256_hf"] = sha(OUT_HF)
    e["stage1_merges"] = len(t.stage1)
    e["stage2_merges"] = len(t.stage2)
    e["alias_merges"] = len(t.alias_merges)
    e["fix"] = "WAZNE-1: grupy od prawej w kodowaniu i eksporcie HF + aliasy scalen"
    with open(MANIFEST, "w", encoding="utf-8", newline="\n") as f:
        json.dump(m, f, indent=2, ensure_ascii=False)
        f.write("\n")
    log("zaktualizowano variant_manifest.json")


if __name__ == "__main__":
    main()
