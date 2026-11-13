"""
Trening tokenizerów.

  # baseline: zwykły byte-level BPE (etap 1 do końca)
  python train.py baseline --vocab 32000 --out tokenizers/bpe-32k.json

  # SuperBPE: bierze prefiks merge'y baseline'u do t, potem etap 2 (przez spacje)
  python train.py superbpe --from tokenizers/bpe-32k.json --transition 24000 \
      --vocab 32000 --stage2-mb 60 --out tokenizers/superbpe-32k-t24k.json

Rozmiar `--vocab` obejmuje 256 bajtów + merge'e + tokeny specjalne.
"""
import argparse
import os
import time
from collections import Counter
from multiprocessing import Pool

from superbpe import SuperBPETokenizer, chunks, pretokens

SPECIALS = ["<|endoftext|>"]


def read_blocks(path: str, max_bytes: int | None, block_chars: int = 2_000_000):
    """Czyta plik kawałkami, zawsze tnąc na granicy linii (regexy nie przekraczają \\n)."""
    done = 0
    buf: list[str] = []
    size = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            buf.append(line)
            size += len(line)
            done += len(line.encode("utf-8"))
            if size >= block_chars:
                yield "".join(buf)
                buf, size = [], 0
            if max_bytes and done >= max_bytes:
                break
    if buf:
        yield "".join(buf)


def _count_pretokens(block: str) -> Counter:
    return Counter(pretokens(block))


def _count_chunks(block: str) -> Counter:
    return Counter(chunks(block))


def parallel_count(path: str, fn, max_bytes=None) -> Counter:
    total = Counter()
    with Pool(max(1, os.cpu_count() - 2)) as pool:
        for c in pool.imap_unordered(fn, read_blocks(path, max_bytes), chunksize=1):
            total.update(c)
    return total


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["baseline", "superbpe"])
    ap.add_argument("--data", default="../data/train.txt")
    ap.add_argument("--vocab", type=int, default=32000)
    ap.add_argument("--stage1-mb", type=int, default=None, help="limit danych etapu 1 (MB)")
    ap.add_argument("--from", dest="src", help="baseline, z którego bierzemy etap 1")
    ap.add_argument("--transition", type=int, help="punkt przejścia t (rozmiar słownika po etapie 1)")
    ap.add_argument("--stage2-mb", type=int, default=60)
    ap.add_argument("--max-words", type=int, default=4)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    target = a.vocab - len(SPECIALS)
    t0 = time.time()

    if a.mode == "baseline":
        mb = a.stage1_mb * 10**6 if a.stage1_mb else None
        cnt = parallel_count(a.data, _count_pretokens, mb)
        print(f"pretokeny: {len(cnt):,} unikalnych, {sum(cnt.values()):,} łącznie ({time.time()-t0:.0f}s)")
        tok = SuperBPETokenizer()
        tok.train_stage1(cnt, target)
        tok.meta = {"kind": "baseline-bpe", "data": os.path.basename(a.data),
                    "stage1_bytes": mb or os.path.getsize(a.data)}
    else:
        tok = SuperBPETokenizer.load(a.src)
        tok.specials = {}
        tok.truncate_stage1(a.transition)
        cnt = parallel_count(a.data, _count_chunks, a.stage2_mb * 10**6)
        print(f"fragmenty: {len(cnt):,} unikalnych, {sum(cnt.values()):,} łącznie ({time.time()-t0:.0f}s)")
        tok.train_stage2(cnt, target, max_words=a.max_words)
        tok.meta = {**tok.meta, "kind": "superbpe", "from": os.path.basename(a.src),
                    "stage2_bytes": a.stage2_mb * 10**6}

    tok.add_specials(SPECIALS)
    tok.meta["train_seconds"] = round(time.time() - t0)
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    tok.save(a.out)
    print(f"zapisano {a.out}: vocab {tok.vocab_size}, t={tok.transition}, "
          f"etap2={len(tok.stage2)} merge'y, {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
