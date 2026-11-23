import json
d=json.load(open("results/tkx_v2_special_chars.json",encoding="utf-8"))
for t in ["TKX/V0-32k","TKX/V3-32k","Slayer1B-1.08"]:
    row=d["tokenizers"][t]
    print(t, "section_sign=", row.get("§"))
