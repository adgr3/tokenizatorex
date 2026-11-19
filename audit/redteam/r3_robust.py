"""R3 task 1: robustness of the ranking to the definition of "word".

Variants (TEST split, 7 official domains + web + wikipedia + nauka):
  baseline : tokens / str.split()
  letters  : tokens / regex ``[^\\W\\d_]+`` (Unicode letters only)
  bytes    : tokens / UTF-8 byte
  drop10   : baseline after dropping the 10% longest documents per domain
  loso     : leave-one-official-domain-out aggregate (pooled tokens/words)
"""
from __future__ import annotations

import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import rtlib as R  # noqa: E402


def rank_table(metric: dict[str, float]) -> list[dict]:
    ranked = sorted(metric.items(), key=lambda kv: kv[1])
    return [{"label": lab, "value": val, "rank": i + 1}
            for i, (lab, val) in enumerate(ranked)]


def add_tkx_metrics(metric: dict[str, float]) -> dict:
    ranked = sorted(metric.items(), key=lambda kv: kv[1])
    best_label, best_val = ranked[0]
    second_label, second_val = ranked[1]
    tkx = metric["TOKENIZATOREX"]
    return {
        "tkx_rank": [i + 1 for i, (lab, _) in enumerate(ranked) if lab == "TOKENIZATOREX"][0],
        "best": best_label,
        "best_value": best_val,
        "second": second_label,
        "second_value": second_val,
        "tkx_value": tkx,
        "gap_tkx_minus_best": tkx - best_val,
        "relative_tkx_vs_best": tkx / best_val - 1.0,
    }


def aggregate(docs: list[dict], tokenizers, docvals: dict) -> dict:
    toks = {lab: 0 for lab in tokenizers}
    words = 0
    words_letters = 0
    byts = 0
    for i, d in enumerate(docs):
        words += docvals[i]["words"]
        words_letters += docvals[i]["words_letters"]
        byts += docvals[i]["bytes"]
        for lab in tokenizers:
            toks[lab] += docvals[i]["tokens"][lab]
    return {"tokens": toks, "words": words, "words_letters": words_letters, "bytes": byts}


def main() -> None:
    tokenizers = R.get_tokenizers()
    domains = R.ALL10
    docs_by_dom = R.load_domain_docs(domains)

    # ---- encode once -------------------------------------------------------
    docvals: dict[str, list[dict]] = {}
    for dom in domains:
        vals = []
        for d in docs_by_dom[dom]:
            text = d["text"]
            vals.append({
                "id": d["id"],
                "source": d.get("source", ""),
                "words": R.words_split(text),
                "words_letters": R.words_letters(text),
                "bytes": R.utf8_bytes(text),
                "tokens": {lab: R.n_tokens(tok, text) for lab, tok in tokenizers.items()},
            })
        docvals[dom] = vals
        print(f"encoded {dom}: {len(vals)} docs")

    out = {
        "meta": {
            "split": "test",
            "domains": domains,
            "official7": R.OFFICIAL7,
            "tokenizers": R.LABELS,
            "word_definitions": {
                "baseline": "str.split()",
                "letters": r"[^\W\d_]+ (regex, Unicode)",
            },
            "drop10": "drop ceil(10%) longest documents per domain, measured in str.split() words",
        },
        "baseline": {},
        "letters": {},
        "bytes": {},
        "drop10": {},
        "loso": {},
        "changes": {},
    }

    base_metrics_by_dom = {}
    for dom in domains:
        agg = aggregate(docs_by_dom[dom], tokenizers, docvals[dom])
        fert = {lab: agg["tokens"][lab] / agg["words"] for lab in tokenizers}
        base_metrics_by_dom[dom] = fert
        out["baseline"][dom] = {
            "docs": len(docs_by_dom[dom]),
            "words": agg["words"],
            "tokens": agg["tokens"],
            "fertility": fert,
            "ranking": rank_table(fert),
            **add_tkx_metrics(fert),
        }

    # ---- (a) letters-only word definition ----------------------------------
    for dom in domains:
        agg = aggregate(docs_by_dom[dom], tokenizers, docvals[dom])
        fert = {lab: agg["tokens"][lab] / agg["words_letters"] for lab in tokenizers}
        out["letters"][dom] = {
            "docs": len(docs_by_dom[dom]),
            "words_letters": agg["words_letters"],
            "tokens": agg["tokens"],
            "fertility": fert,
            "ranking": rank_table(fert),
            **add_tkx_metrics(fert),
        }

    # ---- (b) tokens per UTF-8 byte -----------------------------------------
    for dom in domains:
        agg = aggregate(docs_by_dom[dom], tokenizers, docvals[dom])
        tpb = {lab: agg["tokens"][lab] / agg["bytes"] for lab in tokenizers}
        out["bytes"][dom] = {
            "docs": len(docs_by_dom[dom]),
            "bytes": agg["bytes"],
            "tokens": agg["tokens"],
            "tokens_per_byte": tpb,
            "ranking": rank_table(tpb),
            **add_tkx_metrics(tpb),
        }

    # ---- (c) drop 10% longest documents ------------------------------------
    for dom in domains:
        vals = docvals[dom]
        n = len(vals)
        k = max(1, int(math.floor(0.10 * n)))
        keep_idx = sorted(range(n), key=lambda i: vals[i]["words"])[: n - k]
        keep_docs = [docs_by_dom[dom][i] for i in keep_idx]
        keep_vals = [vals[i] for i in keep_idx]
        agg = aggregate(keep_docs, tokenizers, keep_vals)
        fert = {lab: agg["tokens"][lab] / agg["words"] for lab in tokenizers}
        dropped = [vals[i]["id"] for i in sorted(set(range(n)) - set(keep_idx))]
        out["drop10"][dom] = {
            "docs_total": n,
            "docs_kept": len(keep_idx),
            "docs_dropped": k,
            "dropped_ids_sample": dropped[:5],
            "words_kept": agg["words"],
            "tokens": agg["tokens"],
            "fertility": fert,
            "ranking": rank_table(fert),
            **add_tkx_metrics(fert),
        }

    # ---- (d) leave-one-source-out over the 7 official domains --------------
    for removed in R.OFFICIAL7:
        kept = [dom for dom in R.OFFICIAL7 if dom != removed]
        all_docs = []
        all_vals = []
        for dom in kept:
            all_docs.extend(docs_by_dom[dom])
            all_vals.extend(docvals[dom])
        agg = aggregate(all_docs, tokenizers, all_vals)
        fert = {lab: agg["tokens"][lab] / agg["words"] for lab in tokenizers}
        dom_fert = {}
        for dom in kept:
            a = aggregate(docs_by_dom[dom], tokenizers, docvals[dom])
            dom_fert[dom] = {lab: a["tokens"][lab] / a["words"] for lab in tokenizers}
        mean_fert = {
            lab: sum(dom_fert[d][lab] for d in kept) / len(kept) for lab in tokenizers
        }
        out["loso"][removed] = {
            "domains_kept": kept,
            "docs": len(all_docs),
            "words": agg["words"],
            "tokens": agg["tokens"],
            "pooled_fertility": fert,
            "pooled_ranking": rank_table(fert),
            **add_tkx_metrics(fert),
            "mean_domain_fertility": mean_fert,
            "mean_domain_ranking": rank_table(mean_fert),
            "mean_domain_winner": rank_table(mean_fert)[0]["label"],
        }

    # ---- official aggregate baseline --------------------------------------
    all_docs = []
    all_vals = []
    for dom in R.OFFICIAL7:
        all_docs.extend(docs_by_dom[dom])
        all_vals.extend(docvals[dom])
    agg = aggregate(all_docs, tokenizers, all_vals)
    fert = {lab: agg["tokens"][lab] / agg["words"] for lab in tokenizers}
    out["baseline_official_pooled"] = {
        "docs": len(all_docs), "words": agg["words"], "tokens": agg["tokens"],
        "fertility": fert, "ranking": rank_table(fert), **add_tkx_metrics(fert),
    }
    mean_fert = {lab: sum(base_metrics_by_dom[d][lab] for d in R.OFFICIAL7) / 7
                 for lab in tokenizers}
    out["baseline_official_mean"] = {
        "mean_domain_fertility": mean_fert, "ranking": rank_table(mean_fert),
        **add_tkx_metrics(mean_fert),
    }

    # ---- change detection --------------------------------------------------
    for variant in ("letters", "bytes", "drop10"):
        rows = {}
        for dom in domains:
            b = out["baseline"][dom]["ranking"]
            v = out[variant][dom]["ranking"]
            b_top2 = [x["label"] for x in b[:2]]
            v_top2 = [x["label"] for x in v[:2]]
            rows[dom] = {
                "baseline_top1": b_top2[0],
                "variant_top1": v_top2[0],
                "top1_changed": b_top2[0] != v_top2[0],
                "baseline_top2": b_top2,
                "variant_top2": v_top2,
                "top2_changed": set(b_top2) != set(v_top2),
                "tkx_rank_baseline": out["baseline"][dom]["tkx_rank"],
                "tkx_rank_variant": out[variant][dom]["tkx_rank"],
                "tkx_lead_disappeared": (out["baseline"][dom]["tkx_rank"] == 1
                                         and out[variant][dom]["tkx_rank"] != 1),
            }
        out["changes"][variant] = rows

    path = R.write_json("r3_robustness.json", out)
    print("saved", path)

    # ---- console summary ---------------------------------------------------
    print("\n=== per-domain rankings ===")
    for dom in domains:
        b = out["baseline"][dom]
        print(f"{dom:<22} base: " + " > ".join(
            f"{x['label']}={x['value']:.3f}" for x in b["ranking"][:3]))
        for var in ("letters", "bytes", "drop10"):
            v = out[var][dom]
            print(f"{'':<22} {var:<8}: " + " > ".join(
                f"{x['label']}={x['value']:.3f}" for x in v["ranking"][:3]))
    print("\n=== LOSO pooled ===")
    for removed, v in out["loso"].items():
        print(f"-{removed:<22} " + " > ".join(
            f"{x['label']}={x['value']:.3f}" for x in v["pooled_ranking"][:3]))
    print("\n=== official pooled baseline ===")
    print(" > ".join(f"{x['label']}={x['value']:.4f}"
                     for x in out["baseline_official_pooled"]["ranking"]))


if __name__ == "__main__":
    main()
