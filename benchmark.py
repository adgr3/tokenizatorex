"""
Benchmark TOKENIZATOREX vs tokenizery prawdziwych modeli (polskich i światowych).

  python benchmark.py                       # pobiera tokenizery z HF (publiczne), liczy, zapisuje wyniki
  python benchmark.py --extra speakleash/Bielik-11B-v3.1-Instruct   # modele "gated" po `hf auth login`

Dla każdego tokenizera i każdej dziedziny liczymy fertility = tokeny / słowo (str.split()).
Mniej = taniej, szybciej i więcej tekstu w oknie kontekstu modelu.

Wyniki: results/benchmark.json, results/benchmark.md, results/benchmark.svg
"""
import argparse
import glob
import json
import os
import time

import regex as re
import tiktoken
from tokenizers import Tokenizer

from superbpe import SuperBPETokenizer

# (etykieta, repo HF, opis) — kolejność = kolejność w tabeli przed sortowaniem
MODELS = [
    ("Slayer1B (GoLLeM-v6)", "SlayerLab/Slayer1B-1.07", "SlayerLab, tokenizer v6 (Slayer1B 1.00–1.09)"),
    ("Slayer139", "SlayerLab/Slayer139-base", "SlayerLab"),
    ("Slayer149", "SlayerLab/Slayer149", "SlayerLab"),
    ("Pollock-2.0", "SlayerLab/pollock-2.0-polishdynaword-150m", "SlayerLab"),
    ("GoLLeM-v4", "SlayerLab/gollem-v4-250m-pl", "SlayerLab (= TokenizerTest-32m-A)"),
    ("TokenizerTest-32m-B", "SlayerLab/TokenizerTest-32m-B", "SlayerLab"),
    ("Bielik-11B-v2.3", "speakleash/Bielik-11B-v2.3-Instruct", "SpeakLeash (tokenizer Mistral 7B)"),
    ("PLLuM-12B-2512", "CYFRAGOVPL/PLLuM-12B-chat-2512", "PLLuM (tokenizer Mistral Nemo / Tekken)"),
    ("PLLuM-4B-2512", "CYFRAGOVPL/PLLuM-4B-chat-2512", "PLLuM (tokenizer Gemma 3)"),
    ("Llama-PLLuM-8B-2512", "CYFRAGOVPL/Llama-PLLuM-8B-chat-2512", "PLLuM (tokenizer Llama 3)"),
    ("PLLuM-8x7B-2412", "CYFRAGOVPL/PLLuM-8x7B-chat-2412", "PLLuM (tokenizer Mixtral)"),
    ("APT3-1B", "Azurro/APT3-1B-Base", "Azurro, polski tokenizer"),
    ("polish-gpt2", "sdadas/polish-gpt2-large", "sdadas, polski GPT-2"),
    ("Qwen3", "Qwen/Qwen3-8B", "Alibaba"),
    ("Qwen3.5", "Qwen/Qwen3.5-9B", "Alibaba"),
    ("DeepSeek-V3", "deepseek-ai/DeepSeek-V3", "DeepSeek"),
]
TIKTOKEN = [
    ("GPT-4 (cl100k)", "cl100k_base", "OpenAI"),
    ("GPT-4o / GPT-5 (o200k)", "o200k_base", "OpenAI (też gpt-oss)"),
]
OURS = [
    ("TOKENIZATOREX", "tokenizers/tokenizatorex-32k.json", "nasz — SuperBPE, t=20k"),
    ("TOKENIZATOREX-base", "tokenizers/tokenizatorex-base-32k.json", "nasz — zwykły BPE"),
]
# Tokenizery, które na długim tekście zwalniają ponadliniowo (setki regexów w pretokenizacji).
# Kodujemy je per dokument; sprawdzone, że wynik jest identyczny jak dla całego tekstu.
SPLIT_DOCS = {"SlayerLab/TokenizerTest-32m-B"}
POLISH = ["web", "wikipedia", "literatura", "prawo", "sejm", "nauka", "dyskusje"]
ALL_DOMAINS = POLISH + ["angielski"]


def load_hf(repo: str, cache: str) -> Tokenizer:
    path = os.path.join(cache, repo.replace("/", "__") + ".json")
    if os.path.exists(path):
        return Tokenizer.from_file(path)
    tok = Tokenizer.from_pretrained(repo)
    tok.save(path)
    return tok


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", default="../data/bench")
    ap.add_argument("--cache", default="../data/model_tokenizers")
    ap.add_argument("--extra", nargs="*", default=[], help="dodatkowe repo HF (np. gated po zalogowaniu)")
    ap.add_argument("--out", default="results/benchmark")
    a = ap.parse_args()
    os.makedirs(a.cache, exist_ok=True)

    texts = {}
    for d in ALL_DOMAINS:
        with open(os.path.join(a.bench, f"{d}.txt"), encoding="utf-8") as f:
            texts[d] = f.read()
    words = {d: len(t.split()) for d, t in texts.items()}

    encoders = []  # (label, group, vocab, encode, decode, note)
    for label, path, note in OURS:
        t = SuperBPETokenizer.load(path)
        encoders.append((label, "nasz", t.vocab_size, t.encode_ordinary, t.decode, note))
    for label, name, note in TIKTOKEN:
        e = tiktoken.get_encoding(name)
        encoders.append((label, "świat", e.n_vocab, lambda s, e=e: e.encode(s, disallowed_special=()), e.decode, note))
    models = MODELS + [(r.split("/")[-1], r, "dodatkowy") for r in a.extra]
    for label, repo, note in models:
        try:
            t = load_hf(repo, a.cache)
        except Exception as ex:  # noqa: BLE001
            print(f"POMIJAM {repo}: {type(ex).__name__}: {str(ex)[:120]}")
            continue
        group = "polski" if any(k in repo for k in ("SlayerLab", "speakleash", "CYFRAGOVPL", "Azurro", "sdadas")) else "świat"
        if repo in SPLIT_DOCS:
            enc = lambda s, t=t: [i for e in t.encode_batch(re.split(r"(?<=\n\n)", s), add_special_tokens=False)  # noqa: E731
                                  for i in e.ids]
        else:
            enc = lambda s, t=t: t.encode(s, add_special_tokens=False).ids  # noqa: E731
        encoders.append((label, group, t.get_vocab_size(), enc,
                         lambda ids, t=t: t.decode(ids, skip_special_tokens=False), note))

    rows = []
    for label, group, vocab, enc, dec, note in encoders:
        t0 = time.time()
        r = {"name": label, "group": group, "vocab": vocab, "note": note, "tokens": {}, "fertility": {}, "roundtrip": {}}
        for d, txt in texts.items():
            ids = enc(txt)
            r["tokens"][d] = len(ids)
            r["fertility"][d] = len(ids) / words[d]
            r["roundtrip"][d] = dec(ids) == txt
        r["tokens_pl"] = sum(r["tokens"][d] for d in POLISH)
        r["fertility_pl"] = r["tokens_pl"] / sum(words[d] for d in POLISH)
        rows.append(r)
        print(f"{label:<24} vocab {vocab:>7,}  PL {r['fertility_pl']:.3f}  EN {r['fertility']['angielski']:.3f}  ({time.time()-t0:.0f}s)")

    ref = next(r for r in rows if r["name"] == "TOKENIZATOREX")
    for r in rows:
        r["vs_tokenizatorex_pl"] = r["tokens_pl"] / ref["tokens_pl"]
    rows.sort(key=lambda r: r["fertility_pl"])

    meta = {"words": words, "bytes": {d: len(t.encode()) for d, t in texts.items()}}
    with open(a.out + ".json", "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "rows": rows}, f, indent=2, ensure_ascii=False)
    md = to_markdown(rows, words)
    with open(a.out + ".md", "w", encoding="utf-8") as f:
        f.write(md)
    with open(a.out + ".svg", "w", encoding="utf-8") as f:
        f.write(to_svg(rows))
    print("\n" + md)


def to_markdown(rows, words) -> str:
    head = "| # | tokenizer | słownik | " + " | ".join(ALL_DOMAINS) + " | **PL średnio** | tokenów PL vs TOKENIZATOREX | round-trip |\n"
    head += "|---:|---|---:|" + "---:|" * len(ALL_DOMAINS) + "---:|---:|:-:|\n"
    body = ""
    for i, r in enumerate(rows, 1):
        name = f"**{r['name']}**" if r["group"] == "nasz" else r["name"]
        f = " | ".join(f"{r['fertility'][d]:.2f}" for d in ALL_DOMAINS)
        rt = "✓" if all(r["roundtrip"].values()) else f"✗ ({sum(not v for v in r['roundtrip'].values())}/{len(ALL_DOMAINS)})"
        body += (f"| {i} | {name} | {r['vocab']:,} | {f} | **{r['fertility_pl']:.3f}** | "
                 f"{(r['vs_tokenizatorex_pl'] - 1) * 100:+.0f}% | {rt} |\n")
    foot = "\nWartości w kolumnach dziedzin to fertility (tokeny na słowo, mniej = lepiej). Słowa: " + \
           ", ".join(f"{d} {w:,}" for d, w in words.items()) + ".\n"
    return head + body + foot


def to_svg(rows) -> str:
    """Prosty poziomy wykres słupkowy (bez matplotlib), jasny i ciemny motyw przez CSS."""
    W, bar_h, gap, left, right, top = 760, 20, 6, 210, 70, 46
    H = top + len(rows) * (bar_h + gap) + 30
    mx = max(r["fertility_pl"] for r in rows) * 1.05
    sc = (W - left - right) / mx
    col = {"nasz": "#2563eb", "polski": "#dc2626", "świat": "#6b7280"}
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="system-ui,Segoe UI,sans-serif" font-size="13">',
           "<style>.t{fill:#111827}.m{fill:#6b7280}@media (prefers-color-scheme:dark){.t{fill:#f3f4f6}.m{fill:#9ca3af}}</style>",
           f'<text x="{left}" y="20" class="t" font-weight="600" font-size="15">Tokeny na słowo — polski tekst (7 dziedzin), mniej = lepiej</text>',
           f'<text x="{left}" y="37" class="m" font-size="12">■ niebieski: TOKENIZATOREX · czerwony: modele polskie · szary: modele światowe</text>']
    for i, r in enumerate(rows):
        y = top + i * (bar_h + gap)
        w = r["fertility_pl"] * sc
        weight = ' font-weight="700"' if r["group"] == "nasz" else ""
        out.append(f'<text x="{left - 8}" y="{y + 15}" text-anchor="end" class="t"{weight}>{r["name"]}</text>')
        out.append(f'<rect x="{left}" y="{y}" width="{w:.1f}" height="{bar_h}" rx="3" fill="{col[r["group"]]}"/>')
        out.append(f'<text x="{left + w + 6:.1f}" y="{y + 15}" class="t"{weight}>{r["fertility_pl"]:.2f}</text>')
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    main()
