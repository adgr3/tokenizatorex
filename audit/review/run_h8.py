"""R2 #5: H8 parytet HF na TEST przetargi_ogloszenia.

Fragmenty: CHUNK_RE.findall(text) z superbpe.py. Dla kazdego fragmentu porownujemy
SuperBPETokenizer.encode_ordinary(fragment) z HF encode(fragment,
add_special_tokens=False).ids. Raport: udzial identycznych fragmentow (liczony po
wystapieniach i po unikalnych fragmentach) oraz suma roznicy tokenow (HF - ref).
"""
from __future__ import annotations

import collections
import json

import r2lib
from superbpe import CHUNK_PATTERN, CHUNK_RE


def main() -> None:
    ref = r2lib.RefTok()
    hf = r2lib.HFTok("TOKENIZATOREX-HF", r2lib.HF_PATH)
    docs = r2lib.load_docs("przetargi_ogloszenia")

    n_chunks = 0
    n_ident = 0
    delta = 0
    ref_tokens = 0
    hf_tokens = 0
    uniq = collections.Counter()
    diffs = collections.Counter()
    for d in docs:
        for ch in CHUNK_RE.findall(d["text"]):
            a = ref.encode(ch)
            b = hf.encode(ch)
            n_chunks += 1
            ref_tokens += len(a)
            hf_tokens += len(b)
            delta += len(b) - len(a)
            uniq[ch] += 1
            if a == b:
                n_ident += 1
            else:
                diffs[ch] += 1

    n_uniq = len(uniq)
    n_uniq_ident = sum(1 for ch in uniq if ref.encode(ch) == hf.encode(ch))

    out = {
        "definition": "CHUNK_RE.findall(text); identical if ref.encode_ordinary(chunk) == "
        "hf.encode(chunk, add_special_tokens=False).ids; delta = hf_tokens - ref_tokens",
        "domain": "przetargi_ogloszenia",
        "docs": len(docs),
        "chunk_pattern": CHUNK_PATTERN,
        "chunks": n_chunks,
        "identical_chunks": n_ident,
        "share_identical_chunks": n_ident / n_chunks,
        "unique_chunks": n_uniq,
        "unique_identical_chunks": n_uniq_ident,
        "share_identical_unique_chunks": n_uniq_ident / n_uniq,
        "ref_tokens": ref_tokens,
        "hf_tokens": hf_tokens,
        "token_delta_hf_minus_ref": delta,
        "relative_token_delta": delta / ref_tokens,
        "top_differing_chunks": [
            {"chunk": ch, "count": c, "ref": len(ref.encode(ch)), "hf": len(hf.encode(ch))}
            for ch, c in diffs.most_common(30)
        ],
    }
    print(json.dumps({k: v for k, v in out.items() if k != "top_differing_chunks"}, ensure_ascii=False, indent=2))
    print("top diffs:")
    for x in out["top_differing_chunks"][:15]:
        print(f"  {x['count']:5d} ref={x['ref']} hf={x['hf']} {x['chunk']!r}")
    path = r2lib.write_json("r2_h8_hf_parity.json", out)
    print("WROTE", path)


if __name__ == "__main__":
    main()
