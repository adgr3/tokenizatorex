import json, os, sys
from tokenizers import Tokenizer

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

def test_patterns_deterministic():
    data = json.load(open(os.path.join(REPO, "tkx_v2", "wzorce.json"), encoding="utf-8"))
    tok_path = os.path.join(REPO, "hf", "variants", "V0-32k", "tokenizer.json")
    tok = Tokenizer.from_file(tok_path)
    for it in data["items"][:20]:
        a = tok.encode(it["pattern"], add_special_tokens=False).ids
        b = tok.encode(it["pattern"], add_special_tokens=False).ids
        assert a == b
        assert len(a) > 0
