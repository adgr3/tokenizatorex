import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tokenizers import Tokenizer
REPO=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPECIAL = ["§","„","”","–","—","…","€","×","°","²","½","№","ó","ą","ę","ś","ć","ń","ź","ż",
           "ł","µ","©","®","™","•","·","«","»","−","≥","≤","≠","≈","√","∞","∑","∏","∫","→"]
toks={}
base=os.path.join(REPO,"hf","variants")
for name in sorted(os.listdir(base)):
    p=os.path.join(base,name,"tokenizer.json")
    if os.path.isfile(p):
        toks["TKX/"+name]=Tokenizer.from_file(p)
# remotes cached?
import glob
for cached in glob.glob(os.path.join(REPO,"audit","data","tokenizer_files","*.json")):
    pass
sc={"chars":SPECIAL,"tokenizers":{}}
for label,tok in toks.items():
    row={}
    for ch in SPECIAL:
        try:
            ids=tok.encode(ch, add_special_tokens=False).ids
            row[ch]= (len(ids)==1)
        except Exception:
            row[ch]=False
    sc["tokenizers"][label]=row
# GPT-4o via tiktoken
try:
    import tiktoken
    enc=tiktoken.get_encoding("o200k_base")
    row={}
    for ch in SPECIAL:
        ids=enc.encode(ch, disallowed_special=())
        row[ch]=(len(ids)==1)
    sc["tokenizers"]["GPT-4o-o200k"]=row
except Exception as e:
    print("tiktoken err", e)
# Slayer cached?
sl_path=r"C:\Users\x\.cache\huggingface\hub\models--SlayerLab--Slayer1B-1.08\snapshots\ea0945b11153e67517b70d21192e6076d161f658\tokenizer.json"
if os.path.isfile(sl_path):
    tok=Tokenizer.from_file(sl_path)
    row={}
    for ch in SPECIAL:
        try:
            ids=tok.encode(ch, add_special_tokens=False).ids
            row[ch]=(len(ids)==1)
        except Exception:
            row[ch]=False
    sc["tokenizers"]["Slayer1B-1.08"]=row
out=os.path.join(REPO,"results","tkx_v2_special_chars.json")
json.dump(sc, open(out,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
print("done", len(toks))
