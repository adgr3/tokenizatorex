"""Runda 1.8 — parytet eksportu HF (H8).

Porównuje segmentację referencyjnego enkodera i eksportu HF na tych samych
fragmentach (`CHUNK_PATTERN`): odsetek identycznych fragmentów, różnica tokenów
i klasyfikacja przyczyn różnic. Tylko diagnoza — bez zmian w `export_hf.py`.

Wynik: audit/results/hf_parity.json (+ hf_parity.md)
"""
from __future__ import annotations

import os
import re
import sys
from collections import Counter

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common import (REPO_ROOT, RESULTS_DIR, load_hf_file, load_superbpe, load_domain,
                    write_json)
from superbpe import CHUNK_RE

DOMAINS = ["przetargi_ogloszenia", "przetargi_kio", "samorzad_uchwaly",
           "granty_ogloszenia", "prawo_eli", "ocr_prasa", "tabele_json",
           "web", "wikipedia", "literatura", "prawo", "sejm", "nauka",
           "dyskusje", "angielski"]
OFFICIAL = {"przetargi_ogloszenia", "przetargi_kio", "samorzad_uchwaly",
            "granty_ogloszenia", "prawo_eli", "ocr_prasa", "tabele_json"}
FEATURES = {
    "cyfry": re.compile(r"\d"),
    "4+_cyfry": re.compile(r"\d{4,}"),
    "kropka": re.compile(r"\."),
    "przecinek": re.compile(r","),
    "myslnik": re.compile(r"[-–]"),
    "ukosnik": re.compile(r"/"),
    "procent": re.compile(r"%"),
    "wielkie_litery": re.compile(r"[A-ZĄĆĘŁŃÓŚŹŻ]{2,}"),
    "skrot": re.compile(r"\b(?:art|ust|pkt|lit|Dz|U|M|P|poz|nr)\.", re.I),
    "wiele_spacji": re.compile(r"  +"),
    "dlugi_fragment": re.compile(r".{300,}"),
}


def main() -> None:
    tok = load_superbpe("tokenizers/tokenizatorex-32k.json")
    hf = load_hf_file(os.path.join(REPO_ROOT, "hf/tokenizatorex-32k/tokenizer.json"))
    out = {"meta": {"chunk_pattern": "CHUNK_PATTERN z superbpe.py", "split": "test",
                    "note": "parytet segmentacji liczony na ID (główny) i dodatkowo na zdekodowanych ciągach (kontrola utraty tekstu); tokeny bez specjalnych"},
           "domains": {}, "causes": {}, "h8": {}}

    for dom in DOMAINS:
        docs = load_domain(dom, "test")
        if not docs:
            continue
        total = identical = identical_decoded = 0
        ours_tokens = hf_tokens = 0
        feat_diff = Counter()
        feat_same = Counter()
        examples = []
        for d in docs:
            for ch in CHUNK_RE.findall(d["text"]):
                a = tok.encode_ordinary(ch)
                b = hf.encode(ch, add_special_tokens=False).ids
                total += 1
                ours_tokens += len(a)
                hf_tokens += len(b)
                same_ids = a == b
                a_str = tok.decode(a)
                b_str = hf.decode(b, skip_special_tokens=False)
                same_decoded = a_str == b_str
                identical_decoded += same_decoded
                same = same_ids
                identical += same
                bucket = feat_same if same else feat_diff
                for name, rx in FEATURES.items():
                    if rx.search(ch):
                        bucket[name] += 1
                if not same and len(examples) < 8 and 10 <= len(ch) <= 160:
                    examples.append({
                        "chunk": ch,
                        "ours": [tok.decode([i]) for i in a][:14],
                        "hf": [hf.decode([i], skip_special_tokens=False) for i in b][:14],
                        "tokens_ours": len(a), "tokens_hf": len(b)})
        share = identical / total if total else None
        se = (share * (1 - share) / total) ** 0.5 if total else None
        causes = {}
        for name in FEATURES:
            p_diff = feat_diff[name] / max(1, total - identical)
            p_same = feat_same[name] / max(1, identical)
            causes[name] = {"share_in_different": p_diff, "share_in_identical": p_same,
                            "lift": (p_diff / p_same) if p_same else None}
        out["domains"][dom] = {
            "chunks": total, "identical_chunks": identical,
            "identical_chunks_decoded": identical_decoded,
            "identical_share_decoded": (identical_decoded / total) if total else None,
            "identical_share": share,
            "identical_ci_wilson": _wilson(identical, total),
            "tokens_ours": ours_tokens, "tokens_hf": hf_tokens,
            "token_delta": hf_tokens - ours_tokens,
            "token_delta_pct": (hf_tokens - ours_tokens) / ours_tokens if ours_tokens else None,
            "causes": causes, "examples": examples,
            "official": dom in OFFICIAL,
        }
        print(f"{dom:<22} parytet ID {share:.4%} (ciągi {identical_decoded/total:.4%})  dT {hf_tokens-ours_tokens:+d}")

    out["causes"] = _global_causes(out["domains"])
    out["h8"] = _verdict(out["domains"])
    write_json(os.path.join(RESULTS_DIR, "hf_parity.json"), out)
    write_md(out)
    print("H8", out["h8"])


def _wilson(k: int, n: int) -> list[float]:
    if not n:
        return [float("nan"), float("nan")]
    z = 1.96
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / den
    return [centre - half, centre + half]


def _global_causes(domains: dict) -> dict:
    agg = {}
    for name in FEATURES:
        pd = ps = 0.0
        nd = ns = 0
        for r in domains.values():
            c = r["causes"][name]
            pd += c["share_in_different"]
            ps += c["share_in_identical"]
            nd += 1
            ns += 1
        agg[name] = {"mean_share_in_different": pd / nd, "mean_share_in_identical": ps / ns,
                     "lift": (pd / ps) if ps else None}
    return agg


def _verdict(domains: dict) -> dict:
    official = [r for r in domains.values() if r["official"]]
    web = domains.get("web")
    below = [d for d, r in domains.items() if r["official"] and r["identical_share"] < 0.99]
    o = sum(r["identical_chunks"] for r in official) / sum(r["chunks"] for r in official)
    if web:
        w = web["identical_share"]
        # przybliżony test dwóch proporcji
        se = ((o * (1 - o) / sum(r["chunks"] for r in official)) +
              (w * (1 - w) / web["chunks"])) ** 0.5
        z = (o - w) / se if se else 0.0
    else:
        z = float("nan")
    return {"official_parity": o, "web_parity": (web or {}).get("identical_share"),
            "official_domains_below_99": below,
            "z_official_vs_web": z,
            "confirmed": bool(below) and (z < -1.96)}


def write_md(out: dict) -> None:
    lines = ["# Parytet eksportu HF (test)", "",
             "| dziedzina | fragmentów | identyczne (ID) | identyczne (ciągi) | 95% CI | Δ tokenów | przyczyna #1 (lift) |",
             "|---|---:|---:|---:|---|---:|---|"]
    for d, r in out["domains"].items():
        ci = r["identical_ci_wilson"]
        top = max(r["causes"].items(), key=lambda kv: kv[1]["lift"] or 0)
        lines.append(f"| {d} | {r['chunks']:,} | {r['identical_share']:.3%} | "
                     f"{r['identical_share_decoded']:.3%} | [{ci[0]:.3%}; {ci[1]:.3%}] | "
                     f"{r['token_delta']:+,} ({r['token_delta_pct']:+.3%}) | {top[0]} "
                     f"({top[1]['lift']:.2f}×) |")
    lines += ["", "## Werdykt H8", ""]
    h = out["h8"]
    lines.append(f"* parytet urzędowy: {h['official_parity']:.3%}; web: {h['web_parity']:.3%}")
    lines.append(f"* dziedziny < 99%: {', '.join(h['official_domains_below_99']) or 'brak'}")
    lines.append(f"* H8: {'POTWIERDZONA' if h['confirmed'] else 'OBALONA'} "
                 f"(z = {h['z_official_vs_web']:.2f})")
    path = os.path.join(RESULTS_DIR, "hf_parity.md")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
