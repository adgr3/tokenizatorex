"""Pomiary TKX-ZOO — tokenizery polskich modeli na źródłach v2.

Uruchomienie (PYTHONHASHSEED musi być ustawiony przed startem interpretera):
    $env:PYTHONHASHSEED=0
    python tkx_zoo/measure.py

Zasady: fertility = suma tokenów / suma słów (str.split()), bootstrap 1000×
po dokumentach, seed 20261123, encode(..., add_special_tokens=False).
Liczby dla V0/V0J2/Slayera/Bielika 1.5B/APT3/GPT-4o są KOPIOWANE z istniejących
plików results/tkx_v2_*.json i results/tkx_v21_*.json — bez przeliczania.
Tylko pliki tokenizera są pobierane (nigdy wagi). Token HF nigdy nie jest wypisywany.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import unicodedata
from types import SimpleNamespace

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

from huggingface_hub import HfApi, hf_hub_download, get_token  # noqa: E402
from tokenizers import Tokenizer as HFTokenizer  # noqa: E402
import numpy as np  # noqa: E402

from tkx_zoo import formaty  # noqa: E402

RESULTS = os.path.join(REPO, "results")
ZOO = os.path.join(REPO, "tkx_zoo")
HF_DIR = os.path.join(ZOO, "hf")
AUDIT_RAW = os.path.join(REPO, "audit", "data", "raw")
SPEC1 = r"D:\VPS\fabryka\spec1\data\test.jsonl"
ZBORB = r"D:\VPS\fabryka\spec1\data\zbiorB.jsonl"
TC1 = r"D:\VPS\fabryka\tc1\dane\test.jsonl"
GENERIC_TEST = os.path.join(REPO, "tkx_v21", "dane", "json_generic_heldout_test.jsonl")
SEED = 20261123
BASE_COMMIT = "f12fc2c6bc35881887e57d76a9f5dd6284811ccf"

# ---------------------------------------------------------------- dane (jak w v2)


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


def _load_jsonl_text(path):
    docs = []
    if not os.path.isfile(path):
        return docs
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            t = obj.get("text")
            if t is None:
                t = json.dumps(obj, ensure_ascii=False)
            if t:
                docs.append(t)
    return docs


def load_sources():
    """Kolejność źródeł v2 zachowana dokładnie jak w results/tkx_v2_fertility.json."""
    src = {
        "1_bzp": _load_jsonl_text(SPEC1),
        "2_du_eli": load_audit_domain("prawo_eli"),
        "3_kio": load_audit_domain("przetargi_kio"),
        "4_samorzad": load_audit_domain("samorzad_uchwaly"),
        "5_granty": load_audit_domain("granty_ogloszenia"),
        "6_json_narzedzia": _load_jsonl_text(TC1),
        "7_ogolny": load_audit_domain("web"),
        "json_bzp_tabele": load_audit_domain("tabele_json"),
    }
    src["granty_149"] = _load_jsonl_text(ZBORB)
    src["json_generic_heldout_test"] = _load_jsonl_text(GENERIC_TEST)
    order = ["1_bzp", "2_du_eli", "3_kio", "4_samorzad", "5_granty",
             "6_json_narzedzia", "7_ogolny", "json_bzp_tabele",
             "granty_149", "json_generic_heldout_test"]
    return {k: src[k] for k in order}, order


V2_CORPUS = {"1_bzp", "2_du_eli", "3_kio", "4_samorzad", "5_granty",
             "6_json_narzedzia", "7_ogolny", "json_bzp_tabele"}
ROUNDTRIP_SOURCES = ["1_bzp", "2_du_eli", "3_kio", "4_samorzad", "5_granty",
                     "json_bzp_tabele", "7_ogolny"]

# ---------------------------------------------------------------- tokenizery

NEW = [
    ("PLLuM-4B", "CYFRAGOVPL/PLLuM-4B-instruct-2512",
     "PLLuM 4B (instruct, 2512); tokenizer rozszerzony względem Gemma 3"),
    ("PLLuM-8B", "CYFRAGOVPL/Llama-PLLuM-8B-instruct-2512",
     "Llama-PLLuM 8B (instruct, 2512); baza Llama 3.1 niedostępna (gated)"),
    ("PLLuM-12B", "CYFRAGOVPL/PLLuM-12B-instruct-2512",
     "PLLuM 12B (instruct, 2512); tokenizer rozszerzony względem Mistral Nemo"),
    ("Bielik-11B-v3.1", "speakleash/Bielik-11B-v3.1-Instruct",
     "Bielik 11B v3.1 Instruct (tokenizer Llama/APT4)"),
    ("Bielik-4.5B-v3", "speakleash/Bielik-4.5B-v3",
     "Bielik 4.5B v3 (tokenizer inny niż 11B v3.1)"),
    ("Aster-0.5B", "OrisTeam/Aster-0.5B", "Aster 0.5B (PM: dodać do zoo)"),
    ("EuroLLM-1.7B", "utter-project/EuroLLM-1.7B-Instruct", "EuroLLM 1.7B Instruct (najmniejszy)"),
    ("Mistral-Nemo", "mistralai/Mistral-Nemo-Base-2407", "Mistral Nemo Base 2407 (baza PLLuM 12B)"),
    ("Gemma-3-4B", "google/gemma-3-4b-it", "Gemma 3 4B IT (baza PLLuM 4B)"),
]

UNAVAILABLE = [
    ("Llama-3.1-8B", "meta-llama/Llama-3.1-8B",
     "baza niedostępna (gated, czeka na zatwierdzenie Meta)"),
]

REFERENCE_LOCAL = [
    ("V0-32k", os.path.join(REPO, "hf", "variants", "V0-32k", "tokenizer.json"),
     "wyniki fertility z results/tkx_v2_fertility.json; plik lokalny, bez pobierania"),
    ("V0J2-32k", os.path.join(REPO, "hf", "variants", "V0J2-32k", "tokenizer.json"),
     "wyniki fertility z results/tkx_v21_*.json; plik lokalny, bez pobierania"),
]

REFERENCE_HF = [
    ("Slayer-v6", "SlayerLab/Slayer1B-1.08", "wyniki fertility z istniejących plików (Slayer1B-1.08)"),
    ("Bielik-1.5B-v3", "speakleash/Bielik-1.5B-v3", "wyniki fertility z results/tkx_v2_fertility.json"),
    ("APT3-1B", "Azurro/APT3-1B-Base", "wyniki fertility z results/tkx_v2_fertility.json"),
]

# PR #29 slayerlabs/tokenizer — git fetch origin pull/29/head (FETCH_HEAD=0cf4eff…)
DANIELK_COMMIT = "0cf4eff0e622d23cd38a6c6d190dbba5f5e0fec8"
DANIELK = [
    ("DanielK-t1-pl-polish-32k", "DanielK/artifacts/bpe2_t1_pl_polish_32k/tokenizer.json",
     "PR https://github.com/slayerlabs/tokenizer/pull/29, t1 pl_polish 32k"),
    ("DanielK-t2-pl-cnc-32k", "DanielK/artifacts/bpe2_t2_pl_cnc_32k/tokenizer.json",
     "PR https://github.com/slayerlabs/tokenizer/pull/29, t2 pl_cnc 32k"),
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(repo, label, note):
    """Tylko pliki tokenizera, przięta rewizja (= sha głównej gałęzi w chwili pobrania)."""
    api = HfApi(token=get_token())
    info = api.model_info(repo)
    entry = {
        "status": "ok", "repo": repo, "revision": info.sha, "note": note,
        "gated": getattr(info, "gated", None), "files": [],
    }
    os.makedirs(os.path.join(HF_DIR, label), exist_ok=True)
    for fn in ("tokenizer.json", "tokenizer_config.json"):
        if not any(s.rfilename == fn for s in info.siblings):
            continue
        cached = hf_hub_download(repo_id=repo, filename=fn, revision=info.sha)
        dest = os.path.join(HF_DIR, label, fn)
        shutil.copyfile(cached, dest)
        entry["files"].append({
            "name": fn, "sha256": sha256(dest),
            "path": os.path.relpath(dest, REPO).replace("\\", "/"),
        })
    return entry


def local_entry(path, note):
    return {
        "status": "existing", "path": os.path.relpath(path, REPO).replace("\\", "/"),
        "revision": None, "note": note, "files": [{"name": "tokenizer.json", "sha256": sha256(path)}],
    }


class TiktokenWrap:
    """GPT-4o o200k — bez plików z HF, liczony wyłącznie z istniejących wyników."""

    name = "GPT-4o-o200k"

    def __init__(self, enc):
        self._enc = enc

    def encode(self, text, add_special_tokens=False):  # noqa: ARG002
        ids = self._enc.encode(text, disallowed_special=())
        return SimpleNamespace(ids=ids, tokens=[self._enc.decode([i]) for i in ids])

    def decode(self, ids):
        return self._enc.decode(list(ids))

    def get_vocab(self):
        return {}

    def get_added_vocab(self):
        return {}

    @property
    def n_vocab(self):
        return self._enc.n_vocab


def build_tokenizers():
    toks, manifest = {}, {}
    for label, repo, note in NEW:
        try:
            entry = fetch(repo, label, note)
            p = os.path.join(REPO, entry["files"][0]["path"])
            toks[label] = HFTokenizer.from_file(p)
        except Exception as e:  # noqa: BLE001
            print(f"# brak {label}: {type(e).__name__} {str(e).splitlines()[0][:120]}", file=sys.stderr)
            entry = {"status": "unavailable", "repo": repo, "revision": None,
                     "note": f"{note}; nie udało się pobrać: {type(e).__name__}", "files": []}
        manifest[label] = entry
    for label, rel, note in DANIELK:
        p = os.path.join(REPO, "tkx_zoo", "hf", label, "tokenizer.json")
        if os.path.isfile(p):
            toks[label] = HFTokenizer.from_file(p)
            manifest[label] = {
                "status": "ok", "repo": "https://github.com/slayerlabs/tokenizer/pull/29",
                "revision": DANIELK_COMMIT, "note": note, "gated": False,
                "files": [{"name": "tokenizer.json", "sha256": sha256(p),
                           "path": os.path.relpath(p, REPO).replace("\\", "/"),
                           "source_path": rel}],
            }
        else:
            manifest[label] = {"status": "unavailable", "repo": "PR #29", "revision": DANIELK_COMMIT,
                               "note": f"{note}; brak pliku", "files": []}
    for label, repo, note in UNAVAILABLE:
        api = HfApi(token=get_token())
        try:
            rev = api.model_info(repo).sha
        except Exception:  # noqa: BLE001
            rev = None
        manifest[label] = {"status": "unavailable", "repo": repo, "revision": rev,
                           "note": note, "files": []}
        print(f"# {label}: {note}", file=sys.stderr)
    for label, path, note in REFERENCE_LOCAL:
        if os.path.isfile(path):
            toks[label] = HFTokenizer.from_file(path)
            manifest[label] = local_entry(path, note)
        else:
            manifest[label] = {"status": "unavailable", "path": path, "note": note, "files": []}
    for label, repo, note in REFERENCE_HF:
        try:
            entry = fetch(repo, label, note)
            p = os.path.join(REPO, entry["files"][0]["path"])
            toks[label] = HFTokenizer.from_file(p)
        except Exception as e:  # noqa: BLE001
            print(f"# brak {label}: {type(e).__name__}", file=sys.stderr)
            entry = {"status": "unavailable", "repo": repo, "note": note, "files": []}
        manifest[label] = entry
    try:
        import tiktoken
        toks["GPT-4o-o200k"] = TiktokenWrap(tiktoken.get_encoding("o200k_base"))
        manifest["GPT-4o-o200k"] = {
            "status": "existing", "repo": None, "revision": None,
            "note": "tiktoken o200k_base (lokalna biblioteka); wyniki fertility z istniejących plików",
            "files": [],
        }
    except Exception as e:  # noqa: BLE001
        print(f"# brak GPT-4o: {e}", file=sys.stderr)
        manifest["GPT-4o-o200k"] = {"status": "unavailable", "note": str(e), "files": []}

    # uzupełnienie metadanych
    seen = {}
    for label, entry in manifest.items():
        entry["models_using"] = [entry.get("repo") or entry.get("path") or "tiktoken"]
        if label in toks:
            if label == "GPT-4o-o200k":
                entry["vocab"] = toks[label].n_vocab
            else:
                v = toks[label].get_vocab()
                entry["vocab"] = len(v) if isinstance(v, dict) else None
        else:
            entry["vocab"] = None
        h = next((f["sha256"] for f in entry.get("files", []) if f["name"] == "tokenizer.json"), None)
        entry["tokenizer_json_sha256"] = h
        entry["same_tokenizer_as"] = seen.get(h) if h else None
        if h:
            seen.setdefault(h, label)
    return toks, manifest


# ---------------------------------------------------------------- metryki


def ids(tok, text):
    return list(tok.encode(text, add_special_tokens=False).ids)


def bootstrap_ci(tpd, wpd, n=1000, seed=SEED):
    """Dokładnie jak w tkx_v2/measure.py."""
    if not tpd:
        return [float("nan"), float("nan")]
    t = np.asarray(tpd, dtype=float)
    w = np.asarray(wpd, dtype=float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(t), size=(n, len(t)))
    ratios = t[idx].sum(axis=1) / w[idx].sum(axis=1)
    return [float(np.percentile(ratios, 2.5)), float(np.percentile(ratios, 97.5))]


def measure_source(tok, docs):
    tpd, wpd = [], []
    b = 0
    for text in docs:
        tpd.append(len(ids(tok, text)))
        wpd.append(len(text.split()))
        b += len(text.encode("utf-8"))
    t, w = int(sum(tpd)), int(sum(wpd))
    lo, hi = bootstrap_ci(tpd, wpd)
    return {
        "docs": len(docs), "words": w, "tokens": t, "bytes": b,
        "fertility": t / w if w else float("nan"),
        "bytes_per_token": b / t if t else float("nan"),
        "fertility_ci_lo": lo, "fertility_ci_hi": hi,
    }


# mapowanie wyników istniejących (bez przeliczania)

REF_V2_KEY = {
    "V0-32k": "TKX/V0-32k",
    "Slayer-v6": "Slayer1B-1.08",
    "Bielik-1.5B-v3": "Bielik-1.5B-v3",
    "APT3-1B": "APT3-1B",
    "GPT-4o-o200k": "GPT-4o-o200k",
}
REF_V21_KEY = {
    "V0-32k": "V0-32k",
    "V0J2-32k": "V0J2-32k",
    "Slayer-v6": "Slayer1B-1.08",
    "GPT-4o-o200k": "GPT-4o-o200k",
}
V21_POLISH = {
    "1_bzp": "bzp_ogloszenia", "2_du_eli": "du_eli", "3_kio": "kio",
    "4_samorzad": "samorzad", "5_granty": "granty",
    "json_bzp_tabele": "json_bzp_tabele", "7_ogolny": "general_web",
}


def load_existing():
    p = lambda n: json.load(open(os.path.join(RESULTS, n), encoding="utf-8"))
    return p("tkx_v2_fertility.json"), p("tkx_v21_dev.json"), p("tkx_v21_test.json"), p("tkx_v21_granty149.json")


def from_existing(row, origin):
    out = {k: row[k] for k in ("fertility", "bytes_per_token") if k in row}
    lo, hi = row.get("fertility_ci_lo"), row.get("fertility_ci_hi")
    if lo is None and isinstance(row.get("ci"), list):
        lo, hi = row["ci"]
    out["fertility_ci_lo"] = lo
    out["fertility_ci_hi"] = hi
    out["origin"] = origin
    return out


def copy_reference(sname, label, existing):
    """Zwraca wiersz z istniejącego pliku albo None, gdy go nie ma."""
    v2, v21dev, v21test, v21grant = existing
    if sname in V2_CORPUS and label in REF_V2_KEY:
        row = v2["sources"][sname]["tokenizers"].get(REF_V2_KEY[label])
        if row:
            return from_existing(row, "existing:results/tkx_v2_fertility.json")
    if label in REF_V21_KEY:
        key = REF_V21_KEY[label]
        src, fname = None, None
        if sname in V21_POLISH:
            src, fname = v21dev["sources"][V21_POLISH[sname]], "results/tkx_v21_dev.json"
        elif sname == "6_json_narzedzia":
            src, fname = v21test["sources"]["tc1_test"], "results/tkx_v21_test.json"
        elif sname == "granty_149":
            src, fname = v21grant, "results/tkx_v21_granty149.json"
        elif sname == "json_generic_heldout_test":
            src, fname = v21test["sources"]["json_generic_test"], "results/tkx_v21_test.json"
        if src is not None:
            row = src["tokenizers"].get(key) if "tokenizers" in src else None
            if row:
                return from_existing(row, f"existing:{fname}")
    if sname == "granty_149" and label in ("Bielik-1.5B-v3", "APT3-1B"):
        return None
    return None


def main():
    os.makedirs(RESULTS, exist_ok=True)
    os.makedirs(HF_DIR, exist_ok=True)
    toks, manifest = build_tokenizers()
    print("tokenizery:", ", ".join(toks))

    sources, order = load_sources()
    existing = load_existing()
    fertility = {
        "seed": SEED, "pythonhashseed": 0, "bootstrap": 1000,
        "method": "suma tokenow / suma slow (str.split()), encode(add_special_tokens=False)",
        "note": "origin=existing -> liczby skopiowane z istniejących wyników, bez przeliczania",
        "sources": {}, "tokenizers": list(toks) + ["Llama-3.1-8B"],
    }

    dead_counts = {label: {} for label in toks}
    added = {label: set() for label in toks}
    for label, tok in toks.items():
        try:
            added[label] = set(tok.get_added_vocab().values())
        except Exception:  # noqa: BLE001
            pass
        v = tok.get_vocab()
        if isinstance(v, dict):
            dead_counts[label] = {i: 0 for i in set(v.values())}

    for sname in order:
        docs = sources[sname]
        row = {
            "docs": len(docs),
            "words": sum(len(d.split()) for d in docs),
            "bytes": sum(len(d.encode("utf-8")) for d in docs),
            "tokenizers": {},
        }
        for label, tok in toks.items():
            # liczymy użycie tokenów także dla tokenizatorów referencyjnych,
            # których fertility jest kopiowana z istniejących wyników
            if sname in V2_CORPUS and dead_counts[label]:
                for text in docs:
                    for i in ids(tok, text):
                        if i in dead_counts[label]:
                            dead_counts[label][i] += 1
            ref = copy_reference(sname, label, existing)
            if ref is not None:
                row["tokenizers"][label] = ref
                continue
            m = measure_source(tok, docs)
            row["tokenizers"][label] = dict(m, origin="new")
        fertility["sources"][sname] = row
        print(f"  {sname}: {row['docs']} dok., {row['words']} słów")
    fertility["sources"]["granty_149"]["note"] = "D:\\VPS\\fabryka\\spec1\\data\\zbiorB.jsonl, pole text, tylko odczyt"
    with open(os.path.join(RESULTS, "tkx_zoo_fertility.json"), "w", encoding="utf-8") as f:
        json.dump(fertility, f, ensure_ascii=False, indent=2)
        f.write("\n")

    # JSON narzędzi — osobny plik (jak w v21)
    jt = {
        "seed": SEED, "sources": {},
        "note": " fertility skopiowana z results/tkx_zoo_fertility.json (origin wskazuje źródło)",
    }
    for sname in ("6_json_narzedzia", "json_generic_heldout_test"):
        jt["sources"][sname] = fertility["sources"][sname]
    with open(os.path.join(RESULTS, "tkx_zoo_json_tools.json"), "w", encoding="utf-8") as f:
        json.dump(jt, f, ensure_ascii=False, indent=2)
        f.write("\n")

    # formaty dat/kwot/§
    fmt = formaty.measure_all(toks, ids)
    with open(os.path.join(RESULTS, "tkx_zoo_formats.json"), "w", encoding="utf-8") as f:
        json.dump(fmt, f, ensure_ascii=False, indent=2)
        f.write("\n")

    # test regresji podziału (4 frazy, wszystkie tokenizery łącznie z V0-32k)
    phrases = ["15 maja", "100 mln zł", "3 miesiące", "5 min"]
    base = {}
    if "V0-32k" in toks:
        base = {p: formaty.segment(toks["V0-32k"], p)[0] for p in phrases}
    reg = {"phrases": phrases, "reference": "V0-32k", "tokenizers": {}}
    for label, tok in toks.items():
        row = {}
        for p in phrases:
            tlist, n = formaty.segment(tok, p)
            row[p] = {"tokens": tlist, "n": n,
                      "same_as_v0": (tlist == base[p]) if p in base else None}
        reg["tokenizers"][label] = row
    with open(os.path.join(RESULTS, "tkx_zoo_regression_split.json"), "w", encoding="utf-8") as f:
        json.dump(reg, f, ensure_ascii=False, indent=2)
        f.write("\n")

    # koszt słownika w modelu 150M
    cost = {"vocab_x_dmodel": {}, "d_models": [768, 1024], "model_params": 150_000_000,
            "note": "embeddingi wejściowe = vocab*d_model; przy braku współdzielenia z wyjściem ×2"}
    for label, tok in toks.items():
        v = manifest[label].get("vocab")
        if not v:
            continue
        row = {}
        for d in (768, 1024):
            n = int(v) * d
            row[str(d)] = {"params": n, "params_m": n / 1e6,
                           "pct_150m": 100.0 * n / 150_000_000,
                           "pct_150m_untied": 100.0 * 2 * n / 150_000_000}
        cost["vocab_x_dmodel"][label] = {"vocab": int(v), **row}
    with open(os.path.join(RESULTS, "tkx_zoo_vocab_cost.json"), "w", encoding="utf-8") as f:
        json.dump(cost, f, ensure_ascii=False, indent=2)
        f.write("\n")

    # „§” jako jeden token
    section = {"tokenizers": {}}
    for label, tok in toks.items():
        n = len(ids(tok, "§"))
        section["tokenizers"][label] = {"tokens": n, "one_token": n == 1}
    with open(os.path.join(RESULTS, "tkx_zoo_section_sign.json"), "w", encoding="utf-8") as f:
        json.dump(section, f, ensure_ascii=False, indent=2)
        f.write("\n")

    # martwe tokeny (korpus v2: 8 źródeł)
    dead = {"corpus": sorted(V2_CORPUS), "tokenizers": {}}
    for label, counts in dead_counts.items():
        if not counts:
            dead["tokenizers"][label] = {"vocab": None, "dead": None, "note": "brak get_vocab (tiktoken)"}
            continue
        considered = [i for i in counts if i not in added[label]]
        d = sum(1 for i in considered if counts[i] == 0)
        dead["tokenizers"][label] = {
            "vocab": len(counts), "dead": d, "considered": len(considered),
            "dead_pct": 100.0 * d / len(considered) if considered else None,
            "special_excluded": len(added[label]),
        }
    with open(os.path.join(RESULTS, "tkx_zoo_dead_tokens.json"), "w", encoding="utf-8") as f:
        json.dump(dead, f, ensure_ascii=False, indent=2)
        f.write("\n")

    # round-trip 700 dok. (pierwsze 100 z każdego z 7 źródeł polskich)
    cases, seen = [], set()
    for sname in ROUNDTRIP_SOURCES:
        for d in sources[sname][:100]:
            cases.append((sname, d))
            seen.add(d)
    for sname in ROUNDTRIP_SOURCES:
        for d in sources[sname]:
            if len(cases) >= 700:
                break
            if d not in seen:
                cases.append((sname, d))
                seen.add(d)
    rt = {"cases": len(cases), "unique_texts": len(seen), "tokenizers": {}}
    for label, tok in toks.items():
        bad, nfd = [], 0
        for sname, text in cases:
            if tok.decode(ids(tok, text)) != text:
                bad.append({"source": sname, "chars": len(text)})
                if text != unicodedata.normalize("NFC", text):
                    nfd += 1
        rt["tokenizers"][label] = {"cases": len(cases), "bad": len(bad), "bad_nfd": nfd,
                                   "ok": not bad, "examples_bad": bad[:5]}
    with open(os.path.join(RESULTS, "tkx_zoo_roundtrip.json"), "w", encoding="utf-8") as f:
        json.dump(rt, f, ensure_ascii=False, indent=2)
        f.write("\n")

    # hash: PLLuM vs baza
    comp = {}
    for label, base, status, detail in [
        ("PLLuM-4B", "Gemma-3-4B", "różny (rozszerzony)",
         "PLLuM-4B-instruct tokenizer.json ≠ Gemma 3; PLLuM-4B-base-2512 ma hash identyczny z Gemma 3"),
        ("PLLuM-8B", "Llama-3.1-8B", "baza niedostępna (gated, czeka na zatwierdzenie Meta)",
         "nie podstawiono innego repo; porównanie hashu do uzupełnienia"),
        ("PLLuM-12B", "Mistral-Nemo", "różny (rozszerzony)",
         "PLLuM-12B tokenizer.json ≠ Mistral Nemo; PLLuM-12B-base-2508 ma ten sam hash co instruct-2512"),
    ]:
        comp[label] = {
            "base": base, "status": status, "detail": detail,
            "tokenizer_sha256": manifest[label].get("tokenizer_json_sha256"),
            "base_sha256": manifest[base].get("tokenizer_json_sha256"),
            "base_repo": manifest[base].get("repo"),
            "base_status": manifest[base].get("status"),
        }
    manifest["base_comparison"] = comp
    manifest["branch"] = "feat/tkx-zoo"
    manifest["base_commit"] = BASE_COMMIT
    manifest["seed"] = SEED
    manifest["pythonhashseed"] = 0
    manifest["bootstrap"] = 1000
    with open(os.path.join(ZOO, "MANIFEST.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print("zapisano results/tkx_zoo_*.json oraz tkx_zoo/MANIFEST.json")


if __name__ == "__main__":
    main()
