import json
d=json.load(open("results/tkx_v2_special_chars.json",encoding="utf-8"))
for t in ["TKX/V0-32k","TKX/V3-32k","Slayer1B-1.08","GPT-4o-o200k"]:
    row=d["tokenizers"].get(t,{})
    print(t, "section=", row.get("§"), "count=", sum(1 for v in row.values() if v))
