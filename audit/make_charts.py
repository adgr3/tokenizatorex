"""Wykresy do raportu końcowego (PNG, każdy z tezą, miarą i ustawieniami)."""
from __future__ import annotations

import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common import AUDIT_DIR, RESULTS_DIR  # noqa: E402

FIG = os.path.join(AUDIT_DIR, "figures")
os.makedirs(FIG, exist_ok=True)
DOMS = ["przetargi_ogloszenia", "przetargi_kio", "samorzad_uchwaly",
        "granty_ogloszenia", "prawo_eli", "ocr_prasa", "tabele_json",
        "web", "wikipedia", "nauka"]
LABELS = {"przetargi_ogloszenia": "przetargi\nogłoszenia", "przetargi_kio": "KIO",
          "samorzad_uchwaly": "uchwały\nsamorządu", "granty_ogloszenia": "granty",
          "prawo_eli": "prawo\n(ELI)", "ocr_prasa": "OCR\nprasa",
          "tabele_json": "tabele\nJSON", "web": "web", "wikipedia": "Wikipedia",
          "nauka": "nauka"}
COLS = {"TOKENIZATOREX": "#1d4ed8", "TOKENIZATOREX-HF": "#60a5fa",
        "Slayer1B": "#dc2626", "Pollock-2.0": "#f59e0b", "APT3-1B": "#7c3aed",
        "GPT-4o": "#6b7280"}


def j(name):
    return json.load(open(os.path.join(RESULTS_DIR, name), encoding="utf-8"))


def footer(fig, text):
    fig.text(0.01, 0.01, text, fontsize=7, color="#6b7280", ha="left")


def head(fig, title, subtitle):
    fig.text(0.01, 0.975, title, fontsize=13, fontweight="bold", va="top")
    fig.text(0.01, 0.905, subtitle, fontsize=8.5, color="#4b5563", va="top")


def chart_fertility():
    d = j("fertility.json")
    labs = ["TOKENIZATOREX", "TOKENIZATOREX-HF", "Slayer1B", "Pollock-2.0"]
    fig, ax = plt.subplots(figsize=(14, 6.5))
    n = len(DOMS)
    w = 0.19
    for k, lab in enumerate(labs):
        xs, ys, lo, hi = [], [], [], []
        for i, dom in enumerate(DOMS):
            if dom not in d["domains"]:
                continue
            v = d["domains"][dom]["tokenizers"][lab]
            xs.append(i + (k - 1.5) * w)
            ys.append(v["fertility"])
            lo.append(v["fertility"] - v["fertility_ci"][0])
            hi.append(v["fertility_ci"][1] - v["fertility"])
        ax.errorbar(xs, ys, yerr=[lo, hi], fmt="o", ms=4, capsize=2,
                    color=COLS[lab], label=lab)
    ax.set_xticks(range(n))
    ax.set_xticklabels([LABELS.get(x, x) for x in DOMS], fontsize=9)
    ax.set_ylabel("tokeny na słowo (mniej = lepiej)")
    head(fig, "TOKENIZATOREX jest najlepszy na 7 z 10 dziedzin; istotnie przegrywa\n"
              "tylko w Wikipedii (Pollock) i nauce (APT3)",
         "Miara: fertility = tokeny / słowo (str.split), test 60% dokumentów, "
         "słupki błędu = 95% bootstrap po dokumentach")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(ncol=4, fontsize=9, frameon=False)
    fig.tight_layout(rect=(0, 0.04, 1, 0.87))
    footer(fig, "Dane: audit/results/fertility.json · tokenizery bez tokenów specjalnych · "
                "seed 20261119 · 1000 bootstrapów · APT3/Pollock/Bielik/PLLuM/GPT-4o w JSON")
    fig.savefig(os.path.join(FIG, "01_fertility_dziedziny.png"), dpi=150)
    plt.close(fig)


def chart_years():
    d = j("notations.json")
    years = [str(y) for y in range(2015, 2027)]
    fig, ax = plt.subplots(figsize=(11, 5.6))
    for lab in ["TOKENIZATOREX", "TOKENIZATOREX-HF", "Slayer1B"]:
        ys = [d["h1"]["years"][y].get(lab, {}).get("tokens_mean") for y in years]
        ax.plot(years, ys, marker="o", ms=4, label=lab, color=COLS[lab])
    ax.axvspan(-0.2, 9.2, color="#e5e7eb", alpha=0.5)
    ax.text(4.5, ax.get_ylim()[1] * 0.95, "lata prawdopodobnie w danych treningowych",
            ha="center", fontsize=8, color="#374151")
    ax.set_ylabel("średnia liczba tokenów na wystąpienie roku")
    head(fig, "Kalendarz zamrożony: 2015–2024 to 1 token, 2025–2026 to 2 tokeny",
         "Miara: tokeny na samo wystąpienie roku w korpusie testowym "
         "(Dz.U. + ogłoszenia), średnia; szablon kontrolny w JSON")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout(rect=(0, 0.05, 1, 0.86))
    footer(fig, "Dane: audit/results/notations.json · test · seed 20261119 · "
                "wystąpienia lat z 2026 r. w dziedzinach urzędowych")
    fig.savefig(os.path.join(FIG, "02_koszt_lat_2015_2026.png"), dpi=150)
    plt.close(fig)


def chart_robustness():
    d = j("robustness.json")
    variants = list(d["aggregate"]["variants"])
    labs = ["TOKENIZATOREX", "TOKENIZATOREX-base", "Slayer1B", "APT3-1B", "GPT-4o"]
    fig, ax = plt.subplots(figsize=(13, 6.2))
    w = 0.15
    for k, lab in enumerate(labs):
        ys = [d["aggregate"]["variants"][v]["tokenizers"][lab]["relative_increase_mean"] * 100
              for v in variants]
        ax.bar([i + (k - 2) * w for i in range(len(variants))], ys, width=w,
               color=COLS.get(lab, "#999"), label=lab)
    ax.axhline(25, color="#111827", ls="--", lw=1)
    ax.text(len(variants) - 0.5, 26, "próg słabości 25%", ha="right", fontsize=8)
    ax.set_xticks(range(len(variants)))
    ax.set_xticklabels(variants, rotation=20, ha="right")
    ax.set_ylabel("wzrost liczby tokenów vs czysty tekst [%]")
    head(fig, "Odporność: NFD +46%, CAPS +107%, tytuły +31%; APT3 nie cierpi na NFD,\n"
              "bo normalizuje wejście (stratnie)",
         "Miara: średni względny wzrost tokenów po dziedzinach urzędowych "
         "(7 dziedzin, po 25 dok.); 95% CI w JSON")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(ncol=5, fontsize=8.5, frameon=False)
    fig.tight_layout(rect=(0, 0.05, 1, 0.86))
    footer(fig, "Dane: audit/results/robustness.json · test · seed 20261119 · "
                "literówki/OCR: podmiany 2%/5% · NFD bez NFC")
    fig.savefig(os.path.join(FIG, "03_odpornosc.png"), dpi=150)
    plt.close(fig)


def chart_parity():
    d = j("hf_parity.json")
    doms = [x for x in DOMS if x in d["domains"]]
    vals = [d["domains"][x]["identical_share"] * 100 for x in doms]
    cols = ["#1d4ed8" if d["domains"][x]["official"] else "#9ca3af" for x in doms]
    fig, ax = plt.subplots(figsize=(12, 5.6))
    ax.bar(range(len(doms)), vals, color=cols)
    ax.axhline(99, color="#dc2626", ls="--", lw=1)
    ax.text(len(doms) - 0.4, 99.15, "próg 99%", ha="right", fontsize=8, color="#dc2626")
    ax.set_xticks(range(len(doms)))
    ax.set_xticklabels([LABELS.get(x, x) for x in doms], fontsize=8.5)
    ax.set_ylim(90, 100)
    ax.set_ylabel("% fragmentów z identyczną segmentacją")
    head(fig, "Eksport HF nie jest 1:1: 97,3% na dziedzinach urzędowych vs 99,4% na web",
         "Miara: odsetek fragmentów (CHUNK_PATTERN) o identycznych tokenach "
         "w superbpe.py i eksporcie HF; niebieski = dziedzina urzędowa")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout(rect=(0, 0.05, 1, 0.86))
    footer(fig, "Dane: audit/results/hf_parity.json · test · bez tokenów specjalnych · "
                "te same fragmenty dla obu enkoderów")
    fig.savefig(os.path.join(FIG, "04_parytet_hf.png"), dpi=150)
    plt.close(fig)


def chart_vocab():
    d = j("vocab_usage.json")
    labs = list(d["tokenizers"])
    vals = [d["tokenizers"][l]["renyi"]["renyi_efficiency"] * 1000 for l in labs]
    fig, ax = plt.subplots(figsize=(11, 5.2))
    ax.bar(range(len(labs)), vals, color=[COLS.get(l, "#999") for l in labs])
    ax.set_xticks(range(len(labs)))
    ax.set_xticklabels(labs, rotation=25, ha="right", fontsize=8.5)
    ax.set_ylabel("Rényi efficiency ×1000 (α = 2,5)")
    head(fig, "Słownik TOKENIZATOREX jest w pełni wykorzystany: Rényi 7,4‰,\n"
              "wyżej niż Slayer1B 2,7‰ i Pollock 1,6‰",
         "Miara: exp(H_α)/|V|, α = 2,5, częstości tokenów na korpusie testowym; "
         "wyżej = lepsze wykorzystanie słownika")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout(rect=(0, 0.05, 1, 0.86))
    footer(fig, "Dane: audit/results/vocab_usage.json · test · tokeny specjalne pominięte")
    fig.savefig(os.path.join(FIG, "05_renyi.png"), dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    chart_fertility()
    chart_years()
    chart_robustness()
    chart_parity()
    chart_vocab()
    print("wykresy w", FIG)
