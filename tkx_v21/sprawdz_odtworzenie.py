"""Weryfikacja odtworzenia V0 (V0R): hash, merge'e i fertility na BZP."""
from __future__ import annotations

import hashlib
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from tokenizers import Tokenizer as HFTokenizer  # noqa: E402


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    p_v0 = os.path.join(REPO, "tokenizers", "variants", "V0-32k", "superbpe.json")
    p_v0r = os.path.join(REPO, "tkx_v21", "warianty", "V0R-32k.json")
    a = json.load(open(p_v0, encoding="utf-8"))
    b = json.load(open(p_v0r, encoding="utf-8"))
    docs = []
    spec1 = os.path.join(os.environ.get("TKX_DANE", "data"),
                         "spec1", "test.jsonl")
    with open(spec1, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                t = json.loads(line).get("text")
                if t:
                    docs.append(t)
    hf_v0 = HFTokenizer.from_file(os.path.join(REPO, "hf", "variants", "V0-32k",
                                               "tokenizer.json"))
    hf_v0r = HFTokenizer.from_file(os.path.join(REPO, "tkx_v21", "hf", "V0R-32k",
                                                "tokenizer.json"))

    def stats(tok):
        toks = sum(len(tok.encode(d, add_special_tokens=False).ids) for d in docs)
        words = sum(len(d.split()) for d in docs)
        return {"tokens": toks, "words": words, "fertility": toks / words}

    out = {
        "v0_superbpe_sha256": sha(p_v0),
        "v0r_superbpe_sha256": sha(p_v0r),
        "hash_equal": sha(p_v0) == sha(p_v0r),
        "stage1_merges_equal": a["stage1_merges"] == b["stage1_merges"],
        "stage2_merges_equal": a["stage2_merges"] == b["stage2_merges"],
        "meta_diff": {k: [a.get("meta", {}).get(k), b.get("meta", {}).get(k)]
                      for k in set(a.get("meta", {})) | set(b.get("meta", {}))
                      if a.get("meta", {}).get(k) != b.get("meta", {}).get(k)},
        "bzp": {"v0": stats(hf_v0), "v0r": stats(hf_v0r)},
        "conclusion": "identyczne merge'e; hash pliku rozni sie tylko metadanymi"
                      if a["stage1_merges"] == b["stage1_merges"]
                      and a["stage2_merges"] == b["stage2_merges"]
                      else "ROZNICA w merge'ach — porownania wzgledem V0R",
    }
    out["bzp"]["identical"] = out["bzp"]["v0"]["tokens"] == out["bzp"]["v0r"]["tokens"]
    with open(os.path.join(REPO, "results", "tkx_v21_reproduction.json"), "w",
              encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps({k: out[k] for k in ("hash_equal", "stage1_merges_equal",
                                         "stage2_merges_equal", "conclusion")},
                     ensure_ascii=False))
    print("BZP:", out["bzp"])


if __name__ == "__main__":
    main()
