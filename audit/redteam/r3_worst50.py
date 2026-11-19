"""R3 task 2: the documents on which TOKENIZATOREX is weakest.

For every TEST document in the 7 official domains we compute tokens/word for
TOKENIZATOREX, Slayer1B and APT3-1B and rank documents by the relative
advantage of the competitor over TOKENIZATOREX:

    adv = (tokens_TKX - tokens_competitor) / tokens_TKX

adv > 0 means the competitor uses fewer tokens than TOKENIZATOREX.  Because
TOKENIZATOREX is much cheaper on average, the top of this ranking is the set of
documents where its advantage is the smallest (or absent).
"""
from __future__ import annotations

import os
import re
import statistics
import sys

sys.dont_write_bytecode = True
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import rtlib as R  # noqa: E402

EN_STOP = set("""
the and of to in a is that for it as was with be by on not he i this are or his
from at which but have an had they you were their one all we can her has there
been if more when will would who so no what about up out do like time into
""".split())

DIGIT_RE = re.compile(r"\d")
LETTER_RE = re.compile(r"[^\W\d_]", re.UNICODE)
OCR_WORD_RE = re.compile(r"rn", re.IGNORECASE)


def features(text: str) -> dict:
    n = max(1, len(text))
    words = text.split()
    nw = max(1, len(words))
    letters = sum(1 for c in text if c.isalpha())
    digits = sum(1 for c in text if c.isdigit())
    upper = sum(1 for c in text if c.isupper())
    nonletter = sum(1 for c in text if not c.isalnum() and not c.isspace())
    word_lens = [len(w) for w in words]
    en_hits = 0
    ocr_hits = 0
    digit_word_hits = 0
    for w in words:
        core = "".join(c for c in w.lower() if c.isalpha())
        if core in EN_STOP:
            en_hits += 1
        if OCR_WORD_RE.search(w):
            ocr_hits += 1
        if any(c.isdigit() for c in w) and any(c.isalpha() for c in w):
            digit_word_hits += 1
    return {
        "chars": len(text),
        "words": len(words),
        "lines": text.count("\n") + 1,
        "digit_share": digits / n,
        "uppercase_share": upper / max(1, letters),
        "nonletter_share": nonletter / n,
        "avg_word_len": sum(word_lens) / nw,
        "english_stopword_share": en_hits / nw,
        "ocr_like_per_1000w": 1000.0 * ocr_hits / nw,
        "digit_word_per_1000w": 1000.0 * digit_word_hits / nw,
    }


FEATURE_KEYS = [
    "digit_share", "uppercase_share", "nonletter_share", "avg_word_len",
    "english_stopword_share", "ocr_like_per_1000w", "digit_word_per_1000w",
    "lines", "chars",
]


def mean_feats(rows: list[dict]) -> dict:
    return {k: statistics.fmean(r["features"][k] for r in rows) for k in FEATURE_KEYS}


def _ranks(vals: list[float]) -> list[float]:
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    ranks = [0.0] * len(vals)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def spearman(xs: list[float], ys: list[float]) -> float:
    rx, ry = _ranks(xs), _ranks(ys)
    n = len(rx)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx = (sum((a - mx) ** 2 for a in rx)) ** 0.5
    dy = (sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / (dx * dy) if dx and dy else float("nan")


def snippets(text: str, k: int = 5) -> list[str]:
    """Short generic-looking fragments (no trimming of names is attempted here;
    the report only quotes fragments manually checked to be generic)."""
    out = []
    for line in text.split("\n"):
        s = " ".join(line.split())
        if 40 <= len(s) <= 180 and sum(c.isdigit() for c in s) <= 4:
            out.append(s)
        if len(out) >= k:
            break
    return out


def main() -> None:
    tokenizers = R.get_tokenizers(["TOKENIZATOREX", "Slayer1B", "APT3-1B"])
    rows = []
    for dom in R.OFFICIAL7:
        for d in R.load_docs(dom):
            text = d["text"]
            words = R.words_split(text)
            tokens = {lab: R.n_tokens(tok, text) for lab, tok in tokenizers.items()}
            rows.append({
                "id": d["id"], "domain": dom, "source": d.get("source", ""),
                "words": words, "tokens": tokens,
                "fertility": {lab: tokens[lab] / words for lab in tokenizers},
                "features": features(text),
            })
    for r in rows:
        r["adv_slayer"] = (r["tokens"]["TOKENIZATOREX"] - r["tokens"]["Slayer1B"]) / r["tokens"]["TOKENIZATOREX"]
        r["adv_apt3"] = (r["tokens"]["TOKENIZATOREX"] - r["tokens"]["APT3-1B"]) / r["tokens"]["TOKENIZATOREX"]

    def top(key: str) -> list[dict]:
        return sorted(rows, key=lambda r: r[key], reverse=True)[:50]

    top_s = top("adv_slayer")
    top_a = top("adv_apt3")

    texts = {}
    for dom in R.OFFICIAL7:
        for d in R.load_docs(dom):
            texts[d["id"]] = d["text"]
    for r in top_s + top_a:
        if "snippets" not in r:
            r["snippets"] = snippets(texts[r["id"]])

    all_mean = mean_feats(rows)
    dom_stats = {}
    for dom in R.OFFICIAL7:
        sub = [r for r in rows if r["domain"] == dom]
        dom_stats[dom] = {
            "docs": len(sub),
            "mean_features": mean_feats(sub),
            "median_adv_slayer": statistics.median(r["adv_slayer"] for r in sub),
            "median_adv_apt3": statistics.median(r["adv_apt3"] for r in sub),
        }
    out = {
        "meta": {
            "split": "test",
            "official7": R.OFFICIAL7,
            "docs": len(rows),
            "ranking_metric": "adv = (tokens_TKX - tokens_competitor) / tokens_TKX; >0 means competitor cheaper",
            "feature_definition": {
                "digit_share": "digits / characters",
                "uppercase_share": "uppercase letters / letters",
                "nonletter_share": "non-alphanumeric, non-space characters / characters",
                "avg_word_len": "mean len(str.split())",
                "english_stopword_share": "share of split words whose lowercase letters are in a small English stopword list",
                "ocr_like_per_1000w": "words containing 'rn' per 1000 words",
                "digit_word_per_1000w": "words mixing letters and digits per 1000 words",
            },
        },
        "summary": {
            "docs_where_slayer_beats_tkx": sum(1 for r in rows if r["tokens"]["Slayer1B"] < r["tokens"]["TOKENIZATOREX"]),
            "docs_where_apt3_beats_tkx": sum(1 for r in rows if r["tokens"]["APT3-1B"] < r["tokens"]["TOKENIZATOREX"]),
            "slayer_adv_median": statistics.median(r["adv_slayer"] for r in rows),
            "apt3_adv_median": statistics.median(r["adv_apt3"] for r in rows),
            "slayer_adv_max": max(r["adv_slayer"] for r in rows),
            "apt3_adv_max": max(r["adv_apt3"] for r in rows),
            "all_mean_features": all_mean,
            "all_domain_counts": {d: sum(1 for r in rows if r["domain"] == d) for d in R.OFFICIAL7},
            "spearman_adv_slayer_vs_feature": {
                k: spearman([r["features"][k] for r in rows], [r["adv_slayer"] for r in rows])
                for k in FEATURE_KEYS
            },
            "spearman_adv_apt3_vs_feature": {
                k: spearman([r["features"][k] for r in rows], [r["adv_apt3"] for r in rows])
                for k in FEATURE_KEYS
            },
        },
        "domain_stats": dom_stats,
        "all_docs": [
            {"id": r["id"], "domain": r["domain"], "words": r["words"],
             "tokens": r["tokens"], "adv_slayer": r["adv_slayer"],
             "adv_apt3": r["adv_apt3"], "features": r["features"]}
            for r in rows
        ],
        "top50_slayer": top_s,
        "top50_apt3": top_a,
        "top50_slayer_mean_features": mean_feats(top_s),
        "top50_apt3_mean_features": mean_feats(top_a),
        "top50_slayer_domain_counts": {d: sum(1 for r in top_s if r["domain"] == d) for d in R.OFFICIAL7},
        "top50_apt3_domain_counts": {d: sum(1 for r in top_a if r["domain"] == d) for d in R.OFFICIAL7},
    }
    path = R.write_json("r3_worst50.json", out)
    print("saved", path)
    print("Slayer beats TKX on", out["summary"]["docs_where_slayer_beats_tkx"], "docs; APT3 on",
          out["summary"]["docs_where_apt3_beats_tkx"])
    print("median adv Slayer", round(out["summary"]["slayer_adv_median"], 4),
          "APT3", round(out["summary"]["apt3_adv_median"], 4))
    for name, rows50, counts in (
        ("SLAYER", top_s, out["top50_slayer_domain_counts"]),
        ("APT3", top_a, out["top50_apt3_domain_counts"]),
    ):
        print(f"\n=== top50 {name} by domain ===", counts)
        for r in rows50[:15]:
            f = r["features"]
            print(f"{r['adv_'+('slayer' if name=='SLAYER' else 'apt3')]:+.4f} "
                  f"{r['domain']:<22} {r['words']:>5}w tox={r['tokens']['TOKENIZATOREX']:>5} "
                  f"cmp={r['tokens'][('Slayer1B' if name=='SLAYER' else 'APT3-1B')]:>5} "
                  f"dig={f['digit_share']:.3f} up={f['uppercase_share']:.3f} "
                  f"nl={f['nonletter_share']:.3f} en={f['english_stopword_share']:.3f} "
                  f"ocr={f['ocr_like_per_1000w']:.1f} {r['id']}")
    print("\n=== mean features top50 vs all ===")
    for k in FEATURE_KEYS:
        print(f"{k:<24} all={all_mean[k]:.5f}  sl={out['top50_slayer_mean_features'][k]:.5f}  apt={out['top50_apt3_mean_features'][k]:.5f}")


if __name__ == "__main__":
    main()
