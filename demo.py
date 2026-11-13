"""
Pokaż, jak różne tokenizery tną to samo zdanie.

  python demo.py "Na podstawie umowy, w ramach projektu, zgodnie z planem."
"""
import sys

import tiktoken

from superbpe import SuperBPETokenizer

DEFAULT = [
    "Na podstawie art. 5 ustawy, w ramach projektu, zgodnie z planem.",
    "Wydaje mi się, że nie tylko w Polsce jest to możliwe.",
    "W związku z tym, że klient nie może być obecny, spotkanie przełożono.",
]


def show(name: str, pieces: list[str]) -> None:
    print(f"  {name:<22} {len(pieces):>3} tok  " + "|".join(p.replace(" ", "·") for p in pieces))


def main() -> None:
    texts = sys.argv[1:] or DEFAULT
    base = SuperBPETokenizer.load("tokenizers/tokenizatorex-base-32k.json")
    sup = SuperBPETokenizer.load("tokenizers/tokenizatorex-32k.json")
    cl = tiktoken.get_encoding("cl100k_base")
    o2 = tiktoken.get_encoding("o200k_base")
    for t in texts:
        print(f"\n{t}")
        for enc, n in ((cl, "cl100k (GPT-4)"), (o2, "o200k (GPT-4o)")):
            show(n, [enc.decode_single_token_bytes(i).decode("utf-8", "replace") for i in enc.encode(t)])
        show("TOKENIZATOREX-base", [base.vocab[i].decode("utf-8", "replace") for i in base.encode(t)])
        show("TOKENIZATOREX", [sup.vocab[i].decode("utf-8", "replace") for i in sup.encode(t)])


if __name__ == "__main__":
    main()
