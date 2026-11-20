"""Part B/C: golden i manifest integralnosc."""
import tokenizers as hf  # HF pierwszy
import json, hashlib, pathlib, glob

REPO = pathlib.Path(__file__).resolve().parents[2]
ds = json.loads((REPO / "tkx_c/golden/dataset.json").read_text(encoding="utf-8"))
print("golden sentences:", len(ds["sentences"]))
gold_lens = {}
for p in sorted((REPO / "tkx_c/golden").glob("V*.json")):
    d = json.loads(p.read_text(encoding="utf-8"))
    gold_lens[p.name] = len(d["sequences"])
print("golden files / lens:", gold_lens)

m = json.loads((REPO / "tkx_c/results/variant_manifest.json").read_text(encoding="utf-8"))
print("manifest V2-32k:", json.dumps(m["V2-32k"], ensure_ascii=False, indent=1)[:1200])
bad = []
for v, info in m.items():
    p = REPO / "hf" / "variants" / v / "tokenizer.json"
    if not p.exists():
        bad.append((v, "missing"))
        continue
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    blob = json.dumps(info, ensure_ascii=False)
    if h not in blob:
        bad.append((v, "sha-not-in-manifest", h))
print("hash problems:", bad)
out = {"golden_sentences": len(ds["sentences"]), "golden_lens": gold_lens,
       "manifest_hash_problems": bad}
(REPO / "tkx_c/review_codex/probe_integrity.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
