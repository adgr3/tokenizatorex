"""R3 task 3: does TKX's advantage come from web boilerplate?

Remove every line / sentence that contains a boilerplate phrase from `web` and
from the 7 official domains, then recompute fertility.

Two removal modes are reported:
  boundary : single-word cues must match on word boundaries (so "Kontakt" does
             not delete "kontaktowy"), multi-word cues are literal substrings;
  literal  : any case-insensitive substring match (aggressive upper bound).
"""
from __future__ import annotations

import json
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import rtlib as R  # noqa: E402

PHRASES = [
    "Czytaj więcej", "Zobacz także", "Zobacz też", "Polityka prywatności",
    "cookies", "Strona główna", "Menu", "Szukaj", "Newsletter", "Reklama",
    "Zaloguj", "Kontakt", "Dowiedz się więcej", "Wróć", "Pobierz",
]
SINGLE = {p for p in PHRASES if " " not in p}

SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _hits(text: str) -> dict:
    low = text.lower()
    return {p: low.count(p.lower()) for p in PHRASES}


def remove(text: str, mode: str) -> tuple[str, int, dict]:
    phrases = PHRASES
    if mode == "boundary":
        patterns = []
        for p in phrases:
            if p in SINGLE:
                patterns.append(re.compile(r"(?<!\w)" + re.escape(p) + r"(?!\w)", re.IGNORECASE))
            else:
                patterns.append(re.compile(re.escape(p), re.IGNORECASE))
    else:
        patterns = [re.compile(re.escape(p), re.IGNORECASE) for p in phrases]

    def keep(unit: str) -> bool:
        return not any(pat.search(unit) for pat in patterns)

    removed_units = 0
    out_lines = []
    for line in text.split("\n"):
        if not keep(line):
            removed_units += 1
            continue
        sents = SENT_SPLIT.split(line)
        kept = [s for s in sents if keep(s)]
        removed_units += len(sents) - len(kept)
        if kept:
            out_lines.append(" ".join(kept))
    return "\n".join(out_lines).strip(), removed_units, {}


def aggregate(docs, vals):
    toks = {lab: 0 for lab in vals[0]["tokens"]} if vals else {}
    words = 0
    for v in vals:
        words += v["words"]
        for lab in toks:
            toks[lab] += v["tokens"][lab]
    return {"tokens": toks, "words": words,
            "fertility": {lab: toks[lab] / words for lab in toks} if words else {}}


def main() -> None:
    tokenizers = R.get_tokenizers(["TOKENIZATOREX", "TOKENIZATOREX-HF", "Slayer1B", "Pollock-2.0"])
    domains = R.OFFICIAL7 + ["web"]
    docs_by_dom = R.load_domain_docs(domains)

    # baseline aggregates from task 1 (same code path, same split)
    base_path = os.path.join(os.path.dirname(__file__), "r3_robustness.json")
    with open(base_path, encoding="utf-8") as f:
        base = json.load(f)
    baseline = {}
    for dom in domains:
        baseline[dom] = {
            "docs": base["baseline"][dom]["docs"],
            "words": base["baseline"][dom]["words"],
            "tokens": {lab: base["baseline"][dom]["tokens"][lab] for lab in tokenizers},
        }
        baseline[dom]["fertility"] = {
            lab: baseline[dom]["tokens"][lab] / baseline[dom]["words"] for lab in tokenizers
        }
    baseline["__official_pooled__"] = {
        "words": sum(baseline[d]["words"] for d in R.OFFICIAL7),
        "tokens": {lab: sum(baseline[d]["tokens"][lab] for d in R.OFFICIAL7) for lab in tokenizers},
    }
    baseline["__official_pooled__"]["fertility"] = {
        lab: baseline["__official_pooled__"]["tokens"][lab] / baseline["__official_pooled__"]["words"]
        for lab in tokenizers
    }

    out = {"meta": {"split": "test", "domains": domains, "phrases": PHRASES,
                    "modes": ["boundary", "literal"],
                    "baseline_source": "r3_robustness.json (same TEST docs, str.split words)"},
           "baseline": baseline, "modes": {}}

    for mode in ("boundary", "literal"):
        per_dom = {}
        hits_total = {p: 0 for p in PHRASES}
        removed_docs = 0
        chars_before = chars_after = 0
        for dom in domains:
            vals = []
            dom_hits = {p: 0 for p in PHRASES}
            dom_removed_docs = 0
            for d in docs_by_dom[dom]:
                text = d["text"]
                chars_before += len(text)
                h = _hits(text)
                for p in PHRASES:
                    dom_hits[p] += h[p]
                    hits_total[p] += h[p]
                clean, units, _ = remove(text, mode)
                chars_after += len(clean)
                if clean != text:
                    dom_removed_docs += 1
                    removed_docs += 1
                vals.append({
                    "words": R.words_split(clean),
                    "tokens": {lab: R.n_tokens(tok, clean) for lab, tok in tokenizers.items()},
                })
            per_dom[dom] = {
                "docs": len(docs_by_dom[dom]),
                "docs_changed": dom_removed_docs,
                "words_before": baseline[dom]["words"],
                "words_after": sum(v["words"] for v in vals),
                "tokens_before": baseline[dom]["tokens"],
                "tokens_after": {lab: sum(v["tokens"][lab] for v in vals) for lab in tokenizers},
                "fertility_before": baseline[dom]["fertility"],
                "fertility_after": {
                    lab: sum(v["tokens"][lab] for v in vals) / max(1, sum(v["words"] for v in vals))
                    for lab in tokenizers
                },
                "phrase_hits": dom_hits,
            }
            a = per_dom[dom]
            a["fertility_delta_rel"] = {
                lab: a["fertility_after"][lab] / a["fertility_before"][lab] - 1.0 for lab in tokenizers
            }
            a["tokens_delta_rel"] = {
                lab: a["tokens_after"][lab] / a["tokens_before"][lab] - 1.0 for lab in tokenizers
            }
            a["ranking_after"] = sorted(
                [(lab, v) for lab, v in a["fertility_after"].items()], key=lambda kv: kv[1])
            print(f"{mode:<8} {dom:<22} changed={dom_removed_docs:>3}/{len(docs_by_dom[dom]):>3} "
                  f"words {a['words_before']}->{a['words_after']}  "
                  f"fert TKX {a['fertility_before']['TOKENIZATOREX']:.3f}->{a['fertility_after']['TOKENIZATOREX']:.3f}")

        # official pooled
        off = {}
        for lab in tokenizers:
            off[lab] = {
                "tokens_before": sum(per_dom[d]["tokens_before"][lab] for d in R.OFFICIAL7),
                "tokens_after": sum(per_dom[d]["tokens_after"][lab] for d in R.OFFICIAL7),
            }
        words_before = sum(per_dom[d]["words_before"] for d in R.OFFICIAL7)
        words_after = sum(per_dom[d]["words_after"] for d in R.OFFICIAL7)
        off_summary = {
            "words_before": words_before, "words_after": words_after,
            "tokenizers": {
                lab: {
                    "tokens_before": off[lab]["tokens_before"],
                    "tokens_after": off[lab]["tokens_after"],
                    "fertility_before": off[lab]["tokens_before"] / words_before,
                    "fertility_after": off[lab]["tokens_after"] / words_after,
                    "tokens_delta_rel": off[lab]["tokens_after"] / off[lab]["tokens_before"] - 1.0,
                    "fertility_delta_rel": (off[lab]["tokens_after"] / words_after)
                    / (off[lab]["tokens_before"] / words_before) - 1.0,
                } for lab in tokenizers
            },
        }
        off_summary["ranking_before"] = sorted(
            [(lab, v["fertility_before"]) for lab, v in off_summary["tokenizers"].items()],
            key=lambda kv: kv[1])
        off_summary["ranking_after"] = sorted(
            [(lab, v["fertility_after"]) for lab, v in off_summary["tokenizers"].items()],
            key=lambda kv: kv[1])

        out["modes"][mode] = {
            "per_domain": per_dom,
            "official_pooled": off_summary,
            "hits_total": hits_total,
            "docs_changed": removed_docs,
            "chars_before": chars_before,
            "chars_after": chars_after,
            "chars_removed_share": 1.0 - chars_after / chars_before,
        }
        print(f"\n{mode}: docs changed {removed_docs}; chars removed "
              f"{100*(1-chars_after/chars_before):.2f}%")
        print("  official pooled before: " + " > ".join(
            f"{l}={v:.4f}" for l, v in off_summary["ranking_before"]))
        print("  official pooled after : " + " > ".join(
            f"{l}={v:.4f}" for l, v in off_summary["ranking_after"]))
        w = per_dom["web"]
        print("  web before: " + " > ".join(f"{l}={v:.4f}" for l, v in
              sorted(((l, w["fertility_before"][l]) for l in tokenizers), key=lambda kv: kv[1])))
        print("  web after : " + " > ".join(f"{l}={v:.4f}" for l, v in
              sorted(((l, w["fertility_after"][l]) for l in tokenizers), key=lambda kv: kv[1])))
        print()

    path = R.write_json("r3_boilerplate.json", out)
    print("saved", path)


if __name__ == "__main__":
    main()
