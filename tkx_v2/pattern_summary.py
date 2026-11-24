import json
d=json.load(open("results/tkx_v2_patterns.json",encoding="utf-8"))
for t,info in list(d["tokenizers"].items())[:3]:
    cats=info["by_category"]
    cons=0; tot=0
    for it in info["per_item"]:
        tot+=1
        if it["consistent_counts"]:
            cons+=1
    print(t, "consistent_count_items=", cons, "/", tot)
    for c,v in cats.items():
        print("   ", c, round(v["mean_tokens"],2), v["n"])
