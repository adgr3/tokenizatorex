"""Probe: which 7-domain subset / estimator reproduces the claimed cost numbers?"""
import tokenizers as hf_tok  # HF first
from tokenizers import Tokenizer
import json, pathlib, itertools, sys
import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[2]
RAW = REPO / "audit" / "data" / "raw"
HF = REPO / "hf" / "variants"

manifest = json.loads((REPO / "audit" / "data" / "MANIFEST.json").read_text(encoding="utf-8"))
docs = {}
for f in RAW.rglob("*.json"):
    d = json.loads(f.read_text(encoding="utf-8"))
    if "text" in d and "split" in d:
        docs[d["id"]] = d
test = [docs[r["id"]] for r in manifest["documents"] if r["split"] == "test"]
doms = sorted(manifest["domains"])
toks = {v: Tokenizer.from_file(str(HF / v / "tokenizer.json")) for v in ["V0-32k", "V2-32k", "V2b-32k", "V3-32k"]}
texts = [d["text"] for d in test]
cnt = {v: np.array([len(t.encode(s, add_special_tokens=False).ids) for s in texts], dtype=float)
       for v, t in toks.items()}
b = cnt["V0-32k"]
per = {}
for v in ["V2-32k", "V2b-32k", "V3-32k"]:
    per[v] = {}
    for dom in doms:
        idx = [i for i, d in enumerate(test) if d["domain"] == dom]
        per[v][dom] = (cnt[v][idx].sum() - b[idx].sum()) / b[idx].sum() * 100

target = {"V2-32k": 13.99, "V2b-32k": 11.08, "V3-32k": 5.26}
best = []
for subset in itertools.combinations(doms, 7):
    err = sum(abs(per[v][d] and 0) for v in [] )  # noop
    s = 0
    vals = {}
    for v in target:
        sel = [i for i, d in enumerate(test) if d["domain"] in subset]
        num = cnt[v][sel].sum() - b[sel].sum()
        den = b[sel].sum()
        vals[v] = num/den*100
        s += abs(vals[v] - target[v])
    best.append((s, subset, vals))
best.sort()
for s, subset, vals in best[:8]:
    print(f"err={s:6.2f} {subset}")
    print("   ", {k: round(x,3) for k,x in vals.items()})

# Also: mean-of-per-doc-ratio estimator for candidate subsets
print("=== mean of per-doc ratios (official B) ===")
OFFB = ["granty_ogloszenia","prawo_eli","przetargi_kio","przetargi_ogloszenia","samorzad_uchwaly","tabele_json","sejm"]
idx=[i for i,d in enumerate(test) if d["domain"] in OFFB]
for v in ["V2-32k","V2b-32k","V3-32k"]:
    ratios = (cnt[v][idx]-b[idx])/b[idx]*100
    print(v, "mean per-doc", round(ratios.mean(),3), "median", round(np.median(ratios),3))
