import json
import os
import random
from pathlib import Path

from tokenizers import Tokenizer

REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "results"


def load_tokenizers():
    toks = {
        "V0": Tokenizer.from_file(str(REPO / "tkx_v21" / "hf" / "V0R-32k" / "tokenizer.json")),
        "V0J2": Tokenizer.from_file(str(REPO / "hf" / "variants" / "V0J2-32k" / "tokenizer.json")),
        "V3": Tokenizer.from_file(str(REPO / "hf" / "variants" / "V3-32k" / "tokenizer.json")),
    }
    # Slayer - prefer local HF cache
    try:
        from huggingface_hub import hf_hub_download
        p = hf_hub_download("SlayerLab/Slayer1B-1.08", "tokenizer.json", local_files_only=True)
        toks["Slayer"] = Tokenizer.from_file(p)
    except Exception:
        try:
            toks["Slayer"] = Tokenizer.from_pretrained("SlayerLab/Slayer1B-1.08")
        except Exception as e:
            print("Slayer niedostepny:", str(e)[:120])
    # GPT-4o optional
    try:
        import tiktoken
        enc = tiktoken.get_encoding("o200k_base")
        class W:
            def encode(self, s, add_special_tokens=False):
                return type("O", (), {"ids": enc.encode(s, disallowed_special=())})()
            def decode(self, ids):
                return enc.decode(list(ids))
        toks["GPT-4o"] = W()
    except Exception as e:
        print("GPT-4o niedostepny:", str(e)[:120])
    return toks


def n(tok, s):
    return len(tok.encode(s, add_special_tokens=False).ids)


def main():
    random.seed(20261123)
    rng = random.Random(20261123)
    toks = load_tokenizers()

    M = ['stycznia','lutego','marca','kwietnia','maja','czerwca','lipca','sierpnia','września','października','listopada','grudnia']
    R = ['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII']
    dates = [(rng.randint(2019,2027), rng.randint(1,12), rng.randint(1,28)) for _ in range(40)]
    F = {
        'RRRR.MM.DD': lambda y,m,d: f'{y}.{m:02d}.{d:02d}',
        'RRRR-MM-DD': lambda y,m,d: f'{y}-{m:02d}-{d:02d}',
        'DD.MM.RRRR': lambda y,m,d: f'{d:02d}.{m:02d}.{y}',
        'D.MM.RRRR': lambda y,m,d: f'{d}.{m:02d}.{y}',
        'DD.MM.RRRR r.': lambda y,m,d: f'{d:02d}.{m:02d}.{y} r.',
        'D.MM.RRRRr.': lambda y,m,d: f'{d}.{m:02d}.{y}r.',
        'DD/MM/RRRR': lambda y,m,d: f'{d:02d}/{m:02d}/{y}',
        'D miesiąca RRRR r.': lambda y,m,d: f'{d} {M[m-1]} {y} r.',
        'D miesiąca RRRRr.': lambda y,m,d: f'{d} {M[m-1]} {y}r.',
        'z dnia D miesiąca RRRR r.': lambda y,m,d: f'z dnia {d} {M[m-1]} {y} r.',
        'D RZYM RRRR': lambda y,m,d: f'{d} {R[m-1]} {y}',
        'D.RZYM.RRRR': lambda y,m,d: f'{d}.{R[m-1]}.{y}',
    }
    amts = [rng.choice([rng.randint(100,999), rng.randint(1000,99999), rng.randint(100000,9999999)]) + rng.randint(0,99)/100 for _ in range(40)]
    def sp(x):
        return f'{int(x):,}'.replace(',',' ')
    A = {
        '1 234,56 zł': lambda a: f'{sp(a)},{round(a%1*100):02d} zł',
        '1234,56 zł': lambda a: f'{int(a)},{round(a%1*100):02d} zł',
        '1.234,56 zł': lambda a: f"{int(a):,}".replace(',','.') + f',{round(a%1*100):02d} zł',
        '1234.56 PLN': lambda a: f'{a:.2f} PLN',
        '1 234,56 PLN': lambda a: f'{sp(a)},{round(a%1*100):02d} PLN',
        '1 234 zł': lambda a: f'{sp(a)} zł',
        'kwota brutto: 1 234,56 zł': lambda a: f'kwota brutto: {sp(a)},{round(a%1*100):02d} zł',
        '1,2 mln zł': lambda a: f"{a/1e6:.1f}".replace('.',',')+' mln zł',
        '123 tys. zł': lambda a: f'{int(a/1000)} tys. zł',
    }
    P = ['§','§ 5','§ 12 ust. 3','§ 12 ust. 3 pkt 4 lit. a','§5','§§ 3–5','w § 2','zgodnie z § 14 ust. 1','art. 5 § 2']

    out = {'seed': 20261123, 'daty': {}, 'kwoty': {}, 'paragraf': {}, 'tokenizers': list(toks.keys())}
    hdr = 'format'.ljust(28) + ''.join(k.rjust(10) for k in toks)
    print('DATY (srednia liczba tokenow na 40 dat)'); print(hdr)
    for f, fn in F.items():
        row = {k: sum(n(t, fn(*d)) for d in dates)/len(dates) for k, t in toks.items()}
        out['daty'][f] = row
        print(f.ljust(28) + ''.join(f"{row[k]:10.2f}" for k in toks))
    print('\nKWOTY (40 kwot)'); print(hdr)
    for f, fn in A.items():
        row = {k: sum(n(t, fn(a)) for a in amts)/len(amts) for k, t in toks.items()}
        out['kwoty'][f] = row
        print(f.ljust(28) + ''.join(f"{row[k]:10.2f}" for k in toks))
    print('\nPARAGRAF (tokeny)'); print(hdr)
    for ptn in P:
        row = {k: n(t, ptn) for k, t in toks.items()}
        out['paragraf'][ptn] = row
        print(ptn.ljust(28) + ''.join(f"{row[k]:10d}" for k in toks))

    # summary checks for tests
    date_avgs = {k: sum(v[k] for v in out['daty'].values())/len(out['daty']) for k in toks}
    kwoty_avgs = {k: sum(v[k] for v in out['kwoty'].values())/len(out['kwoty']) for k in toks}
    out['summary'] = {'date_avg': date_avgs, 'kwota_avg': kwoty_avgs}
    out['examples'] = {
        '2 stycznia 2026 r.': {k: [t.decode([i]) for i in t.encode('2 stycznia 2026 r.', add_special_tokens=False).ids] for k, t in toks.items()},
        '1 234 567,89 zł': {k: [t.decode([i]) for i in t.encode('1 234 567,89 zł', add_special_tokens=False).ids] for k, t in toks.items()},
    }

    RESULTS.mkdir(parents=True, exist_ok=True)
    with open(RESULTS / 'tkx_v21_formaty.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print('\nzapisano', RESULTS / 'tkx_v21_formaty.json')


if __name__ == '__main__':
    main()
