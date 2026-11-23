"""Pomiary TKX-V21-JSON.

Dwa etapy (test JSON liczymy raz, po wyborze wariantu):

  python tkx_v21/measure_v21.py --stage dev    # JSON dev + polska bramka
  python tkx_v21/wybierz.py                    # reguła wyboru -> selection.json
  python tkx_v21/measure_v21.py --stage test   # JSON test, wzorce, round-trip, martwe

Wyniki: results/tkx_v21_*.json. Każda liczba w raporcie ma pochodzić z tych plików.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from tokenizers import Tokenizer as HFTokenizer  # noqa: E402
import numpy as np  # noqa: E402

RESULTS = os.path.join(REPO, "results")
AUDIT_RAW = os.path.join(REPO, "audit", "data", "raw")
TC1_DIR = r"D:\VPS\fabryka\tc1\dane"
SPEC1 = r"D:\VPS\fabryka\spec1\data\test.jsonl"
DATA = os.path.join(REPO, "tkx_v21", "dane")
SEED = 20261123

POLISH = {
    "bzp_ogloszenia": "spec1",
    "du_eli": "prawo_eli",
    "kio": "przetargi_kio",
    "samorzad": "samorzad_uchwaly",
    "granty": "granty_ogloszenia",
    "json_bzp_tabele": "tabele_json",
    "general_web": "web",
}


# ---------- dane ----------

def _load_jsonl(path):
    docs = []
    if not os.path.isfile(path):
        return docs
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                docs.append(json.loads(line))
    return docs


def load_tc1(split):
    docs = []
    for obj in _load_jsonl(os.path.join(TC1_DIR, f"{split}.jsonl")):
        t = obj.get("text")
        if t is None:
            t = json.dumps(obj, ensure_ascii=False)
        docs.append(t)
    return docs


def load_tc1_json_only(split):
    """Tylko tury z wywołaniem narzędzia i odpowiedzią narzędzia (czysty JSON)."""
    docs = []
    for obj in _load_jsonl(os.path.join(TC1_DIR, f"{split}.jsonl")):
        parts = []
        for m in obj.get("wiadomosci", []):
            text = (m.get("tresc") or "").strip()
            if not text:
                continue
            if m.get("rola") == "asystent" and "<tool_call>" in text:
                parts.append(text)
            elif m.get("rola") == "narzedzie":
                parts.append(text)
        if parts:
            docs.append("\n".join(parts))
    return docs


def load_generic(split):
    return [o["text"] for o in _load_jsonl(os.path.join(DATA, f"json_generic_heldout_{split}.jsonl"))]


def load_spec1():
    docs = []
    if not os.path.isfile(SPEC1):
        return docs
    with open(SPEC1, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                t = json.loads(line).get("text")
                if t:
                    docs.append(t)
    return docs


def load_audit(domain):
    d = os.path.join(AUDIT_RAW, domain)
    docs = []
    if not os.path.isdir(d):
        return docs
    for name in sorted(os.listdir(d)):
        if not name.endswith(".json"):
            continue
        doc = json.load(open(os.path.join(d, name), encoding="utf-8"))
        if doc.get("split") != "test":
            continue
        docs.append(doc["text"])
    return docs


def load_polish():
    out = {}
    for label, src in POLISH.items():
        out[label] = load_spec1() if src == "spec1" else load_audit(src)
    return out


# ---------- tokenizery ----------

def load_tokenizers():
    toks = {}
    paths = {
        "V0R-32k": os.path.join(REPO, "tkx_v21", "hf", "V0R-32k", "tokenizer.json"),
        "V0-32k": os.path.join(REPO, "hf", "variants", "V0-32k", "tokenizer.json"),
        "V0J2-32k": os.path.join(REPO, "hf", "variants", "V0J2-32k", "tokenizer.json"),
        "V0J5-32k": os.path.join(REPO, "hf", "variants", "V0J5-32k", "tokenizer.json"),
        "V0J10-32k": os.path.join(REPO, "hf", "variants", "V0J10-32k", "tokenizer.json"),
        "V0J5S-32k": os.path.join(REPO, "hf", "variants", "V0J5S-32k", "tokenizer.json"),
    }
    for label, p in paths.items():
        if os.path.isfile(p):
            toks[label] = HFTokenizer.from_file(p)
        else:
            print(f"# brak {label}: {p}", file=sys.stderr)
    try:
        from huggingface_hub import hf_hub_download
        p = hf_hub_download(repo_id="SlayerLab/Slayer1B-1.08", filename="tokenizer.json")
        toks["Slayer1B-1.08"] = HFTokenizer.from_file(p)
    except Exception as e:  # noqa: BLE001
        print(f"# brak Slayera: {e}", file=sys.stderr)
    try:
        import tiktoken
        enc = tiktoken.get_encoding("o200k_base")

        class TiktokenWrap:
            name = "GPT-4o-o200k"

            def encode(self, text, add_special_tokens=False):  # noqa: ARG002
                ids = enc.encode(text, disallowed_special=())
                return type("Enc", (), {"ids": ids, "tokens": []})()

            def decode(self, ids):
                return enc.decode(list(ids))

            def get_vocab(self):
                return {}

            def get_added_vocab(self):
                return {}

        toks["GPT-4o-o200k"] = TiktokenWrap()
    except Exception as e:  # noqa: BLE001
        print(f"# brak tiktoken: {e}", file=sys.stderr)
    return toks


def ids(tok, text):
    return list(tok.encode(text, add_special_tokens=False).ids)


# ---------- metryki ----------

def measure_source(tok, docs):
    tpd, wpd = [], []
    bytes_total = 0
    for text in docs:
        n = len(ids(tok, text))
        w = len(text.split())
        tpd.append(n)
        wpd.append(w)
        bytes_total += len(text.encode("utf-8"))
    total_t = int(sum(tpd))
    total_w = int(sum(wpd))
    fert = total_t / total_w if total_w else float("nan")
    return {
        "docs": len(docs),
        "words": total_w,
        "tokens": total_t,
        "bytes": bytes_total,
        "tokens_per_doc": total_t / len(docs) if docs else float("nan"),
        "fertility": fert,
        "bytes_per_token": bytes_total / total_t if total_t else float("nan"),
        "ci": bootstrap_ci(tpd, wpd),
        "_tpd": tpd,
        "_wpd": wpd,
    }


def bootstrap_ci(tpd, wpd, n=1000, seed=SEED):
    if not tpd:
        return [float("nan"), float("nan")]
    t = np.asarray(tpd, dtype=float)
    w = np.asarray(wpd, dtype=float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(t), size=(n, len(t)))
    ratios = t[idx].sum(axis=1) / np.maximum(w[idx].sum(axis=1), 1)
    return [float(np.percentile(ratios, 2.5)), float(np.percentile(ratios, 97.5))]


def public(row):
    return {k: v for k, v in row.items() if not k.startswith("_")}


def combined(rows):
    t = sum(r["tokens"] for r in rows)
    w = sum(r["words"] for r in rows)
    return {"docs": sum(r["docs"] for r in rows), "words": w, "tokens": t,
            "fertility": t / w if w else float("nan")}


# ---------- etapy ----------

def stage_dev(toks):
    out = {"stage": "dev", "seed": SEED, "tokenizers": {}, "sources": {}}
    # JSON dev
    json_sources = {"tc1_dev": load_tc1("dev"), "json_generic_dev": load_generic("dev"),
                    "tc1_dev_json_only": load_tc1_json_only("dev")}
    for sname, docs in json_sources.items():
        out["sources"][sname] = {"docs": len(docs), "words": sum(len(d.split()) for d in docs),
                                 "tokenizers": {}}
        for label, tok in toks.items():
            row = measure_source(tok, docs)
            out["sources"][sname]["tokenizers"][label] = public(row)
        print(f"  dev {sname}: {len(docs)} dok.")
    # polska bramka
    polish = load_polish()
    for sname, docs in polish.items():
        out["sources"][sname] = {"docs": len(docs), "words": sum(len(d.split()) for d in docs),
                                 "tokenizers": {}}
        for label, tok in toks.items():
            out["sources"][sname]["tokenizers"][label] = public(measure_source(tok, docs))
        print(f"  polski {sname}: {len(docs)} dok.")
    # § przez encode
    out["section_sign"] = {}
    for label, tok in toks.items():
        out["section_sign"][label] = {"tokens": len(ids(tok, "§")),
                                      "one_token": len(ids(tok, "§")) == 1}
    # łączny dev JSON (reguła: tc1 dev + held-out dev) + dodatkowo czysty JSON tc1
    for label in toks:
        rows = [out["sources"][s]["tokenizers"][label]
                for s in ("tc1_dev", "json_generic_dev")]
        rows_only = [out["sources"][s]["tokenizers"][label]
                     for s in ("tc1_dev_json_only", "json_generic_dev")]
        out["tokenizers"][label] = {
            "json_dev_combined": combined(rows),
            "json_dev_json_only_combined": combined(rows_only),
        }
    ranking = sorted(out["tokenizers"], key=lambda k: out["tokenizers"][k]["json_dev_combined"]["fertility"])
    out["ranking_json_dev"] = ranking
    with open(os.path.join(RESULTS, "tkx_v21_dev.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("zapisano results/tkx_v21_dev.json")
    return out


def stage_test(toks):
    out = {"stage": "test", "seed": SEED, "tokenizers": {}, "sources": {}}
    json_sources = {"tc1_test": load_tc1("test"),
                    "json_generic_test": load_generic("test"),
                    "tc1_test_json_only": load_tc1_json_only("test")}
    for sname, docs in json_sources.items():
        out["sources"][sname] = {"docs": len(docs), "words": sum(len(d.split()) for d in docs),
                                 "tokenizers": {}}
        for label, tok in toks.items():
            out["sources"][sname]["tokenizers"][label] = public(measure_source(tok, docs))
        print(f"  test {sname}: {len(docs)} dok.")
    for label in toks:
        rows = [out["sources"][s]["tokenizers"][label]
                for s in ("tc1_test", "json_generic_test")]
        rows_only = [out["sources"][s]["tokenizers"][label]
                     for s in ("tc1_test_json_only", "json_generic_test")]
        out["tokenizers"][label] = {
            "json_test_combined": combined(rows),
            "json_test_json_only_combined": combined(rows_only),
        }
    # wzorce
    wz = json.load(open(os.path.join(REPO, "tkx_v2", "wzorce.json"), encoding="utf-8"))
    pat = {"tokenizers": {}, "items": wz["items"]}
    for label, tok in toks.items():
        per_item = []
        for it in wz["items"]:
            enc = tok.encode(it["pattern"], add_special_tokens=False)
            row = {"id": it["id"], "category": it["category"], "pattern": it["pattern"],
                   "tokens": len(enc.ids)}
            if getattr(enc, "tokens", None):
                row["segmentation"] = list(enc.tokens)
            per_item.append(row)
        cats = {}
        for it, r in zip(wz["items"], per_item):
            cats.setdefault(it["category"], []).append(r["tokens"])
        pat["tokenizers"][label] = {
            "per_item": per_item,
            "by_category": {c: {"mean_tokens": float(np.mean(v)), "n": len(v)}
                            for c, v in cats.items()},
            "json_10_mean_tokens": float(np.mean([r["tokens"] for r, it in zip(per_item, wz["items"])
                                                  if it["category"] == "json_tool_calls"])),
        }
    with open(os.path.join(RESULTS, "tkx_v21_wzorce.json"), "w", encoding="utf-8") as f:
        json.dump(pat, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("zapisano results/tkx_v21_wzorce.json")

    # round-trip: 100 dok. z każdego źródła, dopełnione do 700 (z powtórzeniami)
    polish = load_polish()
    cases, seen = [], set()
    for sname, docs in polish.items():
        for d in docs[:100]:
            cases.append((sname, d))
            seen.add(d)
    for sname, docs in polish.items():
        for d in docs:
            if len(cases) >= 700:
                break
            if d not in seen:
                cases.append((sname, d))
                seen.add(d)
    rt = {"cases": len(cases), "unique_texts": len(seen), "tokenizers": {}}
    for label, tok in toks.items():
        bad, bad_nfd = [], []
        for sname, text in cases:
            ok = tok.decode(ids(tok, text)) == text
            if not ok:
                bad.append({"source": sname, "chars": len(text)})
                if text != __import__("unicodedata").normalize("NFC", text):
                    bad_nfd.append({"source": sname, "chars": len(text)})
        rt["tokenizers"][label] = {"cases": len(cases), "bad": len(bad),
                                   "bad_nfd": len(bad_nfd),
                                   "ok": len(bad) == 0,
                                   "examples_bad": bad[:5]}
    with open(os.path.join(RESULTS, "tkx_v21_roundtrip.json"), "w", encoding="utf-8") as f:
        json.dump(rt, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("zapisano results/tkx_v21_roundtrip.json")

    # tokeny specjalne
    special_names = ["<|system|>", "<|uzytkownik|>", "<|asystent|>", "<|narzedzie|>",
                     "<tool_call>", "</tool_call>"]
    sp = {"names": special_names, "tokenizers": {}}
    for label, tok in toks.items():
        sp["tokenizers"][label] = {
            name: {"tokens": len(ids(tok, name)), "one_token": len(ids(tok, name)) == 1}
            for name in special_names
        }
    with open(os.path.join(RESULTS, "tkx_v21_special_tokens.json"), "w", encoding="utf-8") as f:
        json.dump(sp, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("zapisano results/tkx_v21_special_tokens.json")

    # martwe tokeny na korpusie oceny (7 polskich + 2 JSON test)
    dead = {"tokenizers": {}}
    all_docs = [d for docs in polish.values() for d in docs]
    all_docs += json_sources["tc1_test"] + json_sources["json_generic_test"]
    for label, tok in toks.items():
        vocab = tok.get_vocab() if hasattr(tok, "get_vocab") else {}
        if not vocab:
            dead["tokenizers"][label] = {"vocab": None, "dead": None,
                                         "note": "brak get_vocab (tiktoken)"}
            continue
        added = set()
        try:
            added = set(tok.get_added_vocab().values())
        except Exception:  # noqa: BLE001
            pass
        counts = {i: 0 for i in set(vocab.values())}
        for text in all_docs:
            for i in ids(tok, text):
                if i in counts:
                    counts[i] += 1
        dead_n = sum(1 for i, c in counts.items() if c == 0 and i not in added)
        considered = len([i for i in counts if i not in added])
        dead["tokenizers"][label] = {
            "vocab": len(vocab), "considered": considered, "dead": dead_n,
            "dead_pct": 100.0 * dead_n / considered if considered else None,
            "special_excluded": len(added),
        }
    with open(os.path.join(RESULTS, "tkx_v21_dead_tokens.json"), "w", encoding="utf-8") as f:
        json.dump(dead, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("zapisano results/tkx_v21_dead_tokens.json")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["dev", "test"], required=True)
    a = ap.parse_args()
    os.makedirs(RESULTS, exist_ok=True)
    toks = load_tokenizers()
    print("tokenizery:", list(toks))
    if a.stage == "dev":
        stage_dev(toks)
    else:
        out = stage_test(toks)
        with open(os.path.join(RESULTS, "tkx_v21_test.json"), "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print("zapisano results/tkx_v21_test.json")


if __name__ == "__main__":
    main()
