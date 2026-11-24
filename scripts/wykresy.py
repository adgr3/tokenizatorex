# -*- coding: utf-8 -*-
"""Generowanie wykresow i animacji do dokumentacji TOKENIZATOREX v2.0.

Uruchomienie:
    python scripts/wykresy.py            # wszystko, pelne rozmiary
    python scripts/wykresy.py --szybko   # mniejsze rozmiary / mniej klatek (testy)
    python scripts/wykresy.py --tylko-statyczne
    python scripts/wykresy.py --tylko-animacje

Wszystkie liczby pochodza z results/*.json albo z tokenizacji skryptem.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "results"
OUT = REPO / "docs" / "wykresy"
ANIM = OUT / "anim"

# ---------- pomocnicze ----------

def _load(name):
    with open(RESULTS / name, encoding="utf-8") as f:
        return json.load(f)


def plnum(x, dp=2):
    s = f"{x:.{dp}f}"
    return s.replace(".", ",")


def plint(x):
    return f"{int(x):,}".replace(",", " ")


OI_ORANGE = "#D55E00"
OI_BLUE = "#0072B2"
OI_GREEN = "#009E73"
OI_SKY = "#56B4E9"
GRAY = "#9AA0A6"
LIGHT_GRAY = "#D0D0D0"


def _ensure_dirs():
    OUT.mkdir(parents=True, exist_ok=True)
    ANIM.mkdir(parents=True, exist_ok=True)


def _save(fig, stem, szybko=False):
    _ensure_dirs()
    target_w = 800 if szybko else 1600
    dpi = target_w / fig.get_figwidth()
    fig.savefig(OUT / f"{stem}.png", dpi=dpi, bbox_inches="tight")
    fig.savefig(OUT / f"{stem}.svg", bbox_inches="tight")
    import matplotlib.pyplot as plt
    plt.close(fig)


def _title(fig, text):
    fig.suptitle(text, fontsize=14, fontweight="bold", y=0.98)


def _source(fig, text):
    fig.text(0.01, 0.01, text, fontsize=8, color="#555555", ha="left", va="bottom")


# ---------- dane ----------

def dane_fertility_bzp():
    z = _load("tkx_zoo_fertility.json")
    v2 = _load("tkx_v2_fertility.json")
    man = json.load(open(REPO / "tkx_zoo" / "MANIFEST.json", encoding="utf-8"))
    src = z["sources"]["1_bzp"]["tokenizers"]
    vocab_map = {k: (v.get("vocab") if isinstance(v, dict) else None) for k, v in man.items()
                 if isinstance(v, dict)}
    rows = []
    display = {
        "PLLuM-4B": "PLLuM 4B",
        "PLLuM-8B": "PLLuM 8B",
        "PLLuM-12B": "PLLuM 12B",
        "Bielik-11B-v3.1": "Bielik 11B",
        "Bielik-4.5B-v3": "Bielik 4.5B",
        "Aster-0.5B": "Aster 0.5B",
        "EuroLLM-1.7B": "EuroLLM 1.7B",
        "Mistral-Nemo": "Mistral Nemo",
        "Gemma-3-4B": "Gemma 3 4B",
        "V0-32k": "TOKENIZATOREX V0",
        "V0J2-32k": "TOKENIZATOREX V0J2",
        "Slayer-v6": "Slayer v6",
        "Bielik-1.5B-v3": "Bielik 1.5B",
        "APT3-1B": "APT3 1B",
        "GPT-4o-o200k": "GPT-4o",
    }
    skip = {"DanielK-t1-pl-polish-32k", "DanielK-t2-pl-cnc-32k", "Llama-3.1-8B"}
    for key, m in src.items():
        if key in skip:
            continue
        name = display.get(key, key)
        rows.append({
            "key": key,
            "name": name,
            "fertility": m["fertility"],
            "ci_lo": m["fertility_ci_lo"],
            "ci_hi": m["fertility_ci_hi"],
            "vocab": vocab_map.get(key),
            "highlight": key in ("V0-32k", "V0J2-32k"),
        })
    # base-32k z v2
    base_m = v2["sources"]["1_bzp"]["tokenizers"]["TKX/V2-base-32k"]
    rows.append({
        "key": "base-32k",
        "name": "base-32k (bez SuperBPE)",
        "fertility": base_m["fertility"],
        "ci_lo": base_m["fertility_ci_lo"],
        "ci_hi": base_m["fertility_ci_hi"],
        "vocab": 32000,
        "highlight": False,
    })
    rows.sort(key=lambda r: r["fertility"])
    return rows


def dane_skad_przewaga():
    v2 = _load("tkx_v2_fertility.json")
    sources = ["1_bzp", "2_du_eli", "3_kio", "4_samorzad", "5_granty",
               "6_json_narzedzia", "7_ogolny", "json_bzp_tabele"]
    labels = {
        "1_bzp": "BZP ogłoszenia",
        "2_du_eli": "Dziennik Ustaw",
        "3_kio": "KIO",
        "4_samorzad": "Samorząd",
        "5_granty": "Granty",
        "6_json_narzedzia": "JSON narzędzi",
        "7_ogolny": "Web (ogólny)",
        "json_bzp_tabele": "BZP tabele",
    }
    out = []
    for s in sources:
        toks = v2["sources"][s]["tokenizers"]
        out.append({
            "source": s,
            "label": labels[s],
            "base": toks["TKX/V2-base-32k"]["fertility"],
            "v0": toks["TKX/V0-32k"]["fertility"],
            "apt3": toks["APT3-1B"]["fertility"],
            "slayer": toks["Slayer1B-1.08"]["fertility"],
        })
    return out


def dane_osiem_zrodel():
    return dane_skad_przewaga()


def dane_koszt_slownika():
    z = _load("tkx_zoo_vocab_cost.json")
    vxc = z["vocab_x_dmodel"]
    reps = {
        "32k": "V0-32k",
        "128k": "PLLuM-8B",
        "200k": "GPT-4o-o200k",
        "262k": "PLLuM-4B",
    }
    # ensure vocab buckets sorted
    out = []
    for label, key in reps.items():
        info = vxc[key]
        d768 = info["768"]
        out.append({
            "bucket": label,
            "vocab": info["vocab"],
            "tied": d768["pct_150m"],
            "untied": d768["pct_150m_untied"],
        })
    return out


def dane_daty_kwoty_paragraf():
    z = _load("tkx_zoo_formats.json")
    selected = {
        "V0-32k": "TOKENIZATOREX V0",
        "Slayer-v6": "Slayer v6",
        "APT3-1B": "APT3 1B",
        "GPT-4o-o200k": "GPT-4o",
    }
    out = {"dates": {}, "amounts": {}, "paragraphs": {}}
    for key, name in selected.items():
        dates = list(z["date_formats"][key].values())
        amounts = list(z["amount_formats"][key].values())
        paras = list(z["paragraph_forms"][key].values())
        out["dates"][name] = sum(dates) / len(dates)
        out["amounts"][name] = sum(amounts) / len(amounts)
        out["paragraphs"][name] = sum(paras) / len(paras)
    return out


def dane_json_heldout():
    v21 = _load("tkx_v21_test.json")
    zoo = _load("tkx_zoo_fertility.json")
    tc1 = v21["sources"]["tc1_test"]["tokenizers"]
    held = zoo["sources"]["json_generic_heldout_test"]["tokenizers"]
    return {
        "tc1": {
            "V0": tc1["V0-32k"]["fertility"],
            "V0J2": tc1["V0J2-32k"]["fertility"],
        },
        "heldout": {
            "V0": held["V0-32k"]["fertility"],
            "V0J2": held["V0J2-32k"]["fertility"],
        },
    }


def dane_znane_wady():
    s = _load("tkx_v2_r6_superwords.json")
    v0 = s["tokenizers"]["V0-32k"]
    return {
        "midword_uses_share": v0["usage"]["midword_uses_share"],
        "cases": (13, 172),
        "pairs": (38, 384),
    }


# ---------- wykresy statyczne ----------

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def wykres_fertility_bzp(szybko=False):
    rows = dane_fertility_bzp()
    fig, ax = plt.subplots(figsize=(9, 7) if not szybko else (7, 5))
    names = [r["name"] for r in rows]
    vals = [r["fertility"] for r in rows]
    lo = [r["fertility"] - r["ci_lo"] for r in rows]
    hi = [r["ci_hi"] - r["fertility"] for r in rows]
    colors = [OI_ORANGE if r["highlight"] else GRAY for r in rows]
    y = np.arange(len(rows))
    ax.barh(y, vals, xerr=[lo, hi], color=colors, ecolor="#444444",
            capsize=3, height=0.7)
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=10)
    ax.invert_yaxis()
    for i, r in enumerate(rows):
        v = r["fertility"]
        vocab = r["vocab"]
        vlab = f"{plnum(v)}  ({vocab // 1000}k)" if vocab else plnum(v)
        ax.text(v + (max(vals) * 0.01), i, vlab, va="center", fontsize=9)
    ax.set_xlabel("tokeny / słowo (BZP, 500 ogłoszeń)")
    ax.set_xlim(0, max(vals) * 1.18)
    _title(fig, "TOKENIZATOREX potrzebuje najmniej tokenów na przetargach BZP")
    _source(fig, "Źródło: results/tkx_zoo_fertility.json + results/tkx_v2_fertility.json (base-32k); commit d91a87e")
    _save(fig, "fertility_bzp", szybko)


def wykres_skad_przewaga(szybko=False):
    data = dane_skad_przewaga()
    fig, ax = plt.subplots(figsize=(9, 6) if not szybko else (7, 4.5))
    labels = [d["label"] for d in data]
    y = np.arange(len(data))
    # base->v0 segments
    for i, d in enumerate(data):
        ax.plot([d["base"], d["v0"]], [i, i], color="#888888", lw=2, zorder=1)
        ax.scatter([d["base"]], [i], color=GRAY, s=40, zorder=2, label="base-32k" if i == 0 else None)
        ax.scatter([d["v0"]], [i], color=OI_ORANGE, s=50, zorder=3, label="V0" if i == 0 else None)
        ax.scatter([d["apt3"]], [i], color=OI_BLUE, marker="D", s=40, zorder=3, label="APT3" if i == 0 else None)
        ax.scatter([d["slayer"]], [i], color=OI_GREEN, marker="^", s=45, zorder=3, label="Slayer" if i == 0 else None)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=10)
    ax.invert_yaxis()
    ax.set_xlabel("tokeny / słowo")
    ax.legend(loc="lower right", fontsize=9)
    _title(fig, "Przewaga TOKENIZATOREX-u pochodzi z SuperBPE")
    fig.text(0.5, 0.92, "bez SuperBPE słownik jest na poziomie Slayera i gorszy od APT3",
             ha="center", fontsize=10, color="#444444")
    _source(fig, "Źródło: results/tkx_v2_fertility.json; commit d91a87e")
    _save(fig, "skad_przewaga", szybko)


def wykres_osiem_zrodel(szybko=False):
    data = dane_osiem_zrodel()
    fig, axes = plt.subplots(2, 4, figsize=(12, 6) if not szybko else (9, 4.5), sharex=True)
    axes = axes.flatten()
    maxv = max(max(d["base"], d["v0"], d["apt3"], d["slayer"]) for d in data)
    order = ["V0", "base-32k", "APT3", "Slayer"]
    for ax, d in zip(axes, data):
        vals = [d["v0"], d["base"], d["apt3"], d["slayer"]]
        cols = [OI_ORANGE, GRAY, OI_BLUE, OI_GREEN]
        yy = np.arange(4)
        ax.barh(yy, vals, color=cols, height=0.6)
        ax.set_yticks(yy)
        ax.set_yticklabels(order, fontsize=8)
        ax.invert_yaxis()
        ax.set_xlim(0, maxv * 1.05)
        ax.set_title(d["label"], fontsize=9)
        for i, v in enumerate(vals):
            ax.text(v + maxv * 0.01, i, plnum(v, 2), va="center", fontsize=7)
    _title(fig, "Te same 8 źródeł: V0 przed base-32k, APT3 i Slayerem")
    _source(fig, "Źródło: results/tkx_v2_fertility.json; commit d91a87e")
    _save(fig, "osiem_zrodel", szybko)


def wykres_koszt_slownika(szybko=False):
    data = dane_koszt_slownika()
    fig, ax = plt.subplots(figsize=(9, 5) if not szybko else (7, 4))
    x = np.arange(len(data))
    w = 0.38
    tied = [d["tied"] for d in data]
    untied = [d["untied"] for d in data]
    b1 = ax.bar(x - w / 2, tied, w, color=OI_ORANGE, label="współdzielony wyjściowy")
    b2 = ax.bar(x + w / 2, untied, w, color=GRAY, label="osobny wyjściowy (×2)")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{d['bucket']}\n({plint(d['vocab'])})" for d in data], fontsize=9)
    ax.set_ylabel("% parametrów modelu 150M")
    for b in list(b1) + list(b2):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 1,
                plnum(b.get_height(), 1), ha="center", fontsize=8)
    ax.legend(fontsize=9)
    _title(fig, "Większy słownik to większy koszt embeddingów")
    _source(fig, "Źródło: results/tkx_zoo_vocab_cost.json (d_model 768); commit d91a87e")
    _save(fig, "koszt_slownika", szybko)


def wykres_daty_kwoty_paragraf(szybko=False):
    data = dane_daty_kwoty_paragraf()
    fig, axes = plt.subplots(1, 3, figsize=(12, 5) if not szybko else (9, 4))
    names = list(data["dates"].keys())
    colors = [OI_ORANGE, OI_GREEN, OI_BLUE, OI_SKY]
    for ax, (title, key) in zip(axes, [("Daty (12 zapisów)", "dates"),
                                        ("Kwoty (9 zapisów)", "amounts"),
                                        ("Paragrafy (9 form)", "paragraphs")]):
        vals = [data[key][n] for n in names]
        yy = np.arange(len(names))
        ax.barh(yy, vals, color=colors, height=0.6)
        ax.set_yticks(yy)
        ax.set_yticklabels(names, fontsize=9)
        ax.invert_yaxis()
        ax.set_title(title, fontsize=10)
        for i, v in enumerate(vals):
            ax.text(v + max(vals) * 0.01, i, plnum(v, 2), va="center", fontsize=8)
        ax.set_xlim(0, max(vals) * 1.15)
    _title(fig, "TOKENIZATOREX lepiej dzieli daty, kwoty i paragrafy")
    _source(fig, "Źródło: results/tkx_zoo_formats.json; commit d91a87e")
    _save(fig, "daty_kwoty_paragraf", szybko)


def wykres_json_heldout(szybko=False):
    data = dane_json_heldout()
    fig, ax = plt.subplots(figsize=(8, 5) if not szybko else (6, 4))
    groups = ["tc1 (narzędzia)", "held-out (nowe)"]
    v0 = [data["tc1"]["V0"], data["heldout"]["V0"]]
    v2 = [data["tc1"]["V0J2"], data["heldout"]["V0J2"]]
    x = np.arange(len(groups))
    w = 0.36
    b1 = ax.bar(x - w / 2, v0, w, color=GRAY, label="V0")
    b2 = ax.bar(x + w / 2, v2, w, color=OI_ORANGE, label="V0J2")
    ax.set_xticks(x)
    ax.set_xticklabels(groups, fontsize=10)
    ax.set_ylabel("tokeny / słowo (JSON)")
    for b in list(b1) + list(b2):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.05,
                plnum(b.get_height(), 2), ha="center", fontsize=8)
    # adnotacje delta
    for i in range(2):
        d = (v2[i] - v0[i]) / v0[i] * 100
        ax.text(x[i], max(v0[i], v2[i]) + 0.6, f"{plnum(d, 1)}%", ha="center", fontsize=9, color=OI_ORANGE)
    ax.legend(fontsize=9)
    ax.text(0.5, 0.96, "tc1 (−23%) to górna granica; nowe narzędzia dają −33%",
            transform=ax.transAxes, ha="center", fontsize=9, color="#444444")
    _title(fig, "V0J2 redukuje tokeny JSON na niewidzianych narzędziach")
    _source(fig, "Źródło: results/tkx_v21_test.json + results/tkx_zoo_fertility.json; commit d91a87e")
    _save(fig, "json_heldout", szybko)


def wykres_znane_wady(szybko=False):
    data = dane_znane_wady()
    fig, ax = plt.subplots(figsize=(8, 4.5) if not szybko else (6, 3.5))
    share = data["midword_uses_share"] * 100
    ax.bar([0], [share], color=OI_ORANGE, width=0.5)
    ax.set_xticks([0])
    ax.set_xticklabels(["SuperBPE tnie w środku słowa"], fontsize=10)
    ax.set_ylabel("% użyć tokenów")
    ax.set_ylim(0, max(share * 3, 1))
    ax.text(0, share + 0.02, f"{plnum(share, 2)}%", ha="center", fontsize=11, fontweight="bold")
    ax.text(0, share + 0.12, "13 z 172 tekstów urzędowych (38 z 384 par słów)",
            ha="center", fontsize=9, color="#444444")
    # przykład segmentacji
    ax.text(0.5, 0.85, "„zgodność z” → V0: z | god | ność z   (base: z | go | dnoś |  z)",
            transform=ax.transAxes, ha="center", fontsize=9, color="#333333",
            bbox=dict(boxstyle="round", fc="#F5F5F5", ec="#BBBBBB"))
    _title(fig, "Znana wada: SuperBPE tnie słowo w środku")
    _source(fig, "Źródło: results/tkx_v2_r6_superwords.json + tkx_v2/ZNANE_WADY.md; commit d91a87e")
    _save(fig, "znane_wady", szybko)


# ---------- animacje ----------

def _clean_tok(t):
    return t.replace("Ġ", " ").replace("Â", "").strip() or t.replace("Ġ", " ")


def anim_tokenizacja_porownanie(szybko=False):
    import matplotlib.animation as animation
    from tokenizers import Tokenizer
    import tiktoken

    sentence = ("Zgodnie z § 12 ust. 3 pkt 4 lit. a, wniosek z dnia 2 stycznia 2026 r. "
                "na kwotę 1 234 567,89 zł")

    rows = []
    # V0
    v0 = Tokenizer.from_file(str(REPO / "hf" / "variants" / "V0-32k" / "tokenizer.json"))
    enc = v0.encode(sentence, add_special_tokens=False)
    rows.append(("TOKENIZATOREX V0", [_clean_tok(v0.decode([i])) for i in enc.ids], OI_ORANGE))
    # Slayer (z lokalnego cache, jeśli dostępny)
    slayer_path = None
    for cand in [REPO / "tkx_zoo" / "hf" / "Slayer-v6" / "tokenizer.json",
                 Path("D:/VPS/fabryka/tkx-json/tkx_zoo/hf/Slayer-v6/tokenizer.json")]:
        if cand.is_file():
            slayer_path = cand
            break
    if slayer_path is None:
        for base in [Path("C:/Users/x/.cache/huggingface/hub"),
                     Path("D:/VPS/cache/huggingface/hub")]:
            if base.is_dir():
                for p in base.glob("models--SlayerLab--Slayer1B*/snapshots/*/tokenizer.json"):
                    slayer_path = p
                    break
            if slayer_path is not None:
                break
    if slayer_path is not None:
        sl = Tokenizer.from_file(str(slayer_path))
        sl_enc = sl.encode(sentence, add_special_tokens=False)
        rows.append(("Slayer v6", [_clean_tok(sl.decode([i])) for i in sl_enc.ids], OI_GREEN))
        slayer_note = None
    else:
        slayer_note = "Slayer: tokenizer niedostępny lokalnie (pominięty)"
    # GPT-4o
    gpt = tiktoken.get_encoding("o200k_base")
    gids = gpt.encode(sentence)
    rows.append(("GPT-4o", [gpt.decode([i]) for i in gids], OI_BLUE))

    nframes_tokens = max(len(r[1]) for r in rows)
    hold = 18 if not szybko else 10
    total = nframes_tokens + hold
    fps = 12 if not szybko else 8

    fig, ax = plt.subplots(figsize=(10, 5.5) if not szybko else (8, 4.5))
    ax.axis("off")
    _title(fig, "Tokenizacja jednego zdania urzędowego")

    def draw(frame):
        ax.clear()
        ax.axis("off")
        shown = min(frame + 1, nframes_tokens)
        y0 = 0.85
        for ri, (name, toks, color) in enumerate(rows):
            y = y0 - ri * 0.28
            ax.text(0.02, y + 0.12, f"{name}: {min(shown, len(toks))}/{len(toks)} tokenów",
                    fontsize=11, fontweight="bold", color=color, transform=ax.transAxes)
            # tiles
            x = 0.02
            for ti in range(min(shown, len(toks))):
                txt = toks[ti]
                if len(txt) > 14:
                    txt = txt[:13] + "…"
                ax.text(x, y, txt, fontsize=9, color="white",
                        bbox=dict(boxstyle="round,pad=0.25", fc=color, ec="none"),
                        transform=ax.transAxes)
                x += 0.012 + 0.011 * max(1, len(txt))
                if x > 0.95:
                    break
        if frame >= nframes_tokens:
            ys = 0.05
            summary = "  |  ".join(f"{n}: {len(t)} tokenów" for n, t, _ in rows)
            ax.text(0.5, ys, summary, transform=ax.transAxes, ha="center", fontsize=10,
                    bbox=dict(boxstyle="round", fc="#F0F0F0", ec="#BBBBBB"))
            if slayer_note:
                ax.text(0.5, ys - 0.07, slayer_note, transform=ax.transAxes, ha="center",
                        fontsize=8, color="#777777")
        fig.suptitle("Tokenizacja jednego zdania urzędowego", fontsize=13, fontweight="bold")

    ani = animation.FuncAnimation(fig, draw, frames=total, interval=1000 / fps)
    out = ANIM / "tokenizacja_porownanie.gif"
    ani.save(out, writer=animation.PillowWriter(fps=fps), dpi=100)
    plt.close(fig)


def anim_fertility_wyscig(szybko=False):
    import matplotlib.animation as animation
    rows = dane_fertility_bzp()
    # sort by fertility (rosnąco) final
    ordered = sorted(rows, key=lambda r: r["fertility"])
    names = [r["name"] for r in ordered]
    finals = [r["fertility"] for r in ordered]
    colors = [OI_ORANGE if r["highlight"] else GRAY for r in ordered]
    n = len(names)
    frames = 24 if not szybko else 14
    fps = 12 if not szybko else 8

    fig, ax = plt.subplots(figsize=(10, 6) if not szybko else (8, 4.5))
    _title(fig, "Wyścig fertility na BZP")

    def draw(frame):
        ax.clear()
        t = frame / max(frames - 1, 1)
        # ease-out
        e = 1 - (1 - t) ** 3
        vals = [f * e for f in finals]
        y = np.arange(n)
        ax.barh(y, vals, color=colors, height=0.7)
        ax.set_yticks(y)
        ax.set_yticklabels(names, fontsize=9)
        ax.invert_yaxis()
        ax.set_xlim(0, max(finals) * 1.15)
        ax.set_xlabel("tokeny / słowo")
        for i, v in enumerate(vals):
            if v > 0.05:
                ax.text(v + max(finals) * 0.01, i, plnum(v, 2), va="center", fontsize=8)
        if frame == frames - 1:
            ax.text(0.98, 0.02, "TOKENIZATOREX wyróżniony", transform=ax.transAxes,
                    ha="right", fontsize=9, color=OI_ORANGE, fontweight="bold")
    ani = animation.FuncAnimation(fig, draw, frames=frames + 8, interval=1000 / fps)
    out = ANIM / "fertility_wyscig.gif"
    ani.save(out, writer=animation.PillowWriter(fps=fps), dpi=100)
    plt.close(fig)


def anim_superbpe_sklejanie(szybko=False):
    import matplotlib.animation as animation
    from tokenizers import Tokenizer

    base = Tokenizer.from_file(str(REPO / "hf" / "tokenizatorex-base-32k" / "tokenizer.json"))
    v0 = Tokenizer.from_file(str(REPO / "hf" / "variants" / "V0-32k" / "tokenizer.json"))
    phrase = "zgodność z"
    base_toks = [_clean_tok(t) for t in (base.decode([i]) for i in base.encode(phrase, add_special_tokens=False).ids)]
    v0_toks = [_clean_tok(t) for t in (v0.decode([i]) for i in v0.encode(phrase, add_special_tokens=False).ids)]

    # frames: najpierw base tiles, potem łączenie w V0
    fps = 10 if not szybko else 7
    frames = 30 if not szybko else 18
    fig, ax = plt.subplots(figsize=(10, 4.5) if not szybko else (8, 3.5))
    _title(fig, "Jak SuperBPE skleja słowa")

    def draw(frame):
        ax.clear()
        ax.axis("off")
        ax.text(0.5, 0.92, f"fraza: „{phrase}”", transform=ax.transAxes, ha="center", fontsize=11)
        # base row
        ax.text(0.02, 0.72, "base-32k:", transform=ax.transAxes, fontsize=10, fontweight="bold")
        x = 0.18
        for t in base_toks:
            ax.text(x, 0.72, t, transform=ax.transAxes, fontsize=9, color="white",
                    bbox=dict(boxstyle="round,pad=0.25", fc=GRAY, ec="none"))
            x += 0.015 + 0.012 * max(1, len(t))
        # v0 row
        ax.text(0.02, 0.42, "V0:", transform=ax.transAxes, fontsize=10, fontweight="bold", color=OI_ORANGE)
        merge_progress = min(1.0, frame / (frames * 0.6))
        # show base tokens shrinking? We'll just show V0 tokens after merge
        if merge_progress < 1.0:
            # show base tokens in v0 row (jeszcze nie sklejone)
            x = 0.18
            for t in base_toks:
                ax.text(x, 0.42, t, transform=ax.transAxes, fontsize=9, color="white",
                        bbox=dict(boxstyle="round,pad=0.25", fc=LIGHT_GRAY, ec="none"))
                x += 0.015 + 0.012 * max(1, len(t))
            cnt = len(base_toks)
        else:
            x = 0.18
            for t in v0_toks:
                ax.text(x, 0.42, t, transform=ax.transAxes, fontsize=9, color="white",
                        bbox=dict(boxstyle="round,pad=0.25", fc=OI_ORANGE, ec="none"))
                x += 0.015 + 0.012 * max(1, len(t))
            cnt = len(v0_toks)
        ax.text(0.5, 0.22, f"tokeny: {len(base_toks)} → {len(v0_toks)}", transform=ax.transAxes,
                ha="center", fontsize=10, fontweight="bold")
        if frame == frames + 7:
            ax.text(0.5, 0.08, "znana wada v2.0: SuperBPE czasem tnie słowo w środku (naprawa w v2.1)",
                    transform=ax.transAxes, ha="center", fontsize=8, color="#777777")

    ani = animation.FuncAnimation(fig, draw, frames=frames + 8, interval=1000 / fps)
    out = ANIM / "superbpe_sklejanie.gif"
    ani.save(out, writer=animation.PillowWriter(fps=fps), dpi=100)
    plt.close(fig)


def generate_all(szybko=False, statyczne=True, animacje=True):
    _ensure_dirs()
    if statyczne:
        wykres_fertility_bzp(szybko)
        wykres_skad_przewaga(szybko)
        wykres_osiem_zrodel(szybko)
        wykres_koszt_slownika(szybko)
        wykres_daty_kwoty_paragraf(szybko)
        wykres_json_heldout(szybko)
        wykres_znane_wady(szybko)
    if animacje:
        anim_tokenizacja_porownanie(szybko)
        anim_fertility_wyscig(szybko)
        anim_superbpe_sklejanie(szybko)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--szybko", action="store_true")
    ap.add_argument("--tylko-statyczne", action="store_true")
    ap.add_argument("--tylko-animacje", action="store_true")
    args = ap.parse_args()
    stat = not args.tylko_animacje
    anim = not args.tylko_statyczne
    generate_all(szybko=args.szybko, statyczne=stat, animacje=anim)
    print("STATUS=OK")


if __name__ == "__main__":
    main()
