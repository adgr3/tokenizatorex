"""sprawdz_sam.py — zakoduj podany tekst wszystkimi wariantami i Slayerem, drukuj segmentację.

Użycie:
    python scripts/sprawdz_sam.py "Twój tekst."
    python scripts/sprawdz_sam.py --file sciezka.txt
    echo "tekst" | python scripts/sprawdz_sam.py

Wymaga: tokenizers==0.23.3, tiktoken, (opcjonalnie) sieć dla modeli HF.
"""
from __future__ import annotations

import argparse
import os
import sys

# H9: najpierw pakiet HF, potem repo na sys.path
from tokenizers import Tokenizer as HFTokenizer  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO not in sys.path:
    sys.path.append(REPO)

HF_VARIANTS = os.path.join(REPO, "hf", "variants")


def load_local_variants():
    out = {}
    if os.path.isdir(HF_VARIANTS):
        for name in sorted(os.listdir(HF_VARIANTS)):
            p = os.path.join(HF_VARIANTS, name, "tokenizer.json")
            if os.path.isfile(p):
                try:
                    out[name] = HFTokenizer.from_file(p)
                except Exception as e:  # noqa: BLE001
                    print(f"# ostrzeżenie: nie udało się wczytać {name}: {e}", file=sys.stderr)
    return out


def load_hf_repo(repo):
    try:
        from huggingface_hub import hf_hub_download
        p = hf_hub_download(repo_id=repo, filename="tokenizer.json")
        return HFTokenizer.from_file(p)
    except Exception as e:  # noqa: BLE001
        print(f"# brak dostępu do {repo}: {e}", file=sys.stderr)
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("text", nargs="?", default=None)
    ap.add_argument("--file", default=None)
    args = ap.parse_args()

    if args.file:
        with open(args.file, encoding="utf-8") as f:
            text = f.read()
    elif args.text is not None:
        text = args.text
    else:
        text = sys.stdin.read()

    text = text.strip()
    if not text:
        print("brak tekstu", file=sys.stderr)
        sys.exit(2)

    encoders = {}
    for name, tok in load_local_variants().items():
        encoders[f"TKX/{name}"] = tok

    # Slayer
    sl = load_hf_repo("SlayerLab/Slayer1B-1.08")
    if sl is not None:
        encoders["Slayer1B-1.08"] = sl

    # APT3
    apt = load_hf_repo("Azurro/APT3-1B-Base")
    if apt is not None:
        encoders["APT3-1B"] = apt

    # Qwen3.5
    qw = load_hf_repo("Qwen/Qwen3.5-4B")
    if qw is not None:
        encoders["Qwen3.5"] = qw

    # Bielik
    bi = load_hf_repo("speakleash/Bielik-1.5B-v3")
    if bi is not None:
        encoders["Bielik-1.5B-v3"] = bi

    # PLLuM
    pl = load_hf_repo("CYFRAGOVPL/PLLuM-12B-base-2412")
    if pl is not None:
        encoders["PLLuM-12B"] = pl

    # GPT-4o
    try:
        import tiktoken
        enc = tiktoken.get_encoding("o200k_base")

        class TK:
            def encode(self, t, add_special_tokens=False):
                return type("E", (), {"ids": enc.encode(t, disallowed_special=())})()

            def decode(self, ids):
                return enc.decode(ids)

        # adapt: store a wrapper object with .encode().ids
        class W:
            def __init__(self):
                self._e = enc

            def encode(self, t, add_special_tokens=False):
                return type("O", (), {"ids": self._e.encode(t, disallowed_special=())})()

            def decode(self, ids):
                return enc.decode(ids)

        encoders["GPT-4o-o200k"] = W()
    except Exception as e:  # noqa: BLE001
        print(f"# brak tiktoken: {e}", file=sys.stderr)

    print(f"Tekst: {text!r}")
    print(f"Długość: {len(text)} znaków, {len(text.split())} słów")
    print("=" * 80)
    rows = []
    for label in sorted(encoders):
        tok = encoders[label]
        try:
            ids = tok.encode(text, add_special_tokens=False).ids
            toks = [tok.decode([i]) for i in ids]
            seg = " | ".join(toks)
            rows.append((label, len(ids), seg))
        except Exception as e:  # noqa: BLE001
            rows.append((label, -1, f"ERR: {e}"))
    # sort by token count
    rows.sort(key=lambda r: (r[1] if r[1] >= 0 else 10**9, r[0]))
    for label, n, seg in rows:
        print(f"{label:22s} {n:4d} tok  {seg}")
    print("=" * 80)
    if rows:
        best = min((r for r in rows if r[1] >= 0), key=lambda r: r[1])
        print(f"Najmniej tokenów: {best[0]} ({best[1]})")


if __name__ == "__main__":
    main()
