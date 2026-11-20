"""Round-trip kanonicznego HF + informacyjna zgodność z enkoderem Python."""
from __future__ import annotations

import json
import os
import sys
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from superbpe import CHUNK_RE, SuperBPETokenizer  # noqa: E402
from measure_lib import DOMAINS, OFFICIAL, VARIANTS, docs, hf_encode, load_hf  # noqa: E402

RES = os.path.join(ROOT, "tkx_c", "results")
PY_VARIANTS = ["V0-32k", "V1-32k", "V2-32k", "V2b-32k", "V3-32k"]


def main() -> None:
    toks = {v: load_hf(v) for v in VARIANTS}
    rt = {"meta": {"split": "test", "note": "V2 porównywany po NFC"},
          "variants": {}, "docs": 0}
    for v, tok in toks.items():
        ok = bad = 0
        for d in DOMAINS:
            for doc in docs(d):
                text = doc["text"]
                target = unicodedata.normalize("NFC", text) if v.startswith(("V2", "V3")) else text
                ids = hf_encode(tok, text)
                if tok.decode(ids, skip_special_tokens=False) == target:
                    ok += 1
                else:
                    bad += 1
        rt["variants"][v] = {"ok": ok, "bad": bad}
        rt["docs"] += ok + bad
        print("roundtrip", v, ok, bad)
    with open(os.path.join(RES, "roundtrip.json"), "w", encoding="utf-8") as f:
        json.dump(rt, f, indent=2, ensure_ascii=False)
        f.write("\n")

    par = {"meta": {"split": "test", "sample_docs_per_domain": 50,
                    "note": "porównanie list kawałków na fragmentach; informacyjne"},
           "variants": {}}
    for v in PY_VARIANTS:
        py = SuperBPETokenizer.load(os.path.join(ROOT, "tokenizers", "variants", v,
                                                 "superbpe.json"))
        hf = toks[v]
        total = same = ours_tokens = hf_tokens = 0
        for d in OFFICIAL:
            ds = docs(d)[:50]
            for doc in ds:
                text = doc["text"]
                if v.startswith(("V2", "V3")):
                    text = unicodedata.normalize("NFC", text)
                for ch in CHUNK_RE.findall(text):
                    a = py.encode_ordinary(ch)
                    b = hf_encode(hf, ch)
                    total += 1
                    same += a == b
                    ours_tokens += len(a)
                    hf_tokens += len(b)
        par["variants"][v] = {
            "chunks": total, "identical": same,
            "identical_share": same / total if total else None,
            "tokens_python": ours_tokens, "tokens_hf": hf_tokens,
            "token_delta": hf_tokens - ours_tokens,
        }
        print("parity", v, f"{same/total:.4%}", hf_tokens - ours_tokens)
    with open(os.path.join(RES, "python_parity.json"), "w", encoding="utf-8") as f:
        json.dump(par, f, indent=2, ensure_ascii=False)
        f.write("\n")


if __name__ == "__main__":
    main()
