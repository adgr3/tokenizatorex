import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tokenizers import Tokenizer
for name in ["V0-32k","V3-32k"]:
    p=os.path.join("hf","variants",name,"tokenizer.json")
    t=Tokenizer.from_file(p)
    s="§"
    ids=t.encode(s, add_special_tokens=False).ids
    toks=[t.decode([i]) for i in ids]
    print(name, ids, toks)
