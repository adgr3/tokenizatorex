# -*- coding: utf-8 -*-
"""Niezalezna powtorka TKX-A (Codex). Liczy wszystkie punkty A."""
from __future__ import annotations

import hashlib
import json
import os
import random
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from urllib.parse import urlparse

# H9: HF przed repo
from tokenizers import Tokenizer as HFTokenizer  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repo root? adjust below
# This file lives in audit/review_codex/
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUDIT_DIR = os.path.join(REPO_ROOT, "audit")
if AUDIT_DIR not in sys.path:
    sys.path.append(AUDIT_DIR)
if REPO_ROOT not in sys.path:
    sys.path.append(REPO_ROOT)

from superbpe import SuperBPETokenizer, CHUNK_RE, WORD_RE  # noqa: E402
import common  # noqa: E402

RAW_DIR = common.RAW_DIR
MANIFEST_PATH = common.MANIFEST_PATH
SEED = common.SEED
BOOTSTRAP_N = common.BOOTSTRAP_N

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_PATH = os.path.join(OUT_DIR, "results_codex.json")


def load_manifest():
    return common.read_json(MANIFEST_PATH)


def raw_path(domain, doc_id):
    name = doc_id.replace("/", "_").replace("\\", "_") + ".json"
    return os.path.join(RAW_DIR, domain, name)


def load_raw(domain, doc_id):
    return common.read_json(raw_path(domain, doc_id))


def encoders():
    # TKX ref
    tok = SuperBPETokenizer.load(os.path.join(REPO_ROOT, "tokenizers", "tokenizatorex-32k.json"))
    class Ref:
        def __call__(self, t):
            return tok.encode_ordinary(t)
        def decode_one(self, i):
            return tok.decode([i])
        def vocab_size(self):
            return tok.vocab_size
        def decode_list(self, ids):
            return tok.decode(ids)
    ref = Ref()
    # TKX HF
    hf_tok = HFTokenizer.from_file(os.path.join(REPO_ROOT, "hf", "tokenizatorex-32k", "tokenizer.json"))
    class HF:
        def __call__(self, t):
            return hf_tok.encode(t, add_special_tokens=False).ids
        def decode_one(self, i):
            return hf_tok.decode([i], skip_special_tokens=False)
        def vocab_size(self):
            return hf_tok.get_vocab_size()
        def decode_list(self, ids):
            return hf_tok.decode(ids, skip_special_tokens=False)
    hf = HF()
    # Slayer1B
    sl_tok, _ = common.load_hf_repo("SlayerLab/Slayer1B-1.08")
    class HF2:
        def __init__(self, t):
            self.t = t
        def __call__(self, s):
            return self.t.encode(s, add_special_tokens=False).ids
        def decode_one(self, i):
            return self.t.decode([i], skip_special_tokens=False)
        def vocab_size(self):
            return self.t.get_vocab_size()
        def decode_list(self, ids):
            return self.t.decode(ids, skip_special_tokens=False)
    sl = HF2(sl_tok)
    # Pollock
    pl_tok, _ = common.load_hf_repo("SlayerLab/pollock-2.0-polishdynaword-150m")
    pl = HF2(pl_tok)
    return {"TKX_ref": ref, "TKX_HF": hf, "Slayer1B": sl, "Pollock": pl}


def bootstrap_ci_values(values):
    return common.bootstrap_ci(list(values), n=BOOTSTRAP_N, seed=SEED)


# ---------- A1 ----------
def compute_integrity(manifest):
    docs = manifest["documents"]
    # total docs
    total_docs = len(docs)
    # per id map
    by_id = {}
    dup_ids = []
    for d in docs:
        if d["id"] in by_id:
            dup_ids.append(d["id"])
        by_id[d["id"]] = d

    # SHA check raw vs manifest; word count; split membership
    missing_files = 0
    sha_mismatch = 0
    word_mismatch = 0
    nfd_mismatch = 0
    raw_sha_text_mismatch = 0
    split_of_id = defaultdict(set)
    sha_to_ids = defaultdict(list)
    domain_sources = defaultdict(set)
    official_date_2026 = 0
    official_domains = {"przetargi_ogloszenia", "przetargi_kio", "samorzad_uchwaly",
                        "granty_ogloszenia", "prawo_eli", "tabele_json", "prawo", "sejm"}

    for d in docs:
        domain = d["domain"]
        doc_id = d["id"]
        url = d["url"]
        domain_sources[domain].add(urlparse(url).netloc)
        # date
        if domain in official_domains and "2026" in (d.get("date") or ""):
            official_date_2026 += 1

        sha_to_ids[d["sha256"]].append(doc_id)
        split_of_id[doc_id].add(d["split"])

        path = raw_path(domain, doc_id)
        if not os.path.exists(path):
            missing_files += 1
            continue
        raw = load_raw(domain, doc_id)
        # SHA of text in raw equals manifest
        if raw.get("sha256") != d["sha256"]:
            sha_mismatch += 1
        # recompute sha from text
        if common.sha256_text(raw.get("text", "")) != d["sha256"]:
            raw_sha_text_mismatch += 1
        # word count
        if raw.get("words") != d["words"]:
            word_mismatch += 1
        if len(raw.get("text", "").split()) != d["words"]:
            word_mismatch += 0  # count separately? we count manifest vs recomputed below
        # nfd
        if raw.get("nfd") != d.get("nfd"):
            nfd_mismatch += 1

    # word count vs manifest recomputed
    word_recompute_mismatch = 0
    for d in docs:
        raw = load_raw(d["domain"], d["id"])
        if len(raw.get("text", "").split()) != d["words"]:
            word_recompute_mismatch += 1

    # doc in two splits: same id with multiple splits
    id_two_splits = sum(1 for k, v in split_of_id.items() if len(v) > 1)
    # same sha in both dev and test
    sha_both_splits = 0
    for sha, ids in sha_to_ids.items():
        splits = set()
        for did in ids:
            # find doc
            pass
    # check by sha across docs with split
    sha_split_map = defaultdict(set)
    for d in docs:
        sha_split_map[d["sha256"]].add(d["split"])
    sha_in_both = sum(1 for sha, splits in sha_split_map.items() if len(splits) > 1)

    # duplicate content: same sha under different ids
    dup_content_shas = {sha: ids for sha, ids in sha_to_ids.items() if len(set(ids)) > 1}
    dup_content_count = sum(len(set(ids)) - 1 for ids in dup_content_shas.values())

    # doc count by split
    dev_docs = sum(1 for d in docs if d["split"] == "dev")
    test_docs = sum(1 for d in docs if d["split"] == "test")

    # distinct sources per domain
    sources_per_domain = {k: len(v) for k, v in sorted(domain_sources.items())}

    return {
        "total_docs_manifest": total_docs,
        "dev_docs": dev_docs,
        "test_docs": test_docs,
        "missing_raw_files": missing_files,
        "sha_mismatch_raw_vs_manifest": sha_mismatch,
        "sha_text_recompute_mismatch": raw_sha_text_mismatch,
        "word_count_mismatch_raw_vs_manifest": word_mismatch,
        "word_count_recompute_mismatch": word_recompute_mismatch,
        "nfd_mismatch": nfd_mismatch,
        "ids_in_two_splits": id_two_splits,
        "shas_in_both_splits": sha_in_both,
        "duplicate_content_shas": len(dup_content_shas),
        "duplicate_content_extra_docs": dup_content_count,
        "official_docs_date_2026": official_date_2026,
        "distinct_url_sources_per_domain": sources_per_domain,
    }


# ---------- A2 ----------
def compute_fertility(manifest, encs, domains, split="test"):
    # group docs
    docs_by = defaultdict(list)
    for d in manifest["documents"]:
        if d["split"] == split and d["domain"] in domains:
            docs_by[d["domain"]].append(d)

    out = {}
    for dom in domains:
        out[dom] = {}
        for label, enc in encs.items():
            per_doc_fert = []
            total_tokens = 0
            total_words = 0
            for d in docs_by[dom]:
                raw = load_raw(d["domain"], d["id"])
                text = raw["text"]
                toks = enc(text)
                words = len(text.split())
                if words == 0:
                    continue
                per_doc_fert.append(len(toks) / words)
                total_tokens += len(toks)
                total_words += words
            mean, lo, hi = bootstrap_ci_values(per_doc_fert)
            out[dom][label] = {
                "docs": len(docs_by[dom]),
                "total_tokens": total_tokens,
                "total_words": total_words,
                "fertility_aggregate": total_tokens / total_words if total_words else float("nan"),
                "fertility_mean_per_doc": mean,
                "ci95_lo": lo,
                "ci95_hi": hi,
            }
    return out


# ---------- A3 ----------
def compute_calendar(encs):
    years = list(range(2015, 2036))
    out = {}
    for label in ("TKX_ref", "TKX_HF"):
        enc = encs[label]
        rows = []
        for y in years:
            ys = str(y)
            template = f"w roku {y} r. zadanie"
            rows.append({
                "year": y,
                "tokens_year": len(enc(ys)),
                "tokens_template": len(enc(template)),
            })
        out[label] = rows

    # corpus avg cost of year occurrences 2024 vs 2026 (in-context)
    corpus = {}
    for label in ("TKX_ref", "TKX_HF"):
        enc = encs[label]
        costs = defaultdict(list)
        for domain in ("przetargi_ogloszenia", "przetargi_kio", "samorzad_uchwaly",
                       "prawo_eli", "granty_ogloszenia", "tabele_json"):
            for d in [x for x in load_manifest()["documents"] if x["domain"] == domain and x["split"] == "test"]:
                raw = load_raw(d["domain"], d["id"])
                text = raw["text"]
                for m in re.finditer(r"(?<!\d)(?:19|20)\d{2}(?!\d)", text):
                    yr = m.group(0)
                    if yr not in ("2024", "2026"):
                        continue
                    # in-context cost
                    pre = len(enc(text[:m.start()]))
                    post = len(enc(text[:m.end()]))
                    costs[yr].append(post - pre)
        corpus[label] = {
            yr: {
                "n_occurrences": len(v),
                "mean_tokens": (sum(v) / len(v)) if v else float("nan"),
            }
            for yr, v in costs.items()
        }
    out["corpus_occurrence_cost"] = corpus
    return out


# ---------- A4 ----------
def compute_nfd(manifest, encs):
    domains = ["przetargi_ogloszenia", "przetargi_kio", "samorzad_uchwaly",
               "prawo_eli", "granty_ogloszenia", "tabele_json"]
    out = {}
    for label in ("TKX_ref", "TKX_HF", "Slayer1B", "Pollock"):
        enc = encs[label]
        per_doc_pct = []
        total_orig = 0
        total_nfd = 0
        ndocs = 0
        for dom in domains:
            for d in [x for x in manifest["documents"] if x["domain"] == dom and x["split"] == "test"]:
                raw = load_raw(d["domain"], d["id"])
                text = raw["text"]
                nfd_text = unicodedata.normalize("NFD", text)
                to = len(enc(text))
                tn = len(enc(nfd_text))
                total_orig += to
                total_nfd += tn
                if to > 0:
                    per_doc_pct.append((tn - to) / to * 100.0)
                ndocs += 1
        mean, lo, hi = bootstrap_ci_values(per_doc_pct)
        out[label] = {
            "docs": ndocs,
            "total_tokens_original": total_orig,
            "total_tokens_nfd": total_nfd,
            "increase_pct_aggregate": (total_nfd - total_orig) / total_orig * 100.0 if total_orig else float("nan"),
            "increase_pct_mean_per_doc": mean,
            "ci95_lo": lo,
            "ci95_hi": hi,
        }
    return out


# ---------- A5 ----------
def compute_hf_parity(manifest, encs, domains):
    ref = encs["TKX_ref"]
    hf = encs["TKX_HF"]
    out = {}
    for dom in domains:
        total_frags = 0
        identical = 0
        for d in [x for x in manifest["documents"] if x["domain"] == dom and x["split"] == "test"]:
            raw = load_raw(d["domain"], d["id"])
            text = raw["text"]
            for ch in CHUNK_RE.findall(text):
                if ch == "":
                    continue
                # fragment = chunk
                r_ids = ref(ch)
                h_ids = hf(ch)
                # compare decoded token strings
                r_strs = [ref.decode_one(i) for i in r_ids]
                h_strs = [hf.decode_one(i) for i in h_ids]
                total_frags += 1
                if r_strs == h_strs:
                    identical += 1
        out[dom] = {
            "fragments": total_frags,
            "identical": identical,
            "parity_pct": identical / total_frags * 100.0 if total_frags else float("nan"),
        }
    return out


# ---------- A6 ----------
def compute_renyi(manifest, encs):
    # frequencies over all docs (dev+test), all domains
    labels = ["TKX_ref", "Slayer1B", "Pollock"]
    out = {}
    for label in labels:
        enc = encs[label]
        freq = Counter()
        total = 0
        for d in manifest["documents"]:
            if d["split"] != "test":
                continue
            raw = load_raw(d["domain"], d["id"])
            ids = enc(raw["text"])
            for i in ids:
                freq[i] += 1
                total += 1
        V = enc.vocab_size()
        alpha = 2.5
        # p_i
        s = 0.0
        for cnt in freq.values():
            p = cnt / total
            s += p ** alpha
        import math
        H = 1.0 / (1 - alpha) * math.log(s) if s > 0 else float("nan")
        out[label] = {
            "vocab_size": V,
            "total_tokens": total,
            "distinct_tokens_used": len(freq),
            "H_alpha": H,
            "renyi_standard_H_over_logV": H / math.log(V) if V > 1 else float("nan"),
            "renyi_expH_over_V": (math.exp(H) / V) if V > 0 else float("nan"),
        }
    return out


# ---------- A7 ----------
def compute_digits(manifest):
    enc = encoders()["TKX_ref"]
    domains = sorted({d["domain"] for d in manifest["documents"]})
    out = {}
    for dom in domains:
        test_docs = [d for d in manifest["documents"] if d["domain"] == dom and d["split"] == "test"]
        total_chars = 0
        total_words = 0
        total_digits = 0
        words_with_digit = 0
        total_tokens_domain = 0
        tokens_with_digit = 0
        tokens_digit_leading_space = 0
        for d in test_docs:
            raw = load_raw(d["domain"], d["id"])
            text = raw["text"]
            total_chars += len(text)
            ws = text.split()
            total_words += len(ws)
            total_digits += sum(1 for c in text if c in "0123456789")
            words_with_digit += sum(1 for w in ws if any(c in "0123456789" for c in w))
            ids = enc(text)
            total_tokens_domain += len(ids)
            for i in ids:
                dec = enc.decode_one(i)
                if any(c in "0123456789" for c in dec):
                    tokens_with_digit += 1
                    if dec[:1] == " " and any(c in "0123456789" for c in dec):
                        # leading space + digit
                        tokens_digit_leading_space += 1
        out[dom] = {
            "docs": len(test_docs),
            "digit_char_share": total_digits / total_chars if total_chars else float("nan"),
            "number_word_share": words_with_digit / total_words if total_words else float("nan"),
            "total_digits": total_digits,
            "words_with_digit": words_with_digit,
            "total_tokens_domain": total_tokens_domain,
            "tokens_with_digit": tokens_with_digit,
            "tokens_digit_leading_space": tokens_digit_leading_space,
            "variant_each_digit_separate_abs": total_digits - tokens_with_digit,
            "variant_each_digit_separate_pct_of_tokens": (total_digits - tokens_with_digit) / total_tokens_domain * 100.0 if total_tokens_domain else float("nan"),
        }
    return out


def main():
    manifest = load_manifest()
    encs = encoders()

    res = {}
    res["A1_integrity"] = compute_integrity(manifest)
    res["A2_fertility"] = compute_fertility(
        manifest, encs,
        ["przetargi_ogloszenia", "samorzad_uchwaly", "prawo_eli", "przetargi_kio"],
    )
    res["A3_calendar"] = compute_calendar(encs)
    res["A4_nfd"] = compute_nfd(manifest, encs)
    res["A5_hf_parity"] = compute_hf_parity(manifest, encs, ["przetargi_ogloszenia", "web"])
    res["A6_renyi"] = compute_renyi(manifest, encs)
    res["A7_digits"] = compute_digits(manifest)

    common.write_json(RESULTS_PATH, res)
    print("done", RESULTS_PATH)


if __name__ == "__main__":
    main()
