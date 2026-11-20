"""Part C: V3 - regula groups3 w enkoderze Python vs w kanonicznym eksporcie HF."""
import tokenizers as hf  # HF przed sys.path.append
from tokenizers import Tokenizer
import sys, pathlib, json

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.append(str(REPO))  # append, nigdy insert(0,...)
from superbpe import SuperBPETokenizer, split_groups3  # noqa: E402

py = SuperBPETokenizer.load(str(REPO / "tokenizers/variants/V3-32k/superbpe.json"))
hft = Tokenizer.from_file(str(REPO / "hf/variants/V3-32k/tokenizer.json"))

EXAMPLES = ["2024", "45233140-2", "00-950", "0012", "123456789012345",
            "Dz.U. z 2024 r. poz. 1320", "1 234 567,89 zł"]
print("=== pretoken split_groups3 (Python) ===")
for s in EXAMPLES:
    print(repr(s), "->", split_groups3(s))
print("=== Python encode_ordinary vs HF encode ===")
diffs = 0
for s in EXAMPLES:
    a = py.encode_ordinary(s)
    b = hft.encode(s, add_special_tokens=False).ids
    da = py.decode(a)
    db = hft.decode(b, skip_special_tokens=False)
    same = a == b
    if not same:
        diffs += 1
    print(repr(s))
    print("  PY ", len(a), [py.decode([i]) for i in a])
    print("  HF ", len(b), hft.encode(s, add_special_tokens=False).tokens)
    print("  same:", same, "decode_py==s:", da == s, "decode_hf==s:", db == s)
print("diff count:", diffs)

out = {"examples_checked": len(EXAMPLES), "diff_count": diffs}
(REPO / "tkx_c/review_codex/probe_hf_py_groups3.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
