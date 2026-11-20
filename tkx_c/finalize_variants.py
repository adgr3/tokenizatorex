"""Finalizuje warianty TKX-C: katalogi, eksport HF, manifest."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)
from export_hf import to_hf  # noqa: E402
from superbpe import SuperBPETokenizer  # noqa: E402

TMP = os.path.join(ROOT, "tkx_c", "tmp")
VAR = os.path.join(ROOT, "tokenizers", "variants")
HFV = os.path.join(ROOT, "hf", "variants")
SPECIALS = ["<|endoftext|>"]

SOURCES = {
    "V0-32k": os.path.join(TMP, "V0-32k.json"),
    "V1-32k": os.path.join(TMP, "V1-32k.json"),
    "V2-32k": os.path.join(TMP, "V2-32k.json"),
    "V2-24k": os.path.join(TMP, "V2-24k.json"),
    "V2-16k": os.path.join(TMP, "V2-16k.json"),
    "V2-base-32k": os.path.join(TMP, "V2-base-32k.json"),
    "V2b-32k": os.path.join(TMP, "V2b-32k.json"),
    "V2b-24k": os.path.join(TMP, "V2b-24k.json"),
    "V2b-16k": os.path.join(TMP, "V2b-16k.json"),
    "V3-32k": os.path.join(TMP, "V3-32k.json"),
    "V3-24k": os.path.join(TMP, "V3-24k.json"),
    "V3-16k": os.path.join(TMP, "V3-16k.json"),
}


def sha(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main() -> None:
    os.makedirs(VAR, exist_ok=True)
    os.makedirs(HFV, exist_ok=True)
    manifest = {}
    data_source = "audit/tmp/stability_train.txt (HPLT p2, 400 MB; V0 retrained train.py on same sample)"
    # V2-base truncations
    base = SuperBPETokenizer.load(SOURCES["V2-base-32k"])
    for name, target in (("V2-base-24k", 24000), ("V2-base-16k", 16000)):
        tok = SuperBPETokenizer.load(SOURCES["V2-base-32k"])
        tok.specials = {}
        tok.truncate_stage1(target - len(SPECIALS))
        tok.add_specials(SPECIALS)
        out = os.path.join(TMP, name + ".json")
        tok.save(out)
        SOURCES[name] = out

    for name, src in SOURCES.items():
        tok = SuperBPETokenizer.load(src)
        outdir = os.path.join(VAR, name)
        os.makedirs(outdir, exist_ok=True)
        out = os.path.join(outdir, "superbpe.json")
        tok.save(out)
        hfdir = os.path.join(HFV, name)
        os.makedirs(hfdir, exist_ok=True)
        hf = to_hf(tok)
        hf.save(os.path.join(hfdir, "tokenizer.json"))
        manifest[name] = {
            "superbpe": os.path.relpath(out, ROOT),
            "hf": os.path.relpath(os.path.join(hfdir, "tokenizer.json"), ROOT),
            "sha256_superbpe": sha(out),
            "sha256_hf": sha(os.path.join(hfdir, "tokenizer.json")),
            "vocab": tok.vocab_size,
            "transition": tok.transition,
            "stage1_merges": len(tok.stage1),
            "stage2_merges": len(tok.stage2),
            "digits": tok.digits,
            "normalize": tok.normalize,
            "forced_merges": tok.meta.get("forced_merges", 0),
            "data_source": data_source,
        }
        print(name, manifest[name]["vocab"], manifest[name]["sha256_hf"][:12])
    os.makedirs(os.path.join(ROOT, "tkx_c", "results"), exist_ok=True)
    with open(os.path.join(ROOT, "tkx_c", "results", "variant_manifest.json"),
              "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write("\n")


if __name__ == "__main__":
    main()
