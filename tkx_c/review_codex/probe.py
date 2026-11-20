"""Blind probe: load HF tokenizers BEFORE touching repo-local tokenizers/ dir."""
import tokenizers as hf_tok  # noqa: F401  -- import HF first (trap rule 6)
from tokenizers import Tokenizer
import sys, os, json

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

EXAMPLES = [
    "2024", "2027", "45233140-2", "1 234 567,89", "0,125", "00-950",
    "ZP.271.12.2026", "20.11.2026", "Dz.U. z 2024 r. poz. 1320",
    "art. 275 pkt 1", "0012", "123456789012345", "COVID-19", "A4", "H2O",
]

def load(v):
    return Tokenizer.from_file(os.path.join(REPO, "hf", "variants", v, "tokenizer.json"))

toks = {v: load(v) for v in ["V0-32k", "V2-32k", "V2b-32k", "V3-32k"]}
print("=== example pieces ===")
for s in EXAMPLES:
    print("TEXT:", repr(s))
    for v, t in toks.items():
        e = t.encode(s, add_special_tokens=False)
        print(f"  {v:8s} -> {len(e.ids):2d} pieces: {e.tokens}")
print("=== decode roundtrip quick ===")
for s in EXAMPLES:
    for v, t in toks.items():
        e = t.encode(s, add_special_tokens=False)
        d = t.decode(e.ids, skip_special_tokens=False)
        if d != s:
            print("MISMATCH", v, repr(s), repr(d))
print("=== 특수: ·roku· ===")
for v, t in toks.items():
    vocab = json.load(open(os.path.join(REPO,"hf","variants",v,"tokenizer.json"),encoding="utf-8"))["model"]["vocab"]
    key = "ĠrokuĠ"
    print(v, "has ĠrokuĠ:", key in vocab)
    e = t.encode("w roku 2024 r. zadanie", add_special_tokens=False)
    print("   ", e.tokens)
