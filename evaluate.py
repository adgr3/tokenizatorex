"""
Ewaluacja na held-oucie (tekst z innego shardu niż trening).

  python evaluate.py tokenizers/bpe-32k.json tokenizers/superbpe-*.json --hf speakleash/Bielik-11B-v2.3-Instruct

Metryki (im mniej tokenów, tym taniej i dłuższy efektywny kontekst):
  tokens        — łączna liczba tokenów na całym held-oucie
  fertility     — tokeny / słowo (słowo = ciąg znaków między białymi znakami, `str.split()`)
  bytes/token   — bajty UTF-8 / token (kompresja)
  vs cl100k     — ile razy MNIEJ tokenów niż GPT-4 (cl100k_base) na tym samym tekście
  superwords    — odsetek tokenów, które przekraczają spację (tylko SuperBPE)
  vocab used    — odsetek słownika użyty choć raz na held-oucie
  roundtrip     — decode(encode(x)) == x
"""
import argparse
import glob
import json
import os
import time

import tiktoken

from superbpe import SuperBPETokenizer


def evaluate(name, encode, decode, text, vocab_size=None, is_super=None):
    t0 = time.time()
    ids = encode(text)
    dt = time.time() - t0
    n_words = len(text.split())
    n_bytes = len(text.encode("utf-8"))
    row = {
        "name": name,
        "vocab": vocab_size,
        "tokens": len(ids),
        "fertility": len(ids) / n_words,
        "bytes_per_token": n_bytes / len(ids),
        "chars_per_token": len(text) / len(ids),
        "roundtrip": decode(ids) == text,
        "encode_seconds": round(dt, 1),
    }
    if vocab_size:
        row["vocab_used"] = len(set(ids)) / vocab_size
    if is_super:
        row["superword_share"] = sum(1 for i in ids if is_super(i)) / len(ids)
    return row


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("tokenizers", nargs="*")
    ap.add_argument("--heldout", default="../data/heldout.txt")
    ap.add_argument("--max-mb", type=float, default=10)
    ap.add_argument("--hf", nargs="*", default=[], help="tokenizery HF do porównania (repo id)")
    ap.add_argument("--out", default="results/metrics.json")
    a = ap.parse_args()

    with open(a.heldout, encoding="utf-8") as f:
        text = f.read(int(a.max_mb * 10**6))
    print(f"held-out: {len(text):,} znaków, {len(text.split()):,} słów")

    rows = []
    for enc_name in ("cl100k_base", "o200k_base"):
        enc = tiktoken.get_encoding(enc_name)
        rows.append(evaluate(enc_name, lambda t: enc.encode(t, disallowed_special=()), enc.decode,
                             text, enc.n_vocab))
        print(rows[-1])

    for repo in a.hf:
        from tokenizers import Tokenizer
        try:
            hf = Tokenizer.from_pretrained(repo)
        except Exception as e:  # noqa: BLE001
            print(f"pomijam {repo}: {e}")
            continue
        rows.append(evaluate(repo.split("/")[-1], lambda t: hf.encode(t, add_special_tokens=False).ids,
                             lambda ids: hf.decode(ids, skip_special_tokens=False), text,
                             hf.get_vocab_size()))
        print(rows[-1])

    paths = sorted({p for pat in a.tokenizers for p in glob.glob(pat)})
    for p in paths:
        tok = SuperBPETokenizer.load(p)
        name = os.path.splitext(os.path.basename(p))[0]
        row = evaluate(name, tok.encode_ordinary, tok.decode, text, tok.vocab_size,
                       tok.is_superword if tok.stage2 else None)
        row["transition"] = tok.transition
        rows.append(row)
        print(row)

    base = next(r["tokens"] for r in rows if r["name"] == "cl100k_base")
    for r in rows:
        r["vs_cl100k"] = base / r["tokens"]

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump({"heldout_chars": len(text), "heldout_words": len(text.split()),
                   "heldout_bytes": len(text.encode("utf-8")), "rows": rows}, f, indent=2, ensure_ascii=False)

    print("\n| tokenizer | vocab | t | tokens | fertility | bytes/tok | vs cl100k | superwords | vocab used | roundtrip |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|:-:|")
    for r in rows:
        print(f"| {r['name']} | {r['vocab']:,} | {r.get('transition', '—')} | {r['tokens']:,} | "
              f"{r['fertility']:.3f} | {r['bytes_per_token']:.2f} | {r['vs_cl100k']:.2f}× | "
              f"{r['superword_share']*100:.1f}% | " if 'superword_share' in r else
              f"| {r['name']} | {r['vocab']:,} | {r.get('transition', '—')} | {r['tokens']:,} | "
              f"{r['fertility']:.3f} | {r['bytes_per_token']:.2f} | {r['vs_cl100k']:.2f}× | — | ", end="")
        print(f"{r['vocab_used']*100:.1f}% | {'✓' if r['roundtrip'] else '✗'} |")


if __name__ == "__main__":
    main()
