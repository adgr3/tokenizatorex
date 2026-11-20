"""Generuje zamrożone sekwencje ID z kanonicznego eksportu HF dla każdego wariantu."""
from __future__ import annotations

import hashlib
import json
import os
import sys

from tokenizers import Tokenizer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLD = os.path.join(ROOT, "tkx_c", "golden")
VARIANTS = ["V0-32k", "V1-32k", "V2-32k", "V2-24k", "V2-16k",
            "V2-base-32k", "V2-base-24k", "V2-base-16k",
            "V2b-32k", "V2b-24k", "V2b-16k",
            "V3-32k", "V3-24k", "V3-16k"]


def sha(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main() -> None:
    data = json.load(open(os.path.join(GOLD, "dataset.json"), encoding="utf-8"))
    sents = data["sentences"]
    sents_sha = hashlib.sha256(json.dumps(sents, ensure_ascii=False).encode()).hexdigest()
    for name in VARIANTS:
        path = os.path.join(ROOT, "hf", "variants", name, "tokenizer.json")
        tok = Tokenizer.from_file(path)
        seqs = []
        bad = 0
        for s in sents:
            ids = tok.encode(s, add_special_tokens=False).ids
            seqs.append(ids)
            if tok.decode(ids, skip_special_tokens=False) != s:
                bad += 1
        payload = {"variant": name, "sentences_sha256": sents_sha,
                   "tokenizer_sha256": sha(path), "roundtrip_bad": bad,
                   "sequences": seqs}
        out = os.path.join(GOLD, name + ".json")
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            json.dump(payload, f, ensure_ascii=False)
            f.write("\n")
        print(name, "sentences", len(seqs), "bad_roundtrip", bad, "->", out)


if __name__ == "__main__":
    main()
