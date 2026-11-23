"""sprawdz_sam.py — zakoduj podany tekst wszystkimi wariantami i Slayerem, drukuj segmentację.

Użycie:
    python scripts/sprawdz_sam.py "Twój tekst."
    python scripts/sprawdz_sam.py --file sciezka.txt
    echo "tekst" | python scripts/sprawdz_sam.py

Domyślnie: lokalne tokenizery TOKENIZATOREX + Slayer (bez logowania).
Flaga --wszystkie: dodatkowo Bielik, APT3, Qwen3.5, PLLuM, GPT-4o.
"""
from __future__ import annotations

import argparse
import os
import sys

from tokenizers import Tokenizer as HFTokenizer  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO not in sys.path:
    sys.path.append(REPO)

HF_VARIANTS = os.path.join(REPO, "hf", "variants")


def readable_token(tok_str: str) -> str:
    # Pokaż tokeny bajtowe czytelnie, bez znaków zastępczych.
    if "\ufffd" in tok_str or any(ord(c) < 32 and c not in "\n\t\r" for c in tok_str):
        return "".join(f"<0x{b:02X}>" for b in tok_str.encode("utf-8", errors="replace"))
    return tok_str


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


def load_hf_repo(repo, local_only=True):
    try:
        from huggingface_hub import hf_hub_download
        p = hf_hub_download(repo_id=repo, filename="tokenizer.json", local_files_only=local_only)
        return HFTokenizer.from_file(p)
    except Exception as e:  # noqa: BLE001
        print(f"# brak dostępu do {repo}: {e}", file=sys.stderr)
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("text", nargs="?", default=None)
    ap.add_argument("--file", default=None)
    ap.add_argument("--wszystkie", action="store_true", help="dołącz także zewnętrzne tokenizery HF/tiktoken")
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

    sl = load_hf_repo("SlayerLab/Slayer1B-1.08", local_only=True)
    if sl is not None:
        encoders["Slayer1B-1.08"] = sl

    if args.wszystkie:
        for label, repo in [
            ("APT3-1B", "Azurro/APT3-1B-Base"),
            ("Qwen3.5", "Qwen/Qwen3.5-4B"),
            ("Bielik-1.5B-v3", "speakleash/Bielik-1.5B-v3"),
            ("PLLuM-12B", "CYFRAGOVPL/PLLuM-12B-base-2412"),
        ]:
            tok = load_hf_repo(repo, local_only=True)
            if tok is not None:
                encoders[label] = tok
        try:
            import tiktoken
            enc = tiktoken.get_encoding("o200k_base")

            class W:
                def __init__(self):
                    self._e = enc

                def encode(self, t, add_special_tokens=False):
                    return type("O", (), {"ids": self._e.encode(t, disallowed_special=())})()

                def decode(self, ids):
                    return enc.decode(list(ids))

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
            toks = [readable_token(tok.decode([i])) for i in ids]
            seg = " | ".join(toks)
            rows.append((label, len(ids), seg))
        except Exception as e:  # noqa: BLE001
            rows.append((label, -1, f"ERR: {e}"))
    rows.sort(key=lambda r: (r[1] if r[1] >= 0 else 10**9, r[0]))
    for label, n, seg in rows:
        print(f"{label:22s} {n:4d} tok  {seg}")
    print("=" * 80)
    ok_rows = [r for r in rows if r[1] >= 0]
    if ok_rows:
        best = min(ok_rows, key=lambda r: r[1])
        print(f"Najmniej tokenów: {best[0]} ({best[1]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
