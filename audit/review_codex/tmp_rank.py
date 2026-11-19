import sys, os
sys.path.append('audit')
from common import *
m = read_json('audit/data/MANIFEST.json')
encs = build_encoders(['TOKENIZATOREX', 'TOKENIZATOREX-HF'])
for dom in sorted({d['domain'] for d in m['documents']}):
    docs = load_domain(dom, 'test')
    if not docs:
        continue
    tot = {l: 0 for l in encs}
    words = 0
    for d in docs:
        words += len(d['text'].split())
        for l, e in encs.items():
            tot[l] += len(e.ids(d['text']))
    ref = tot['TOKENIZATOREX'] / words
    hf = tot['TOKENIZATOREX-HF'] / words
    print(dom.ljust(22), 'ref', round(ref, 4), 'hf', round(hf, 4), 'delta', tot['TOKENIZATOREX-HF'] - tot['TOKENIZATOREX'])
