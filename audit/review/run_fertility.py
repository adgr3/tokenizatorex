"""R2 #1: fertility = tokeny / str.split() na TEST, 3 dziedziny urzedowe."""
from __future__ import annotations

import json

import r2lib


def main() -> None:
    toks = r2lib.get_tokenizers()
    out = {"definition": "tokens / len(text.split()), split == 'test'", "domains": {}}
    for dom in r2lib.OFFICIAL3:
        docs = r2lib.load_docs(dom)
        words = sum(len(d["text"].split()) for d in docs)
        words_field = sum(int(d["words"]) for d in docs)
        entry = {
            "docs": len(docs),
            "words_from_split": words,
            "words_field": words_field,
            "chars": sum(len(d["text"]) for d in docs),
            "tokenizers": {},
        }
        for label, tok in toks.items():
            n = sum(r2lib.n_tokens(tok, d["text"]) for d in docs)
            entry["tokenizers"][label] = {
                "tokens": n,
                "fertility": n / words,
                "bytes_per_token": sum(len(d["text"].encode("utf-8")) for d in docs) / n,
                "chars_per_token": entry["chars"] / n,
            }
        out["domains"][dom] = entry
        print(dom, "docs", len(docs), "words", words)
        for label, v in entry["tokenizers"].items():
            print(f"  {label:18s} tokens={v['tokens']:8d} fertility={v['fertility']:.6f}")
    path = r2lib.write_json("r2_fertility.json", out)
    print("WROTE", path)


if __name__ == "__main__":
    main()
