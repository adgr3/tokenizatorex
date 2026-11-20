"""Wykresy TKX-C (PNG, tytuł = wniosek, podtytuł = miara, stopka = ustawienia)."""
from __future__ import annotations

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "tkx_c", "results")
FIG = os.path.join(ROOT, "tkx_c", "figures")
os.makedirs(FIG, exist_ok=True)
COLS = {"V0-32k": "#6b7280", "V1-32k": "#1d4ed8", "V2-32k": "#16a34a",
        "V2-24k": "#f59e0b", "V2-16k": "#dc2626",
        "V2b-32k": "#7c3aed", "V3-32k": "#0891b2"}


def j(name):
    return json.load(open(os.path.join(RES, name), encoding="utf-8"))


def head(fig, title, subtitle):
    fig.text(0.01, 0.975, title, fontsize=13, fontweight="bold", va="top")
    fig.text(0.01, 0.905, subtitle, fontsize=8.5, color="#4b5563", va="top")


def footer(fig, text):
    fig.text(0.01, 0.01, text, fontsize=7, color="#6b7280")


def chart_calendar():
    d = j("calendar.json")
    years = [int(y) for y in d["years"]]
    fig, ax = plt.subplots(figsize=(12, 5.4))
    for v, col in (("V0-32k", COLS["V0-32k"]), ("V1-32k", COLS["V1-32k"]),
                   ("V2-32k", COLS["V2-32k"]), ("V2b-32k", COLS["V2b-32k"]),
                   ("V3-32k", COLS["V3-32k"])):
        ax.plot(years, [d["variants"][v][str(y)] for y in years], marker="o",
                ms=3, label=v, color=col)
    ax.set_ylabel("tokeny w zdaniu `w roku RRRR r. zadanie`")
    ax.set_xticks(years[::2])
    ax.tick_params(axis="x", rotation=45)
    head(fig, "Kalendarz: V0 ma schodki 4/5/6, V1/V2/V2b/V3 są płaskie 2015–2035",
         "Miara: liczba tokenów zdania-kontrolnego; kanoniczny eksport HF; "
         "V2b i V3 dodane post hoc (decyzja właściciela 20.11)")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout(rect=(0, 0.05, 1, 0.86))
    footer(fig, "Dane: tkx_c/results/calendar.json · kanoniczny HF · seed 20261119")
    fig.savefig(os.path.join(FIG, "01_kalendarz.png"), dpi=150)
    plt.close(fig)


def chart_digits():
    d = j("digits_cost.json")
    doms = list(d["domains"])
    vals = [d["domains"][x]["delta_pct"] * 100 for x in doms]
    ci = np.array([
        [c / (d["domains"][x]["tokens_v0"] / d["domains"][x]["words"]) * 100
         for c in d["domains"][x]["delta_ci"]]
        for x in doms])
    lo = np.array([v - c[0] for v, c in zip(vals, ci)])
    hi = np.array([c[1] - v for v, c in zip(vals, ci)])
    aud_lo = [d["domains"][x]["audit_lower_pct"] * 100 for x in doms]
    aud_hi = [d["domains"][x]["audit_upper_pct"] * 100 for x in doms]
    fig, ax = plt.subplots(figsize=(13, 6))
    x = np.arange(len(doms))
    ax.bar(x, vals, color=COLS["V1-32k"], alpha=0.85, label="V1 vs V0 (prawdziwy)")
    ax.errorbar(x, vals, yerr=[lo, hi], fmt="none", ecolor="#111827", capsize=3)
    for i, (a, b) in enumerate(zip(aud_lo, aud_hi)):
        ax.plot([i - 0.18, i + 0.18], [a, a], color="#dc2626", lw=2)
        ax.plot([i - 0.18, i + 0.18], [b, b], color="#dc2626", lw=2)
        ax.plot([i, i], [a, b], color="#dc2626", lw=1)
    ax.scatter([], [], color="#dc2626", marker="_", label="przedział audytu (dolna–górna)")
    ax.set_xticks(x)
    ax.set_xticklabels(doms, rotation=30, ha="right", fontsize=8.5)
    ax.set_ylabel("wzrost tokenów V1 vs V0 [%]")
    head(fig, "Prawdziwy koszt pojedynczych cyfr: +14,0% na 7 dziedzinach urzędowych,\n"
              "w górnej części przedziału audytu",
         "Miara: różnica tokenów V1−V0 / V0 na teście, słupki błędu = 95% bootstrap "
         "po dokumentach; czerwone kreski = dolna/górna granica z audytu")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout(rect=(0, 0.05, 1, 0.86))
    footer(fig, "Dane: tkx_c/results/digits_cost.json · test TKX-A · kanoniczny HF · "
                "1000 bootstrapów · seed 20261119")
    fig.savefig(os.path.join(FIG, "02_koszt_cyfr.png"), dpi=150)
    plt.close(fig)


def chart_nfd():
    d = j("nfd.json")
    doms = list(d["domains"])
    labs = ["V0-32k", "V1-32k", "V2-32k", "V2b-32k", "V3-32k"]
    fig, ax = plt.subplots(figsize=(13, 5.6))
    w = 0.16
    for k, v in enumerate(labs):
        vals = [d["domains"][x]["variants"][v]["increase"] * 100 for x in doms]
        ax.bar([i + (k - 2) * w for i in range(len(doms))], vals, width=w,
               label=v, color=COLS[v])
    ax.set_xticks(range(len(doms)))
    ax.set_xticklabels(doms, rotation=30, ha="right", fontsize=8.5)
    ax.set_ylabel("wzrost tokenów NFD vs NFC [%]")
    head(fig, "NFC w potoku usuwa koszt PDF: V2/V2b/V3 +0,0%, V0 +45,4%",
         "Miara: (tokeny(tekst NFD) − tokeny(tekst NFC)) / tokeny(NFC), "
         "7 dziedzin urzędowych; słupki = punktowa różnica")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout(rect=(0, 0.05, 1, 0.86))
    footer(fig, "Dane: tkx_c/results/nfd.json · test TKX-A · kanoniczny HF · "
                "V2 normalizuje wejście do NFC przed kodowaniem")
    fig.savefig(os.path.join(FIG, "03_nfd.png"), dpi=150)
    plt.close(fig)


def chart_context():
    d = j("context.json")
    doms = list(d["domains"])
    labs = ["V0-32k", "V2-32k", "V2-16k"]
    fig, ax = plt.subplots(figsize=(12, 5.8))
    w = 0.26
    for k, v in enumerate(labs):
        vals = [d["domains"][x]["variants"][v]["median"] for x in doms]
        ax.bar([i + (k - 1) * w for i in range(len(doms))], vals, width=w,
               label=v, color=COLS[v])
        for i, val in enumerate(vals):
            ax.text(i + (k - 1) * w, val, f"{val:,.0f}", ha="center",
                    va="bottom", fontsize=7, rotation=90)
    ax.axhline(2048, color="#111827", ls="--", lw=1)
    ax.axhline(4096, color="#dc2626", ls="--", lw=1)
    ax.text(len(doms) - 0.5, 2048, "2048", ha="right", va="bottom", fontsize=8)
    ax.text(len(doms) - 0.5, 4096, "4096", ha="right", va="bottom", fontsize=8,
            color="#dc2626")
    ax.set_yscale("log")
    ax.set_xticks(range(len(doms)))
    ax.set_xticklabels(doms, rotation=20, ha="right", fontsize=8.5)
    ax.set_ylabel("mediana tokenów pełnego dokumentu (skala log)")
    head(fig, "Pełne ogłoszenie i uchwała nie mieszczą się w 2048; KIO zwykle tak.\n"
              "Po cyfrach mediana ogłoszenia rośnie z 3 883 do 4 536 tokenów",
         "Miara: mediana tokenów kanonicznego HF na pełnych dokumentach bez cięcia "
         "20 tys. znaków (świeża próbka 20 dok./dziedzinę)")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout(rect=(0, 0.05, 1, 0.86))
    footer(fig, "Dane: tkx_c/results/context.json · pełne dokumenty z tych samych "
                "źródeł, nie test TKX-A · 20 dok./dziedzinę")
    fig.savefig(os.path.join(FIG, "04_kontekst.png"), dpi=150)
    plt.close(fig)


def chart_variants():
    d = j("digits_cost_new.json")
    doms = list(d["domains"]["V2-32k"])
    labs = ["V2-32k", "V2b-32k", "V3-32k"]
    fig, ax = plt.subplots(figsize=(13, 5.8))
    w = 0.26
    for k, v in enumerate(labs):
        vals = [d["domains"][v][x]["delta_pct"] * 100 for x in doms]
        ax.bar([i + (k - 1) * w for i in range(len(doms))], vals, width=w,
               label=v, color=COLS[v])
    ax.axhline(0, color="#111827", lw=0.8)
    ax.set_xticks(range(len(doms)))
    ax.set_xticklabels(doms, rotation=30, ha="right", fontsize=8.5)
    ax.set_ylabel("wzrost tokenów vs V0 [%]")
    o = {v: d["official"][v]["delta_pct"] * 100 for v in labs}
    head(fig, "V2b i V3 tną liczby taniej niż V2; wybór ostateczny w TKX-D na BPB",
         f"Miara: (tokeny wariantu − tokeny V0) / V0, 7 dziedzin urzędowych; "
         f"urzędowe razem: V2 {o['V2-32k']:+.1f}%, V2b {o['V2b-32k']:+.1f}%, "
         f"V3 {o['V3-32k']:+.1f}%")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout(rect=(0, 0.05, 1, 0.86))
    footer(fig, "Dane: tkx_c/results/digits_cost_new.json · test TKX-A · kanoniczny HF · "
                "bootstrap 1000× · seed 20261119 (post hoc)")
    fig.savefig(os.path.join(FIG, "05_varianty.png"), dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    chart_calendar()
    chart_digits()
    chart_nfd()
    chart_context()
    chart_variants()
    print("wykresy w", FIG)
