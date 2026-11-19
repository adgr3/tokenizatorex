"""Runda 1.5 — morfologia: MorphScore (arXiv 2507.06378) + spójność rdzenia.

Używa publicznego kodu MorphScore (commit 821fabf4692b6376cd9cf446a5e6fada7e61e608)
i publicznego zbioru `polish_data.csv` (UD_Polish-PDB, 42 545 pozycji).
SuperBPE oceniamy na izolowanych formach (tak działa oficjalny kod); to
ograniczenie opisujemy w raporcie.

Dodatkowo: dla 200 częstych lematów (rzeczowniki/czasowniki/przymiotniki)
odsetek form, w których pierwszy token jest wspólny z formą podstawową.

Wynik: audit/results/morphology.json (+ morphology.md)
"""
from __future__ import annotations

import importlib.util
import os
import sys
from collections import defaultdict

import numpy as np

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common import AUDIT_DIR, RESULTS_DIR, SEED, build_encoders, write_json

MORPHSCORE_CODE = os.path.join(AUDIT_DIR, "tmp", "morphscore", "morphscore.py")
MORPHSCORE_DATA = os.path.join(AUDIT_DIR, "tmp", "polish_data.csv")
MORPHSCORE_COMMIT = "821fabf4692b6376cd9cf446a5e6fada7e61e608"


class Adapter:
    """Minimalny interfejs tokenizera wymagany przez MorphScore."""

    special_tokens_map: dict = {}

    def __init__(self, enc):
        self.enc = enc

    def __call__(self, text: str):
        return {"input_ids": self.enc.ids(text)}

    def decode(self, ids):
        if isinstance(ids, int):
            ids = [ids]
        return self.enc.decode(ids)


def load_morphscore():
    spec = importlib.util.spec_from_file_location("morphscore_ext", MORPHSCORE_CODE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.MorphScore


def main() -> None:
    import pandas as pd

    MorphScore = load_morphscore()
    df = pd.read_csv(MORPHSCORE_DATA)
    df = df[df["unique"] == "unique"] if "unique" in df.columns else df
    df = df[~df["wordform"].astype(str).str.contains(r"\d", regex=True)]
    df = df[df["stem"] == df["lemma"]]
    encoders = build_encoders()

    out = {"meta": {"morphscore_commit": MORPHSCORE_COMMIT,
                    "dataset": "catherinearnett/morphscore polish_data.csv (UD_Polish-PDB)",
                    "items_after_filter": int(len(df)),
                    "seed": SEED,
                    "note": "MorphScore liczony na izolowanych formach; SuperBPE może "
                            "dzielić inaczej w kontekście (ograniczenie metody)."},
           "morphscore": {}, "core_consistency": {}}

    for label, enc in encoders.items():
        row = {}
        for cfg_name, cfg in (("default_paper", {"freq_scale": True, "exclude_single_tok": True}),
                              ("all_words", {"freq_scale": False, "exclude_single_tok": False})):
            ms = MorphScore(**cfg)
            r = ms.get_morphscore(df, Adapter(enc))
            row[cfg_name] = {k: (float(v) if isinstance(v, (int, float, np.floating)) else v)
                             for k, v in r.items()}
        out["morphscore"][label] = row
        print(f"{label:<20} precision {row['default_paper']['morphscore_precision']:.3f} "
              f"recall {row['default_paper']['morphscore_recall']:.3f}")

    # --- spójność rdzenia ---------------------------------------------------
    pos_map = {"NOUN": "rzeczowniki", "VERB": "czasowniki", "ADJ": "przymiotniki"}
    sub = df[df["pos"].isin(pos_map)]
    agg = sub.groupby(["lemma", "pos"])["word_freq"].sum().reset_index()
    top = agg.sort_values("word_freq", ascending=False)
    chosen = []
    for pos in pos_map:
        chosen += top[top["pos"] == pos].head(200).values.tolist()
    chosen = chosen[:600]

    core = {}
    for label, enc in encoders.items():
        per_pos = defaultdict(lambda: {"total": 0, "same_first": 0, "forms": 0})
        for lemma, pos, _freq in chosen:
            forms = sub[(sub["lemma"] == lemma) & (sub["pos"] == pos)]
            if forms.empty:
                continue
            counts = forms["wordform"].value_counts()
            base = lemma if lemma in counts.index else counts.index[0]
            base_first = _first_token(enc, str(base))
            per_pos[pos]["forms"] += 1
            for form in counts.index:
                per_pos[pos]["total"] += 1
                if _first_token(enc, str(form)) == base_first:
                    per_pos[pos]["same_first"] += 1
        core[label] = {pos_map[p]: {
            "lemmas": v["forms"], "forms": v["total"],
            "share_same_first_token": v["same_first"] / v["total"] if v["total"] else None,
        } for p, v in per_pos.items()}
        total = sum(v["total"] for v in per_pos.values())
        same = sum(v["same_first"] for v in per_pos.values())
        core[label]["overall"] = same / total if total else None
        print(f"   rdzeń {label:<20} {core[label]['overall']:.3f}")
    out["core_consistency"] = core

    write_json(os.path.join(RESULTS_DIR, "morphology.json"), out)
    write_md(out)


def _first_token(enc, word: str) -> str:
    ids = enc.ids(word)
    return enc.decode([ids[0]]) if ids else ""


def write_md(out: dict) -> None:
    labs = list(out["morphscore"])
    lines = ["# Morfologia (UD_Polish-PDB)", "",
             f"Kod MorphScore: `{MORPHSCORE_COMMIT[:12]}`; pozycji po filtrze: "
             f"{out['meta']['items_after_filter']}.", "",
             "## MorphScore (paper default: freq_scale=True, bez słów 1-tokenowych)", "",
             "| tokenizer | precision | recall | micro F1 | mean token/char |",
             "|---|---:|---:|---:|---:|"]
    for l in labs:
        r = out["morphscore"][l]["default_paper"]
        lines.append(f"| {l} | {r['morphscore_precision']:.3f} | {r['morphscore_recall']:.3f} | "
                     f"{r['micro_f1']:.3f} | {r['mean_token_char_ratio']:.3f} |")
    lines += ["", "## Spójność rdzenia (pierwszy token wspólny z formą podstawową)", "",
              "| tokenizer | rzeczowniki | czasowniki | przymiotniki | razem |",
              "|---|---:|---:|---:|---:|"]
    for l in labs:
        c = out["core_consistency"][l]
        lines.append(f"| {l} | {c['rzeczowniki']['share_same_first_token']:.3f} | "
                     f"{c['czasowniki']['share_same_first_token']:.3f} | "
                     f"{c['przymiotniki']['share_same_first_token']:.3f} | {c['overall']:.3f} |")
    lines += ["", "Zgodność z morfologią słabo przewiduje jakość modelu (R² ≈ 0,02); "
                  "raportujemy, ale nie optymalizujemy na ślepo."]
    path = os.path.join(RESULTS_DIR, "morphology.md")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("zapisano", path)


if __name__ == "__main__":
    main()
