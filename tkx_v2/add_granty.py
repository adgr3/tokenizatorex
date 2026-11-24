import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tokenizers import Tokenizer as HFTokenizer
import tkx_v2.measure as m

docs = m.load_tc1() if False else None
# load granty
pass
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "audit"))
import common
granty_docs = []
import os as _os
d = _os.path.join(_os.path.dirname(__file__), "..", "audit", "data", "raw", "granty_ogloszenia")
for name in sorted(_os.listdir(d)):
    if name.endswith(".json"):
        doc = json.load(open(_os.path.join(d, name), encoding="utf-8"))
        if doc.get("split") == "test":
            granty_docs.append(doc["text"])
print("granty test docs", len(granty_docs))
if not granty_docs:
    granty_docs = [json.load(open(_os.path.join(d,n),encoding="utf-8"))["text"] for n in sorted(_os.listdir(d)) if n.endswith(".json")]

toks = m.load_tokenizers()
res = json.load(open(os.path.join(os.path.dirname(__file__), "..", "results", "tkx_v2_fertility.json"), encoding="utf-8"))
src = {"docs": len(granty_docs), "words": sum(len(x.split()) for x in granty_docs),
       "bytes": sum(len(x.encode("utf-8")) for x in granty_docs), "tokenizers": {}}
for label, tok in toks.items():
    fert, bpt, tpd, wpd = m.fertility_for(tok, granty_docs)
    lo, hi = m.bootstrap_ratio_ci(tpd, wpd)
    src["tokenizers"][label] = {"fertility": fert, "bytes_per_token": bpt,
                                "fertility_ci_lo": lo, "fertility_ci_hi": hi}
res["sources"]["5_granty"] = src
with open(os.path.join(os.path.dirname(__file__), "..", "results", "tkx_v2_fertility.json"), "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=2)
    f.write("\n")
print("done")
