import json, os
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def test_fertility_in_ci():
    d = json.load(open(os.path.join(REPO, "results", "tkx_v2_fertility.json"), encoding="utf-8"))
    for src, info in d["sources"].items():
        for label, m in info["tokenizers"].items():
            assert m["fertility_ci_lo"] <= m["fertility"] <= m["fertility_ci_hi"], (src, label)
