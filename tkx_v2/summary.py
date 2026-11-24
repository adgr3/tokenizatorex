import json
d=json.load(open("results/tkx_v2_fertility.json",encoding="utf-8"))
for s,v in d["sources"].items():
    toks=sorted(v["tokenizers"].items(), key=lambda x:x[1]["fertility"])
    print("==",s, v["docs"], "docs", v["words"], "words")
    for t,x in toks[:6]:
        print("  %-22s fert=%.3f bpt=%.2f" % (t, x["fertility"], x["bytes_per_token"]))
