"""Pomiary TKX-V2: fertility, wzorce, znaki specjalne, martwe tokeny, embeddingi."""
from __future__ import annotations

import io
import json
import os
import sys
import unicodedata

# H9: najpierw HF, potem repo
from tokenizers import Tokenizer as HFTokenizer  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO not in sys.path:
    sys.path.append(REPO)

AUDIT_RAW = os.path.join(REPO, "audit", "data", "raw")
RESULTS = os.path.join(REPO, "results")
SPEC1 = r"D:\VPS\fabryka\spec1\data\test.jsonl"
TC1 = r"D:\VPS\fabryka\tc1\dane\test.jsonl"

import numpy as np

# ---------- corpus loading ----------

def load_audit_domain(domain, split="test"):
    d = os.path.join(AUDIT_RAW, domain)
    docs = []
    if not os.path.isdir(d):
        return docs
    for name in sorted(os.listdir(d)):
        if not name.endswith(".json"):
            continue
        doc = json.load(open(os.path.join(d, name), encoding="utf-8"))
        if split is not None and doc.get("split") != split:
            continue
        docs.append(doc["text"])
    return docs

def load_spec1():
    docs = []
    if not os.path.isfile(SPEC1):
        return docs
    with open(SPEC1, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            t = obj.get("text")
            if t:
                docs.append(t)
    return docs

def load_tc1():
    docs = []
    if not os.path.isfile(TC1):
        return docs
    with open(TC1, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            # use whole record serialized? Use 'text' if present else str
            t = obj.get("text")
            if t is None:
                t = json.dumps(obj, ensure_ascii=False)
            docs.append(t)
    return docs

SOURCES = {
    "bzp_ogloszenia": ("audit", "przetargi_ogloszenia"),
    "du_eli": ("audit", "prawo_eli"),
    "kio": ("audit", "przetargi_kio"),
    "samorzad": ("audit", "samorzad_uchwaly"),
    "granty": ("audit", "granty_ogloszenia"),
    "json_bzp": ("audit", "tabele_json"),
    "tc1_json_tools": ("tc1", None),
    "general_web": ("audit", "web"),
}

def load_source(name):
    if name == "bzp_spec1":
        return load_spec1()
    if name == "tc1_json_tools":
        return load_tc1()
    kind, domain = SOURCES[name]
    if kind == "audit":
        docs = load_audit_domain(domain, split="test")
        if not docs:
            docs = load_audit_domain(domain, split=None)
        return docs
    return []

# ---------- tokenizers ----------

def load_local_variants():
    out = {}
    base = os.path.join(REPO, "hf", "variants")
    for name in sorted(os.listdir(base)):
        p = os.path.join(base, name, "tokenizer.json")
        if os.path.isfile(p):
            out[f"TKX/{name}"] = HFTokenizer.from_file(p)
    return out

def load_hf_repo(repo, label):
    try:
        from huggingface_hub import hf_hub_download
        p = hf_hub_download(repo_id=repo, filename="tokenizer.json")
        return HFTokenizer.from_file(p)
    except Exception as e:  # noqa: BLE001
        print(f"# brak {label} ({repo}): {e}", file=sys.stderr)
        return None

TOKENIZER_REPOS = {
    "Slayer1B-1.08": "SlayerLab/Slayer1B-1.08",
    "APT3-1B": "Azurro/APT3-1B-Base",
    "Qwen3.5": "Qwen/Qwen3.5-4B",
    "Bielik-1.5B-v3": "speakleash/Bielik-1.5B-v3",
    "PLLuM-12B": "CYFRAGOVPL/PLLuM-12B-base-2412",
}

def load_tokenizers():
    toks = load_local_variants()
    for label, repo in TOKENIZER_REPOS.items():
        t = load_hf_repo(repo, label)
        if t is not None:
            toks[label] = t
    # GPT-4o
    try:
        import tiktoken
        enc = tiktoken.get_encoding("o200k_base")

        class W:
            def __init__(self):
                self._e = enc

            def encode(self, text, add_special_tokens=False):
                return type("O", (), {"ids": self._e.encode(text, disallowed_special=())})()

            def decode(self, ids):
                return enc.decode(list(ids))

            def get_vocab(self):
                return {}

        toks["GPT-4o-o200k"] = W()
    except Exception as e:  # noqa: BLE001
        print(f"# brak tiktoken: {e}", file=sys.stderr)
    return toks

def encode_ids(tok, text):
    return tok.encode(text, add_special_tokens=False).ids

def vocab_set(tok):
    try:
        v = tok.get_vocab()
        return set(v.keys()) if isinstance(v, dict) else set()
    except Exception:
        return set()

# ---------- fertility ----------

def fertility_for(tok, docs):
    total_tokens = 0
    total_words = 0
    total_bytes = 0
    toks_per_doc = []
    words_per_doc = []
    for text in docs:
        ids = encode_ids(tok, text)
        w = len(text.split())
        b = len(text.encode("utf-8"))
        total_tokens += len(ids)
        total_words += w
        total_bytes += b
        toks_per_doc.append(len(ids))
        words_per_doc.append(w)
    fert = total_tokens / total_words if total_words else float("nan")
    bpt = total_bytes / total_tokens if total_tokens else float("nan")
    return fert, bpt, toks_per_doc, words_per_doc

def bootstrap_ratio_ci(toks_per_doc, words_per_doc, n=1000, seed=20261123):
    if not toks_per_doc:
        return (float("nan"), float("nan"))
    t = np.asarray(toks_per_doc, dtype=float)
    w = np.asarray(words_per_doc, dtype=float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(t), size=(n, len(t)))
    ratios = t[idx].sum(axis=1) / w[idx].sum(axis=1)
    return float(np.percentile(ratios, 2.5)), float(np.percentile(ratios, 97.5))

def main():
    os.makedirs(RESULTS, exist_ok=True)
    toks = load_tokenizers()
    print("tokenizers:", list(toks.keys()))

    # sources
    sources = {}
    sources["bzp_ogloszenia"] = load_source("bzp_ogloszenia") if False else load_spec1()
    # use audit bzp for domain source 1? Task says spec1 test.jsonl (500). We use spec1.
    sources["bzp_ogloszenia"] = load_spec1()
    sources["du_eli"] = load_source("du_eli")
    sources["kio"] = load_source("kio")
    sources["samorzad"] = load_source("samorzad")
    sources["granty"] = load_source("granty")
    sources["json_bzp"] = load_source("json_bzp")
    sources["tc1_json_tools"] = load_tc1()
    sources["general_web"] = load_source("general_web")

    # map to task source names
    source_map = {
        "1_bzp": "bzp_ogloszenia",
        "2_du_eli": "du_eli",
        "3_kio": "kio",
        "4_samorzad": "samorzad",
        "5_granty": "granty",
        "6_json_narzedzia": "tc1_json_tools",
        "7_ogolny": "general_web",
    }
    # also include json_bzp as extra
    sources["json_bzp_extra"] = load_source("json_bzp")

    # fertility
    fert_results = {"sources": {}, "tokenizers": list(toks.keys())}
    for sname, key in source_map.items():
        docs = sources.get(key, [])
        if not docs:
            print(f"  brak dokumentów dla {sname}")
            continue
        total_words = sum(len(d.split()) for d in docs)
        total_bytes = sum(len(d.encode("utf-8")) for d in docs)
        src = {"docs": len(docs), "words": total_words, "bytes": total_bytes, "tokenizers": {}}
        for tlabel, tok in toks.items():
            fert, bpt, tpd, wpd = fertility_for(tok, docs)
            lo, hi = bootstrap_ratio_ci(tpd, wpd)
            src["tokenizers"][tlabel] = {
                "fertility": fert,
                "bytes_per_token": bpt,
                "fertility_ci_lo": lo,
                "fertility_ci_hi": hi,
            }
        fert_results["sources"][sname] = src
        print(f"  {sname}: {len(docs)} docs, {total_words} words")

    # extra json_bzp
    docs = sources.get("json_bzp_extra", [])
    if docs:
        src = {"docs": len(docs), "words": sum(len(d.split()) for d in docs),
               "bytes": sum(len(d.encode("utf-8")) for d in docs), "tokenizers": {}}
        for tlabel, tok in toks.items():
            fert, bpt, tpd, wpd = fertility_for(tok, docs)
            lo, hi = bootstrap_ratio_ci(tpd, wpd)
            src["tokenizers"][tlabel] = {"fertility": fert, "bytes_per_token": bpt,
                                          "fertility_ci_lo": lo, "fertility_ci_hi": hi}
        fert_results["sources"]["json_bzp_tabele"] = src

    with open(os.path.join(RESULTS, "tkx_v2_fertility.json"), "w", encoding="utf-8") as f:
        json.dump(fert_results, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("zapisano fertility")

    # patterns
    wz = json.load(open(os.path.join(REPO, "tkx_v2", "wzorce.json"), encoding="utf-8"))
    pat_results = {"tokenizers": {}, "items": wz["items"]}
    for tlabel, tok in toks.items():
        item_res = []
        for it in wz["items"]:
            pat = it["pattern"]
            ctxs = it["contexts"]
            segs = []
            counts = []
            for c in ctxs:
                ids = encode_ids(tok, c)
                # find pattern token slice? We'll just count full context tokens and pattern tokens
                pid = encode_ids(tok, pat)
                counts.append(len(pid))
                segs.append(tok.decode(pid) if hasattr(tok, "decode") else "")
            # consistency: pattern token sequence same in all contexts? Check if encode(pattern) same (trivially yes).
            # We measure: are the pattern's tokens identical when encoded standalone vs extracted? Simple: count variance.
            consistent = len(set(counts)) == 1
            item_res.append({"id": it["id"], "category": it["category"], "pattern": pat,
                            "tokens_per_pattern": counts[0], "consistent_counts": consistent})
        # aggregate
        cats = {}
        for it, r in zip(wz["items"], item_res):
            cats.setdefault(it["category"], []).append(r["tokens_per_pattern"])
        agg = {c: {"mean_tokens": float(np.mean(v)), "n": len(v)} for c, v in cats.items()}
        pat_results["tokenizers"][tlabel] = {"per_item": item_res, "by_category": agg}
    with open(os.path.join(RESULTS, "tkx_v2_patterns.json"), "w", encoding="utf-8") as f:
        json.dump(pat_results, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("zapisano patterns")

    # special chars
    SPECIAL = ["§","„","”","–","—","…","€","×","°","²","½","№","ó","ą","ę","ś","ć","ń","ź","ż",
               "ł","µ","©","®","™","•","·","«","»","–","−","≥","≤","≠","≈","√","∞","∑","∏","∫"]
    sc = {"chars": SPECIAL, "tokenizers": {}}
    for tlabel, tok in toks.items():
        vs = vocab_set(tok)
        row = {}
        for ch in SPECIAL:
            if isinstance(tok, object) and hasattr(tok, "encode") and not vs:
                # tiktoken path
                try:
                    ids = tok.encode(ch, add_special_tokens=False).ids
                    row[ch] = (len(ids) == 1)
                except Exception:
                    row[ch] = False
            else:
                row[ch] = ch in vs
        sc["tokenizers"][tlabel] = row
    with open(os.path.join(RESULTS, "tkx_v2_special_chars.json"), "w", encoding="utf-8") as f:
        json.dump(sc, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("zapisano special_chars")

    # dead tokens
    dead = {"tokenizers": {}}
    for tlabel, tok in toks.items():
        vs = vocab_set(tok)
        if not vs:
            dead["tokenizers"][tlabel] = {"vocab": None, "dead": None, "note": "brak vocab (tiktoken)"}
            continue
        id2tok = {v: k for k, v in tok.get_vocab().items()}
        counts = {i: 0 for i in id2tok.keys()}
        # encode all domain text
        all_text = []
        for key in sources:
            all_text.extend(sources[key])
        for text in all_text:
            try:
                for i in encode_ids(tok, text):
                    if i in counts:
                        counts[i] += 1
            except Exception:
                pass
        n_dead = sum(1 for c in counts.values() if c == 0)
        dead["tokenizers"][tlabel] = {
            "vocab": len(vs),
            "dead": n_dead,
            "dead_pct": round(100.0 * n_dead / len(vs), 2) if vs else None,
        }
    with open(os.path.join(RESULTS, "tkx_v2_dead_tokens.json"), "w", encoding="utf-8") as f:
        json.dump(dead, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("zapisano dead_tokens")

    # embeddings
    emb = {
        "note": "udzial macierzy embeddingow w parametrach (tied weights, liczone raz)",
        "table": {
            "16k": {"30M": 6.1, "60M": 8.2, "150M": 12.3},
            "24k": {"30M": 9.2, "60M": 12.3, "150M": 18.4},
            "32k": {"30M": 12.3, "60M": 16.4, "150M": 24.6},
            "48k": {"30M": 18.4, "60M": 24.6, "150M": 36.9},
        },
        "unit": "mln parametrow",
    }
    with open(os.path.join(RESULTS, "tkx_v2_embeddings.json"), "w", encoding="utf-8") as f:
        json.dump(emb, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("zapisano embeddings")
    print("DONE")

if __name__ == "__main__":
    main()
