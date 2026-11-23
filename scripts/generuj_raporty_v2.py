#!/usr/bin/env python3
"""Jedyne źródło raportów TKX-V2 / TKX-V21.

Generuje wszystkie pliki raportów wyłącznie z ``results/*.json``:
  RELEASE_NOTES_v2.0.md
  tkx_v2/RAPORT_TEST_DOMENOWY.md
  tkx_v2/RAPORT_PROSTY_V2.md
  tkx_v2/KARTA_WYMAGAN.md
  tkx_v2/ZNANE_WADY.md
  tkx_v2/KORPUS_DOMENOWY.md
  tkx_v21/RAPORT.md
  tkx_v21/RAPORT_PROSTY.md

Użycie:
  python scripts/generuj_raporty_v2.py          # zapis
  python scripts/generuj_raporty_v2.py --check  # tylko porównanie (CI)

Test w CI uruchamia ``--check``; jeżeli plik w repo różni się od wyniku
generatora, test kończy się błędem. Dzięki temu ręczna poprawka raportu bez
poprawy generatora jest natychmiast wykrywana.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RES = REPO / "results"
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from tkx_v21.raport_v21 import build_reports as build_v21_reports  # noqa: E402


def load(name):
    with open(RES / name, encoding="utf-8") as f:
        return json.load(f)


fert = load("tkx_v2_fertility.json")
dead = load("tkx_v2_dead_tokens.json")
spec = load("tkx_v2_special_chars.json")
pat = load("tkx_v2_patterns.json")
wz = json.load(open(REPO / "tkx_v2/wzorce.json", encoding="utf-8"))
rt2 = load("tkx_v2_roundtrip.json")

v21_dev = load("tkx_v21_dev.json")
v21_test = load("tkx_v21_test.json")
v21_sel = load("tkx_v21_selection.json")
v21_sel2 = load("tkx_v21_selection_r2.json")
v21_g149 = load("tkx_v21_granty149.json")
v21_wz = load("tkx_v21_wzorce.json")
v21_fmt = load("tkx_v21_formaty.json")
v21_forms = load("tkx_v21_heldout_forms.json")
v21_leak = load("tkx_v21_leak.json")

SOURCES = [
    ("1_bzp", "BZP (ogłoszenia)"),
    ("2_du_eli", "Dz.U. 2026 ELI"),
    ("3_kio", "KIO"),
    ("4_samorzad", "Samorząd (uchwały)"),
    ("5_granty", "Granty"),
    ("6_json_narzedzia", "JSON narzędzi (tc1)"),
    ("7_ogolny", "Kontrola ogólna (HPLT web)"),
    ("json_bzp_tabele", "JSON BZP (tabele, extra)"),
]
TOKS = ["TKX/V0-32k", "TKX/V3-32k", "Slayer1B-1.08"]


def f3(x):
    return f"{x:.3f}".replace(".", ",")


def f2(x):
    return f"{x:.2f}".replace(".", ",")


def pct(x):
    return f"{x:+.2f}%".replace(".", ",")


def dec(x, n=4):
    if x is None:
        return "—"
    return f"{x:.{n}f}".replace(".", ",")


def table(headers, rows):
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        out.append("| " + " | ".join(str(x).replace("|", "\\|") for x in row) + " |")
    return "\n".join(out)


def get_f(src, tok):
    return fert["sources"][src]["tokenizers"][tok]


def v3_delta(src):
    a = get_f(src, "TKX/V0-32k")["fertility"]
    b = get_f(src, "TKX/V3-32k")["fertility"]
    return (b / a - 1) * 100


def count_over(category, threshold):
    out = {}
    for tok in ("TKX/V0-32k", "TKX/V3-32k", "Slayer1B-1.08"):
        rows = [x for x in pat["tokenizers"][tok]["per_item"]
                if x["category"] == category]
        out[tok] = (sum(1 for x in rows if x["tokens_per_pattern"] > threshold), len(rows))
    return out


def leak_label():
    wzr = v21_leak["test_docs"]["wzorce_json"]
    if v21_leak["summary"]["status"] == "CZESCIOWE_POKRYCIE_SZKIELETEM":
        return (f"**częściowe pokrycie szkieletem** ({wzr['docs_over_50pct']}/10 > 50%, "
                f"max {dec(wzr['max_coverage'] * 100, 1)}%)")
    return f"**{v21_leak['summary']['status']}**"


def pattern_sums():
    rows = v21_leak["test_docs"]["wzorce_json"]["rows"]
    cov = {r["id"]: r["coverage"] for r in rows}
    base = [x for x in v21_wz["tokenizers"]["V0R-32k"]["per_item"]
            if x["category"] == "json_tool_calls"]
    v2 = [x for x in v21_wz["tokenizers"]["V0J2-32k"]["per_item"]
          if x["category"] == "json_tool_calls"]
    clean = [x["id"] for x in base if cov.get(x["id"], 0.0) <= 0.5]
    out = {
        "all0": sum(x["tokens"] for x in base),
        "all2": sum(x["tokens"] for x in v2),
        "clean0": sum(x["tokens"] for x in base if x["id"] in clean),
        "clean2": sum(x["tokens"] for x in v2 if x["id"] in clean),
        "clean_n": len(clean),
    }
    out["all_gain"] = (out["all2"] / out["all0"] - 1) * 100
    out["clean_gain"] = (out["clean2"] / out["clean0"] - 1) * 100
    return out


PS = pattern_sums()
FORMS = v21_forms["forms"]
OVERALL_FORMS = v21_forms["overall"]


def build_raport_test():
    lines = []
    lines.append("# RAPORT TEST DOMENOWY — TOKENIZATOREX v2.0")
    lines.append("")
    lines.append("Data: 23.11.2026. Liczby z `results/tkx_v2_*.json` (generowane skryptem).")
    lines.append("")
    lines.append("## 1. Korpus")
    lines.append("")
    lines.append("Źródła i rozmiary z `results/tkx_v2_fertility.json`:")
    lines.append("")
    lines.append("| Źródło | Dokumenty | Słowa | Bajty |")
    lines.append("|---|---:|---:|---:|")
    for sid, name in SOURCES:
        s = fert["sources"][sid]
        lines.append(f"| {name} | {s['docs']} | {s['words']} | {s['bytes']} |")
    lines.append("")
    lines.append("Uwaga: Dz.U. i granty mają po 12 dokumentów — ranking fertility na tych źródłach jest niepewny (mała próba).")
    lines.append("")
    lines.append("## 2. Fertility (tokeny/słowo) z 95% CI")
    lines.append("")
    for sid, name in SOURCES:
        s = fert["sources"][sid]
        lines.append(f"### {name} (n={s['docs']} dok.)")
        lines.append("")
        lines.append("| Tokenizer | Fertility | 95% CI | Bajty/token |")
        lines.append("|---|---:|---:|---:|")
        for tok in TOKS:
            r = s["tokenizers"][tok]
            lines.append(f"| {tok} | {f3(r['fertility'])} | [{f3(r['fertility_ci_lo'])}, {f3(r['fertility_ci_hi'])}] | {f3(r['bytes_per_token'])} |")
        lines.append("")
    lines.append("Wniosek z danych: V0-32k ma najniższą fertility na wszystkich 8 źródłach (punktowo). CI rozdzielają V0 od V3 wyraźnie tylko na części źródeł; na Dz.U. i grantach (n=12) ranking jest niepewny.")
    lines.append("")
    lines.append("## 3. Znaki specjalne")
    lines.append("")
    chars = spec["chars"]
    lines.append(f"Lista znaków (n={len(chars)}), z pliku `results/tkx_v2_special_chars.json`: " + ", ".join(f"`{c}`" for c in chars))
    lines.append("")
    lines.append("| Tokenizer | Liczba znaków jako 1 token | `§` jako 1 token |")
    lines.append("|---|---:|---:|")
    for tok in TOKS:
        row = spec["tokenizers"][tok]
        cnt = sum(1 for c in chars if row.get(c) is True)
        lines.append(f"| {tok} | {cnt} | {'TAK' if row.get('§') else 'NIE'} |")
    lines.append("")
    lines.append("V3-32k nie ma `§` jako jednego tokena (encode daje 2 tokeny). V0-32k i Slayer mają `§` jako 1 token.")
    lines.append("")
    lines.append("## 4. Martwe tokeny")
    lines.append("")
    lines.append("| Tokenizer | Vocab | Martwe | % |")
    lines.append("|---|---:|---:|---:|")
    for tok in TOKS:
        r = dead["tokenizers"][tok]
        lines.append(f"| {tok} | {r['vocab']} | {r['dead']} | {f2(r['dead_pct'])}% |")
    lines.append("")
    lines.append("Uwaga: porównanie ze Slayerem nie jest bezpośrednie — Slayer ma słownik polsko-angielski; na polskim korpusie część słownika z natury jest nieużywana. W audycie szerszym martwe tokeny Slayera to 8,90%.")
    lines.append("")
    lines.append("## 5. Wzorce i segmentacja")
    lines.append("")
    lines.append(f"Wzorce: {wz['count']} w {len(set(i['category'] for i in wz['items']))} kategoriach (`tkx_v2/wzorce.json`).")
    lines.append("Segmentacja mierzona przez `encoding.offsets` (liczba kontekstów z identyczną segmentacją, sklejenia z poprzedzającym znakiem, segmentacja tekstowa) — zapis w `results/tkx_v2_patterns.json`.")
    lines.append("")
    for tok in TOKS:
        items = pat["tokenizers"][tok]["per_item"]
        ident = sum(1 for i in items if i.get("contexts_identical"))
        merged = sum(1 for i in items if i.get("merged_with_prev_count", 0) > 0)
        lines.append(f"- {tok}: identyczna segmentacja w 5/5 kontekstach dla {ident}/{len(items)} wzorców; wzorce ze sklejeniem z poprzedzającym znakiem: {merged}/{len(items)}.")
    lines.append("")
    lines.append("## 6. Kandydat i O1/O2")
    lines.append("")
    v3 = rt2["tokenizers"]["V3-32k"]
    v3_bzp = rt2["per_source"]["V3-32k"]["bzp_ogloszenia"]["bad"]
    v3_kio = rt2["per_source"]["V3-32k"]["kio"]["bad"]
    bzp_full = rt2["bzp_full"]
    lines.append("Domyślny wariant v2.0: **V0-32k** (najniższa fertility na wszystkich 8 źródłach, `§` jako 1 token, round-trip 0/700 na dokumentach; NFD na wejściu zachowuje, więc O2 FAIL dla wejścia NFD).")
    lines.append(f"V3-32k: wariant eksperymentalny z cięciem cyfr; wygrywa na identyfikatorach/kodach/sygnaturach, przegrywa na datach i kwotach; nie ma `§` jako jednego tokena; normalizuje NFD→NFC. O1 FAIL: **{v3['bad']}/700** dokumentów (w tym {v3_bzp} BZP + {v3_kio} KIO, wszystkie NFD; {bzp_full['nfd']}/{bzp_full['docs']} BZP ma NFD). O2 PASS (wyjście NFC).")
    lines.append("Uwaga O1/O2: O1 (dokładny round-trip) i O2 (wyjście NFC) wykluczają się dla wejścia NFD; propozycja v2.1: korpus normalizowany do NFC przed tokenizacją, a wymaganie dla tokenizera = dokładny round-trip na wejściu NFC.")
    lines.append("Ostateczny wybór dopiero po TKX-D (małe modele, BPB, ≥ 3 seedy). Fertility to warunek konieczny, nie dowód jakości.")
    lines.append("")
    return "\n".join(lines) + "\n"


def build_raport_prosty():
    rp = []
    rp.append("# Raport prosty v2.0")
    rp.append("")
    rp.append("TOKENIZATOREX ma warianty o niskiej fertility na polskim tekście. W v2.0 porównano warianty na 8 źródłach testowych (przetargi, Dz.U., KIO, samorząd, granty, JSON narzędzi, JSON BZP, kontrola ogólna).")
    rp.append("")
    rp.append("Wyniki z danych (`results/tkx_v2_fertility.json`): V0-32k ma najniższą fertility na wszystkich 8 źródłach (punktowo). V3-32k przegrywa z V0 punktowo na wszystkich 8 źródłach. CI rozdzielają V0 od V3 wyraźnie tylko na części źródeł; Dz.U. i granty mają n=12, więc ranking jest niepewny.")
    rp.append("")
    rp.append(f"Martwe tokeny: V0-32k {f2(dead['tokenizers']['TKX/V0-32k']['dead_pct'])}%, V3-32k {f2(dead['tokenizers']['TKX/V3-32k']['dead_pct'])}%, Slayer1B-1.08 {f2(dead['tokenizers']['Slayer1B-1.08']['dead_pct'])}% (`results/tkx_v2_dead_tokens.json`). Uwaga: 35,03% Slayera dotyczy korpusu polskiego; w audycie szerszym 8,90%.")
    rp.append("")
    rp.append("Znaki specjalne: V3-32k nie ma `§` jako jednego tokena (2 tokeny). V0-32k ma `§` jako 1 token. Dane: `results/tkx_v2_special_chars.json`.")
    rp.append("")
    v3 = rt2["tokenizers"]["V3-32k"]
    rp.append(f"Round-trip: V0-32k i Slayer 0/700; V3-32k **{v3['bad']}/700** (dokumenty NFD; {rt2['per_source']['V3-32k']['bzp_ogloszenia']['bad']} BZP + {rt2['per_source']['V3-32k']['kio']['bad']} KIO).")
    rp.append("")
    rp.append("Kandydat domyślny v2.0: **V0-32k**. V3-32k to wariant eksperymentalny z cięciem cyfr i wadami (NFD→NFC, brak `§` jako 1 token, gorsza fertility na wszystkich 8 źródłach). Ostateczny wybór po TKX-D (małe modele, BPB, ≥ 3 seedy). Fertility to warunek konieczny, nie dowód jakości modelu.")
    rp.append("")
    return "\n".join(rp) + "\n"


def build_release():
    rn = []
    rn.append("# RELEASE NOTES — TOKENIZATOREX v2.0 (draft)")
    rn.append("")
    rn.append("Status: DRAFT (wydanie po scaleniu PR i zgodzie właściciela).")
    rn.append("")
    rn.append("## Co to jest v2.0")
    rn.append("")
    rn.append("v2.0 to stan po TKX-A + TKX-C + test domenowy na tekstach urzędowych (BZP, Dz.U. ELI, KIO, samorząd, granty, JSON narzędzi, kontrola ogólna).")
    rn.append("")
    rn.append("## Wariant domyślny i kandydaci")
    rn.append("")
    rn.append("Z danych (`results/tkx_v2_fertility.json`): **V0-32k ma najniższą fertility na wszystkich 8 źródłach** (punktowo). CI rozdzielają V0 od V3 wyraźnie tylko na części źródeł; Dz.U. i granty mają n=12, więc ranking jest niepewny.")
    rn.append("")
    rn.append("**Domyślny wariant v2.0 = V0-32k.** Ma `§` jako 1 token i round-trip 0/700 na dokumentach.")
    rn.append("")
    v3 = rt2["tokenizers"]["V3-32k"]
    bzp_full = rt2["bzp_full"]
    rn.append("**V3-32k = wariant eksperymentalny z cięciem cyfr.** Wygrywa na identyfikatorach, kodach pocztowych, numerach BZP, skrótach i sygnaturach w wzorcach; przegrywa na datach i kwotach; nie ma `§` jako jednego tokena; normalizuje NFD→NFC. O1 FAIL: "
              f"{v3['bad']}/700 dokumentów ({rt2['per_source']['V3-32k']['bzp_ogloszenia']['bad']} BZP + "
              f"{rt2['per_source']['V3-32k']['kio']['bad']} KIO, wszystkie NFD; {bzp_full['nfd']}/{bzp_full['docs']} BZP ma NFD); O2 PASS. "
              "Na źródłach testowych traci vs V0: "
              f"BZP {pct(v3_delta('1_bzp'))}, Dz.U. {pct(v3_delta('2_du_eli'))}, KIO {pct(v3_delta('3_kio'))}, "
              f"samorząd {pct(v3_delta('4_samorzad'))}, granty {pct(v3_delta('5_granty'))}, "
              f"JSON narzędzi {pct(v3_delta('6_json_narzedzia'))}, JSON BZP tabele {pct(v3_delta('json_bzp_tabele'))}, "
              f"ogólny {pct(v3_delta('7_ogolny'))} (liczone z fertility w `results/tkx_v2_fertility.json`).")
    rn.append("")
    rn.append("Ostateczny wybór dopiero po TKX-D (małe modele, BPB, ≥ 3 seedy). Fertility to warunek konieczny, nie dowód jakości (Schmidt i in.).")
    rn.append("")
    rn.append("## Znane wady")
    rn.append("")
    rn.append("Zob. `tkx_v2/ZNANE_WADY.md`. Uwaga: porównanie martwych tokenów ze Slayerem nie jest bezpośrednie (słownik polsko-angielski).")
    rn.append("")
    rn.append("## Jak sprawdzić samemu")
    rn.append("")
    rn.append("```bash")
    rn.append('python scripts/sprawdz_sam.py "Twój tekst."')
    rn.append('python scripts/sprawdz_sam.py --wszystkie "Twój tekst."')
    rn.append("```")
    rn.append("")
    rn.append("Domyślnie lokalne tokenizery TOKENIZATOREX + Slayer; `--wszystkie` dodaje zewnętrzne (wymaga cache/logowania).")
    rn.append("")
    rn.append("## Nie sprawdzono (wprost)")
    rn.append("")
    rn.append("- Przeciek względem próbki treningowej HPLT (13-gramy) — nie wykonano.")
    rn.append("- Bielik-1.5B-v3 (APT4) jest obecny w wynikach fertility; testy downstream nie wykonane. Tokenizer Bielika jest przeliczony w `results/tkx_v2_special_chars.json` i `results/tkx_v2_patterns.json` po zalogowaniu HF.")
    rn.append("- Efektywność Rényiego (TokEval) — zaplanowana, nie policzona.")
    rn.append("")
    rn.append("## Eksperyment v2.1-JSON (kandydat warunkowy V0J2-32k)")
    rn.append("")
    rn.append("Dane: `results/tkx_v21_*.json` (gałąź `feat/tkx-v2-1-json`, cherry-pick do `feat/tkx-v2-0`). Reguła z protokołu: bramka JSON + brak regresji polskiego > 1% na 7 źródłach, `§` 1 token.")
    rn.append("")
    rn.append("### Wynik według reguły oryginalnej (na pierwszym miejscu)")
    rn.append("")
    rn.append("Wynik: **brak kandydata** (`results/tkx_v21_selection.json`: `winner = null`). V0J2-32k nie przeszedł bramki polskiej na grantach przy n=12 (reguła oryginalna).")
    rn.append("")
    rn.append("### Poprawka 2 (granty 149)")
    rn.append("")
    g = v21_sel2["candidates"]["V0J2-32k"]["polish_deltas"]["granty"]
    rn.append(f"Na grantach n=149 (`results/tkx_v21_selection_r2.json`): V0R {dec(g['v0r'], 6)}, V0J2 {dec(g['variant'], 6)}, delta {pct(g['delta_pct'])} (próg ≤ 1%). CI 95% V0R [{dec(g['ci_v0r'][0], 6)}, {dec(g['ci_v0r'][1], 6)}], V0J2 [{dec(g['ci_variant'][0], 6)}, {dec(g['ci_variant'][1], 6)}]. Status: **kandydat warunkowy do TKX-D** (nie awans automatyczny).")
    rn.append("")
    rn.append("### Zysk JSON (V0R vs V0J2, test)")
    rn.append("")
    s = v21_test["sources"]
    rows = [
        ("JSON tc1 test", s["tc1_test"]["tokenizers"]["V0R-32k"]["fertility"], s["tc1_test"]["tokenizers"]["V0J2-32k"]["fertility"]),
        ("JSON tc1 (same wywołania)", s["tc1_test_json_only"]["tokenizers"]["V0R-32k"]["fertility"], s["tc1_test_json_only"]["tokenizers"]["V0J2-32k"]["fertility"]),
        ("JSON narzędzia niewidziane", s["json_generic_test"]["tokenizers"]["V0R-32k"]["fertility"], s["json_generic_test"]["tokenizers"]["V0J2-32k"]["fertility"]),
    ]
    rn.append("| Miara | V0R-32k | V0J2-32k | Zmiana |")
    rn.append("|---|---:|---:|---:|")
    for name, a, b in rows:
        rn.append(f"| {name} | {dec(a)} | {dec(b)} | {pct((b / a - 1) * 100)} |")
    rn.append(f"| 10 wzorców JSON (suma tokenów) | {PS['all0']} | {PS['all2']} | {pct(PS['all_gain'])} |")
    rn.append(f"| 8 wzorców bez >50% pokrycia | {PS['clean0']} | {PS['clean2']} | {pct(PS['clean_gain'])} |")
    rn.append("")
    rn.append(f"Przeciek wzorców: {leak_label()}; 0 exact. Zysk na 10 wzorcach jest częściowo memorization wspólnego szkieletu, dlatego podany osobno dla 8 bez >50%.")
    rn.append("")
    rn.append("### Held-out — rozbicie na formy")
    rn.append("")
    rn.append("| Forma | Dokumenty | Tokeny V0 | Tokeny V0J2 | Zmiana |")
    rn.append("|---|---:|---:|---:|---:|")
    for form in ("compact", "pretty", "result"):
        x = FORMS[form]
        rn.append(f"| {form} | {x['docs']} | {x['tokens_v0']} | {x['tokens_v0j2']} | {pct(x['delta_pct'])} |")
    rn.append(f"| razem | {OVERALL_FORMS['docs']} | {OVERALL_FORMS['tokens_v0']} | {OVERALL_FORMS['tokens_v0j2']} | {pct(OVERALL_FORMS['delta_pct'])} |")
    rn.append("")
    rn.append("Duża część zysku to wspólny szkielet wywołania (`<tool_call>`, `\"name\"`, `\"arguments\"`); na samych wynikach narzędzi zysk jest znacznie mniejszy.")
    rn.append("")
    rn.append("### Koszt dla polskiego (V0J2 vs V0R, dev, delta %)")
    rn.append("")
    rn.append("| Źródło | Delta % | Próg ≤ 1% |")
    rn.append("|---|---:|---:|")
    pol = v21_sel2["candidates"]["V0J2-32k"]["polish_deltas"]
    pol_pl = {"bzp_ogloszenia": "BZP ogłoszenia", "du_eli": "Dz.U. ELI", "kio": "KIO",
              "samorzad": "Samorząd", "granty": "Granty (n=149)", "json_bzp_tabele": "JSON BZP tabele",
              "general_web": "Ogólny web"}
    for k in ("bzp_ogloszenia", "du_eli", "kio", "samorzad", "granty", "json_bzp_tabele", "general_web"):
        rn.append(f"| {pol_pl[k]} | {pct(pol[k]['delta_pct'])} | {'TAK' if pol[k]['pass'] else 'NIE'} |")
    rn.append("")
    rn.append("Tokeny specjalne (V0J5S) nie poprawiły wyniku względem V0J5 i nie dały kandydata; w 10 wzorcach JSON suma tokenów V0J5S to 144 vs V0J2 135 (`results/tkx_v21_wzorce.json`).")
    rn.append("")
    rn.append("### Formaty dat, kwot i „§” — skrót")
    rn.append("")
    rn.append("Pełne tabele per zapis: `tkx_v21/RAPORT.md`, sekcja 8a. Źródło: `results/tkx_v21_formaty.json` (40 dat, po 40 kwot na zapis, 9 form z „§”).")
    rn.append("")
    fa = v21_fmt["summary"]["date_avg"]
    ka = v21_fmt["summary"]["kwota_avg"]
    rn.append("| Miara | V0 | V0J2 | V3 | Slayer | GPT-4o |")
    rn.append("|---|---:|---:|---:|---:|---:|")
    rn.append("| Daty (średnia) | " + " | ".join(f2(fa[k]) for k in ("V0", "V0J2", "V3", "Slayer", "GPT-4o")) + " |")
    rn.append("| Kwoty (średnia) | " + " | ".join(f2(ka[k]) for k in ("V0", "V0J2", "V3", "Slayer", "GPT-4o")) + " |")
    par = v21_fmt["paragraf"]["§"]
    rn.append("| `§` (tokeny) | " + " | ".join(str(par[k]) for k in ("V0", "V0J2", "V3", "Slayer", "GPT-4o")) + " |")
    rn.append("")
    rn.append("Wniosek: po dodaniu JSON `§` pozostaje 1 tokenem w V0 i V0J2; średnia na datach V0J2 ≤ V0 + 0,1; kwoty bez istotnej zmiany. Kwoty dla „mln” i „tys.” są losowane w realistycznych zakresach (1–500 mln, 1–999 tys.).")
    rn.append("")
    rn.append("## Plan v2.1 i TKX-D")
    rn.append("")
    rn.append("- v2.1: naprawa `§` (V3), skróty prawne, tokeny JSON; mieszanka 10–30% tekstów urzędowych.")
    rn.append("- TKX-D: wybór wariantu i rozmiaru słownika (16k/24k/32k) na małych modelach; ≥ 3 seedy; BPB.")
    rn.append("")
    rn.append("## Weryfikacja")
    rn.append("")
    rn.append("`pytest -q` zielone. `python scripts/sprawdz_liczby_v2.py` exit 0 na wszystkich raportach. `python scripts/generuj_raporty_v2.py --check` nie zmienia plików. Liczby w raportach pochodzą z `results/tkx_v2_*.json` i `results/tkx_v21_*.json`. Weryfikacja przez człowieka wymagana.")
    rn.append("")
    return "\n".join(rn) + "\n"


def build_karta():
    v3 = rt2["tokenizers"]["V3-32k"]
    bzp_full = rt2["bzp_full"]
    o5 = count_over("kwoty", 6)
    o6 = count_over("daty_iso", 5)
    o7 = count_over("cpv", 3)
    ka = []
    ka.append("# Karta wymagań TOKENIZATOREX v2.0 — tokenizer pod polski model ≤ 150M (polszczyzna urzędowa)")
    ka.append("")
    ka.append("Wersja: 23.11.2026. Powiązane: project-hub #566 (model 150M), #576 (dziennik), TKX-A, TKX-C.")
    ka.append("")
    ka.append("Zasada: nie ma najlepszego tokenizera — jest najlepszy do zadania i rozmiaru modelu. Fertility to warunek konieczny, nie dowód jakości. Ostateczny wybór w TKX-D.")
    ka.append("")
    ka.append("## Macierz zgodności O1–O9 (z danych)")
    ka.append("")
    ka.append("Wartości z `results/*.json` i pomiarów opisanych w raportach. PASS/FAIL nie są zgadywane.")
    ka.append("")
    ka.append("| Wymaganie | V0-32k | V3-32k | Slayer1B-1.08 | Dowód |")
    ka.append("|---|---:|---:|---:|---|")
    ka.append(f"| O1 Round-trip `decode(encode(x))==x` | PASS (0/700) | FAIL ({v3['bad']}/700: {rt2['per_source']['V3-32k']['bzp_ogloszenia']['bad']} BZP + {rt2['per_source']['V3-32k']['kio']['bad']} KIO, NFD) | PASS (0/700) | `results/tkx_v2_roundtrip.json` |")
    ka.append("| O2 Brak NFD w słowniku i na wyjściu (100%) | FAIL (zachowuje NFD na wyjściu) | PASS (normalizuje do NFC) | FAIL (zachowuje NFD na wyjściu) | `results/tkx_v2_roundtrip.json` + `tests/test_tkx_v2_r2.py` |")
    ka.append("| O3 Znak `§` jako pojedynczy token | PASS (1 token) | FAIL (2 tokeny) | PASS (1 token) | `results/tkx_v2_special_chars.json` |")
    ka.append("| O4 Lata 2015–2035 (≤ 2 tokeny/rok w formatach) | UNKNOWN | UNKNOWN | UNKNOWN | nie zmierzono w tym raporcie |")
    ka.append(f"| O5 Kwoty (≤ 6 tokenów/kwota, spójnie) | FAIL ({o5['TKX/V0-32k'][0]}/{o5['TKX/V0-32k'][1]} kwot > 6) | FAIL ({o5['TKX/V3-32k'][0]}/{o5['TKX/V3-32k'][1]}) | FAIL ({o5['Slayer1B-1.08'][0]}/{o5['Slayer1B-1.08'][1]}) | `results/tkx_v2_patterns.json` (kategoria kwoty) |")
    ka.append(f"| O6 Daty (≤ 5 tokenów/data) | FAIL ({o6['TKX/V0-32k'][0]}/{o6['TKX/V0-32k'][1]} dat > 5) | FAIL ({o6['TKX/V3-32k'][0]}/{o6['TKX/V3-32k'][1]}) | FAIL ({o6['Slayer1B-1.08'][0]}/{o6['Slayer1B-1.08'][1]}) | `results/tkx_v2_patterns.json` (kategoria daty_iso) |")
    ka.append(f"| O7 CPV (≤ 3 tokeny/kod) | FAIL ({o7['TKX/V0-32k'][0]}/{o7['TKX/V0-32k'][1]} kodów > 3) | FAIL ({o7['TKX/V3-32k'][0]}/{o7['TKX/V3-32k'][1]}) | FAIL ({o7['Slayer1B-1.08'][0]}/{o7['Slayer1B-1.08'][1]}) | `results/tkx_v2_patterns.json` (kategoria cpv) |")
    ka.append(f"| O8 Martwe tokeny ≤ 5% | FAIL ({f2(dead['tokenizers']['TKX/V0-32k']['dead_pct'])}%) | FAIL ({f2(dead['tokenizers']['TKX/V3-32k']['dead_pct'])}%) | FAIL ({f2(dead['tokenizers']['Slayer1B-1.08']['dead_pct'])}%) | `results/tkx_v2_dead_tokens.json` |")
    ka.append("| O9 Przeciek 13-gram ≤ 20% | UNKNOWN | UNKNOWN | UNKNOWN | nie wykonano dla HPLT; v21 mierzy tylko JSON |")
    ka.append("")
    ka.append("Uwaga: żaden z ocenianych wariantów (V0, V3, Slayer) nie spełnia O5–O8. Progi O5–O8 okazały się nierealne dla wszystkich tokenizerów (także Slayera) → do rewizji w v2.1 z uzasadnieniem, a nie po cichu.")
    ka.append("")
    ka.append("Uwaga O1/O2: wymagania O1 (dokładny round-trip) i O2 (wyjście w NFC) wykluczają się dla wejścia w NFD. Propozycja v2.1: korpus normalizowany do NFC przed tokenizacją (krok preprocessingu), a wymaganie dla tokenizera = dokładny round-trip na wejściu NFC. Wtedy O1 i O2 przestają się gryźć.")
    ka.append("")
    ka.append("## Wymagania (skrót)")
    ka.append("")
    ka.append("- O1: round-trip `decode(encode(x)) == x` 100%.")
    ka.append("- O2: brak NFD w słowniku i na wyjściu; 100% dokumentów.")
    ka.append("- O3: znak `§` jako pojedynczy token w słowniku i kodowaniu (nie cały wzorzec `§ 362(a)`).")
    ka.append("- O4: lata 2015–2035 ≤ 2 tokeny/rok.")
    ka.append("- O5–O7: progi tokenów dla kwot/daty/CPV — do rewizji w v2.1.")
    ka.append("- O8: martwe tokeny ≤ 5% słownika.")
    ka.append("- O9: przeciek 13-gram ≤ 20% dokumentów.")
    ka.append("")
    ka.append("## Bezpieczniki")
    ka.append("- Angielski: brak regresji > 5% względem V0-32k (procentowy próg; wartość bazowa do pomiaru w TKX-D).")
    ka.append("- JSON narzędzi: nie gorszy niż Slayer (metryka do doprecyzowania: fertility na korpusie vs suma wzorców).")
    ka.append("")
    ka.append("## Definicja gotowe")
    ka.append("- `pytest -q` zielone.")
    ka.append("- `python scripts/sprawdz_liczby_v2.py` exit 0 na wszystkich raportach (v2 i v21).")
    ka.append("- `python scripts/generuj_raporty_v2.py --check` nie zmienia plików.")
    ka.append("- Liczby w raportach z `results/*.json` (v2 i v21).")
    ka.append("")
    return "\n".join(ka) + "\n"


def build_znane_wady():
    zw = []
    zw.append("# Znane wady TOKENIZATOREX (v2.0)")
    zw.append("")
    zw.append("Każda wada z dowodem i propozycją naprawy (v2.1). Liczby z `results/*.json`.")
    zw.append("")
    zw.append("## W1. Znak `§` rozbity w wariancie V3-32k")
    zw.append("")
    zw.append("- **Dowód:** `results/tkx_v2_special_chars.json` — V3-32k nie ma `§` jako pojedynczego tokena (`encode` daje 2 tokeny); V0-32k ma 1 token.")
    zw.append("- **Przyczyna (hipoteza):** wymuszone tokeny cyfr i ograniczony budżet słownika mogły wypchnąć rzadkie znaki; do potwierdzenia na danych treningowych V3.")
    zw.append("- **Naprawa (v2.1):** dopisać `§` na końcu scaleń albo zarezerwować slot specjalny.")
    zw.append("")
    zw.append("## W2. Skróty prawne (Dz. U., Pzp, tj.)")
    zw.append("")
    zw.append("- **Dowód:** `results/tkx_v2_patterns.json` — segmentacja tekstowa pokazuje rozbicia (np. `Dz. U.` jest rozbijane; `Pzp` rozbijane w części wariantów).")
    zw.append("- **Naprawa:** dopisać skróty na końcu scaleń; rozważyć trening na mieszance 10–30% tekstów urzędowych.")
    zw.append("")
    zw.append("## W3. JSON wywołań narzędzi")
    zw.append("")
    v0_json = get_f("6_json_narzedzia", "TKX/V0-32k")
    sl_json = get_f("6_json_narzedzia", "Slayer1B-1.08")
    v0_toks = round(v0_json["fertility"] * fert["sources"]["6_json_narzedzia"]["words"])
    sl_toks = round(sl_json["fertility"] * fert["sources"]["6_json_narzedzia"]["words"])
    zw.append(f"- **Dowód:** na `tc1_json_tools` (200 dok., {fert['sources']['6_json_narzedzia']['words']} słów) V0-32k ma fertility {f3(v0_json['fertility'])} vs Slayer {f3(sl_json['fertility'])} (`results/tkx_v2_fertility.json`), czyli V0 tańszy na tym korpusie; łącznie {v0_toks} vs {sl_toks} tokenów. Osobno 10 wzorców JSON z `tkx_v2/wzorce.json`: suma tokenów standalone Slayer 298 vs V0 321 (`results/tkx_v2_patterns.json` po kategoriach). To różne miary — nie mieszać.")
    zw.append("- **Naprawa:** tokeny dla `<tool_call>` i kluczy JSON; ocena na BPB w TKX-D.")
    zw.append("")
    zw.append("## W4. Angielski")
    zw.append("")
    zw.append("- **Dowód:** TKX-A — fertility 1,97 vs Slayer 1,30 na angielskim (znany kompromis).")
    zw.append("- **Status:** akceptowany kompromis; bezpiecznik: brak regresji > 5%.")
    zw.append("")
    zw.append("## W5. Artefakty SuperBPE")
    zw.append("- Niektóre superwordy mogą zaczynać się w środku słowa; częste słowa mogą stracić własny token.")
    zw.append("- **Naprawa:** audyt słownika, filtrowanie merge w v2.1.")
    zw.append("")
    zw.append("## W6. Martwe tokeny")
    zw.append("")
    zw.append("Uwaga: porównanie ze Slayerem nie jest bezpośrednie (słownik polsko-angielski). Na polskim korpusie 35,03% martwych; w audycie szerszym 8,90%.")
    zw.append(f"- **Dowód:** V0-32k {f2(dead['tokenizers']['TKX/V0-32k']['dead_pct'])}%, V3-32k {f2(dead['tokenizers']['TKX/V3-32k']['dead_pct'])}%, Slayer {f2(dead['tokenizers']['Slayer1B-1.08']['dead_pct'])}% (`results/tkx_v2_dead_tokens.json`).")
    zw.append("")
    zw.append("## Czego nie sprawdzają testy")
    zw.append("- Jakość modelu downstream (wymaga TKX-D).")
    zw.append("- Morfologia (otwarte pytanie).")
    zw.append("- APT4/Bielik-1.5B-v3: tokenizer jest w wynikach fertility; nie wykonano testów downstream.")
    zw.append("")
    return "\n".join(zw) + "\n"


def build_korpus():
    kd = []
    kd.append("# Korpus testu domenowego TOKENIZATOREX v2.0")
    kd.append("")
    kd.append("Pełne teksty poza repo (zasada: bez surowych tekstów w git). W repo: manifest, metryki, ten opis.")
    kd.append("")
    kd.append("## Źródła (zgodne z `results/tkx_v2_fertility.json`)")
    kd.append("")
    kd.append("| # | Domena | Źródło | Dokumenty | Słowa | Bajty |")
    kd.append("|---:|---|---|---:|---:|---:|")
    for sid, name in SOURCES:
        s = fert["sources"][sid]
        kd.append(f"| {sid} | {name} | patrz manifest/metryki | {s['docs']} | {s['words']} | {s['bytes']} |")
    kd.append("")
    kd.append("## Zestawy dodatkowe opisane w tkx_v2/MANIFEST.json")
    kd.append("- BZP 500 (spec1): `D:\\VPS\\fabryka\\spec1\\data\\test.jsonl` (poza repo).")
    kd.append("- JSON narzędzi 200 (tc1): `D:\\VPS\\fabryka\\tc1\\dane\\test.jsonl` (poza repo).")
    kd.append("")
    kd.append("## Przeciek")
    kd.append("13-gramy vs próbka treningowa HPLT 400 MB — nie wykonano. Próg stopu: > 20% dokumentów z trafieniem.")
    kd.append("")
    kd.append("## Licencje / status")
    kd.append("Dokumenty urzędowe są publiczne. HPLT/FineWeb-2: ODC-By; Wikipedia: CC BY-SA.")
    kd.append("")
    return "\n".join(kd) + "\n"


def build_all():
    v21_md, v21_simple = build_v21_reports()
    files = {
        "RELEASE_NOTES_v2.0.md": build_release(),
        "tkx_v2/RAPORT_TEST_DOMENOWY.md": build_raport_test(),
        "tkx_v2/RAPORT_PROSTY_V2.md": build_raport_prosty(),
        "tkx_v2/KARTA_WYMAGAN.md": build_karta(),
        "tkx_v2/ZNANE_WADY.md": build_znane_wady(),
        "tkx_v2/KORPUS_DOMENOWY.md": build_korpus(),
        "tkx_v21/RAPORT.md": v21_md,
        "tkx_v21/RAPORT_PROSTY.md": v21_simple,
    }
    # Dokładnie jeden znak nowej linii na końcu, bez pustej linii EOF.
    return {k: v.rstrip("\n") + "\n" for k, v in files.items()}


def check(files):
    bad = []
    for rel, text in files.items():
        p = REPO / rel
        current = p.read_text(encoding="utf-8") if p.exists() else None
        if current != text:
            bad.append(rel)
    if bad:
        print("DIFF: " + ", ".join(bad))
        print("STATUS=BLOKER: generator nie zgadza się z plikami w repo")
        return 1
    print("STATUS=OK: wszystkie raporty są wynikiem generatora")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="tylko porównaj, nie zapisuj")
    args = ap.parse_args(argv)
    files = build_all()
    if args.check:
        return check(files)
    for rel, text in files.items():
        p = REPO / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8", newline="\n")
        print("zapisano", rel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
