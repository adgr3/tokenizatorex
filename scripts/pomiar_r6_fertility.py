"""R6: fertility z 95% CI, efektywność Rényiego i odsetek słów > 1 token.

Zakres: 8 źródeł v2.0, tokenizery: V0-32k, V0J2-32k, TOKENIZATOREX-base-32k,
Slayer1B-1.08, APT3-1B, Bielik-1.5B-v3, GPT-4o (o200k).

Rényi: alpha = 2.5 (jak TokEval; wyższe alpha mocniej karze ogon rozkładu).
Efektywność = H_alpha / log2(|V|), gdzie H_alpha = 1/(1-alpha) * log2(sum p_i^alpha),
p_i z częstości tokenów na źródle, |V| = rozmiar słownika tokenizera (z dodanymi).

Wynik: results/tkx_v2_r6_measure.json
"""
from __future__ import annotations

import glob
import json
import os
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "results"
sys.path.insert(0, str(REPO))

from tokenizers import Tokenizer  # noqa: E402

TKX_DANE = Path(os.environ.get("TKX_DANE", "data"))
SPEC1 = TKX_DANE / "spec1" / "test.jsonl"
TC1 = TKX_DANE / "tc1" / "test.jsonl"
AUDIT_RAW = REPO / "audit" / "data" / "raw"
ALPHA = 2.5
SEED = 20261123


def load_jsonl_text(path: Path):
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            o = json.loads(line)
            t = o.get("text")
            if t is None:
                t = json.dumps(o, ensure_ascii=False)
            out.append(t)
    return out


def load_audit(domain: str):
    docs = []
    for p in sorted((AUDIT_RAW / domain).glob("*.json")):
        d = json.load(open(p, encoding="utf-8"))
        if d.get("split") == "test":
            docs.append(d["text"])
    if not docs:
        for p in sorted((AUDIT_RAW / domain).glob("*.json")):
            d = json.load(open(p, encoding="utf-8"))
            docs.append(d["text"])
    return docs


SOURCES = {
    "1_bzp": ("BZP (ogłoszenia)", lambda: load_jsonl_text(SPEC1)),
    "2_du_eli": ("Dz.U. 2026 ELI", lambda: load_audit("prawo_eli")),
    "3_kio": ("KIO", lambda: load_audit("przetargi_kio")),
    "4_samorzad": ("Samorząd (uchwały)", lambda: load_audit("samorzad_uchwaly")),
    "5_granty": ("Granty", lambda: load_audit("granty_ogloszenia")),
    "6_json_narzedzia": ("JSON narzędzi (tc1)", lambda: load_jsonl_text(TC1)),
    "7_ogolny": ("Kontrola ogólna (HPLT web)", lambda: load_audit("web")),
    "json_bzp_tabele": ("JSON BZP (tabele, extra)", lambda: load_audit("tabele_json")),
}


def find_snapshot(repo_dir: str) -> Path | None:
    roots = [Path.home() / ".cache" / "huggingface" / "hub",
             Path(r"D:\VPS\cache\huggingface\hub")]
    for root in roots:
        snaps = root / repo_dir / "snapshots"
        if not snaps.is_dir():
            continue
        for p in sorted(snaps.glob("*/tokenizer.json")):
            return p
    return None


def load_hf(path: Path) -> Tokenizer:
    return Tokenizer.from_file(str(path))


class GPT4o:
    def __init__(self):
        import tiktoken
        self.enc = tiktoken.get_encoding("o200k_base")

    def encode(self, text):
        return self.enc.encode(text, disallowed_special=())

    def offsets(self, text):
        ids = self.encode(text)
        out = []
        pos = 0
        for i in ids:
            b = self.enc.decode_single_token_bytes(i)
            out.append((pos, pos + len(b)))
            pos += len(b)
        return out

    @property
    def vocab_size(self):
        return self.enc.n_vocab


def word_spans(text: str):
    out = []
    i, n = 0, len(text)
    while i < n:
        while i < n and text[i].isspace():
            i += 1
        if i >= n:
            break
        a = i
        while i < n and not text[i].isspace():
            i += 1
        out.append((a, i))
    return out


def split_words_offsets(text: str, offsets, char_spans):
    """Ile słów jest pokrytych przez > 1 token (offset w znakach)."""
    if not offsets:
        return 0, len(char_spans)
    split = 0
    j = 0
    nt = len(offsets)
    for a, b in char_spans:
        while j < nt and offsets[j][1] <= a:
            j += 1
        k = j
        covering = 0
        while k < nt and offsets[k][0] < b:
            if offsets[k][1] > a:
                covering += 1
            k += 1
        if covering > 1:
            split += 1
    return split, len(char_spans)


def renyi_efficiency(counts: np.ndarray, vocab_size: int) -> float:
    total = counts.sum()
    if total <= 0 or vocab_size <= 1:
        return float("nan")
    p = counts[counts > 0] / total
    h = (1.0 / (1.0 - ALPHA)) * np.log2(np.sum(p ** ALPHA))
    return float(h / np.log2(vocab_size))


def bootstrap_ci(toks, words, n=1000, seed=SEED):
    t = np.asarray(toks, dtype=float)
    w = np.asarray(words, dtype=float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(t), size=(n, len(t)))
    r = t[idx].sum(axis=1) / w[idx].sum(axis=1)
    return float(np.percentile(r, 2.5)), float(np.percentile(r, 97.5))


def measure(tok, is_gpt: bool, docs):
    toks_per_doc, words_per_doc = [], []
    split_words = total_words = 0
    counts: dict[int, int] = {}
    total_tokens = 0
    for text in docs:
        if is_gpt:
            ids = tok.encode(text)
            offs = tok.offsets(text)
        else:
            enc = tok.encode(text, add_special_tokens=False)
            ids = enc.ids
            offs = list(enc.offsets)
        toks_per_doc.append(len(ids))
        words_per_doc.append(len(text.split()))
        total_tokens += len(ids)
        for i in ids:
            counts[i] = counts.get(i, 0) + 1
        sp, tw = split_words_offsets(text, offs, word_spans(text))
        split_words += sp
        total_words += tw
    words = sum(words_per_doc)
    arr = np.fromiter(counts.values(), dtype=np.int64)
    vocab_size = tok.vocab_size if is_gpt else tok.get_vocab_size(with_added_tokens=True)
    lo, hi = bootstrap_ci(toks_per_doc, words_per_doc)
    return {
        "docs": len(docs),
        "tokens": total_tokens,
        "words": words,
        "fertility": total_tokens / words if words else float("nan"),
        "fertility_ci_lo": lo,
        "fertility_ci_hi": hi,
        "renyi_alpha": ALPHA,
        "renyi_efficiency": renyi_efficiency(arr, vocab_size),
        "vocab_size": int(vocab_size),
        "split_words": split_words,
        "split_words_pct": 100.0 * split_words / total_words if total_words else float("nan"),
    }


def main() -> None:
    sources = {k: (name, fn()) for k, (name, fn) in SOURCES.items()}

    toks = {
        "V0-32k": (load_hf(REPO / "hf/variants/V0-32k/tokenizer.json"), False),
        "V0J2-32k": (load_hf(REPO / "hf/variants/V0J2-32k/tokenizer.json"), False),
        "TOKENIZATOREX-base-32k": (load_hf(REPO / "hf/tokenizatorex-base-32k/tokenizer.json"), False),
        "Slayer1B-1.08": (load_hf(find_snapshot("models--SlayerLab--Slayer1B-1.08")), False),
        "APT3-1B": (load_hf(find_snapshot("models--Azurro--APT3-1B-Base")), False),
        "Bielik-1.5B-v3": (load_hf(find_snapshot("models--speakleash--Bielik-1.5B-v3")), False),
        "GPT-4o-o200k": (GPT4o(), True),
    }

    out = {
        "meta": {
            "script": "scripts/pomiar_r6_fertility.py",
            "alpha": ALPHA,
            "alpha_justification": "alpha=2,5 jak w TokEval (Zouhar i in.); wyższe alpha "
                                   "mocniej karze ogon rozkładu tokenów",
            "renyi_definition": "H_alpha=1/(1-alpha)*log2(sum p_i^alpha); "
                                "efektywność=H_alpha/log2(|V|)",
            "ci": "bootstrap 1000x po dokumentach, seed 20261123",
            "split_words_definition": "słowo (\\S+) pokryte przez >1 token na offsetach; "
                                      "token przechodzący przez granicę słowa sam nie dzieli słowa",
        },
        "sources": {k: {"name": v[0], "docs": len(v[1])} for k, v in sources.items()},
        "results": {},
    }

    for tname, (tok, is_gpt) in toks.items():
        print("tokenizer", tname, flush=True)
        out["results"][tname] = {}
        for sid, (_name, docs) in sources.items():
            m = measure(tok, is_gpt, docs)
            out["results"][tname][sid] = m
            print(f"  {sid}: fert {m['fertility']:.3f} renyi {m['renyi_efficiency']:.3f} "
                  f"split {m['split_words_pct']:.2f}%", flush=True)

    comp = {}
    for a in toks:
        comp[a] = {}
        for b in toks:
            if a == b:
                continue
            lower = sum(1 for s in sources
                        if out["results"][a][s]["fertility"]
                        < out["results"][b][s]["fertility"])
            ta = sum(out["results"][a][s]["tokens"] for s in sources)
            tb = sum(out["results"][b][s]["tokens"] for s in sources)
            reduction = (1 - ta / tb) * 100
            comp[a][b] = {
                "sources_lower": lower,
                "sources_total": len(sources),
                "tokens_reduction_pct": reduction,
                "tokens_reduction_abs_pct": abs(reduction),
            }
    out["comparison"] = comp
    out["meta"]["base_check"] = {
        "file": "tokenizers/tokenizatorex-base-32k.json",
        "transition": 31999,
        "stage2_merges": 0,
        "same_training": True,
        "note": "ten sam etap 1; 0 mergeów etapu 2 "
                "(log results/train-bpe-32k.log: etap2=0)",
    }

    with open(RESULTS / "tkx_v2_r6_measure.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("zapisano results/tkx_v2_r6_measure.json")


if __name__ == "__main__":
    main()
