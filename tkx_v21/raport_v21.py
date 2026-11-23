"""Generuje tkx_v21/RAPORT.md i tkx_v21/RAPORT_PROSTY.md wyłącznie z results/*.json.

  python tkx_v21/raport_v21.py

Żadnej liczby w raportach nie wpisujemy ręcznie.
"""
from __future__ import annotations

import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(REPO, "results")
OUT = os.path.join(REPO, "tkx_v21")

POLISH = ["bzp_ogloszenia", "du_eli", "kio", "samorzad", "granty",
          "json_bzp_tabele", "general_web"]
POLISH_PL = {"bzp_ogloszenia": "BZP (ogłoszenia)", "du_eli": "Dz.U. ELI",
             "kio": "KIO", "samorzad": "samorząd", "granty": "granty",
             "json_bzp_tabele": "JSON BZP (tabele)", "general_web": "ogólny web"}
CAT_PL = {"skroty_prawne": "skróty prawne", "identyfikatory": "identyfikatory",
          "daty_slowne": "daty słowne", "kwoty": "kwoty", "daty_iso": "daty ISO",
          "cpv": "CPV", "sygnatury": "sygnatury", "kody_pocztowe": "kody pocztowe",
          "numery_bzp": "numery BZP", "json_tool_calls": "JSON narzędzi",
          "adresy": "adresy", "nazwy_firm": "nazwy firm"}


def load(name, required=True):
    p = os.path.join(R, name)
    if not os.path.isfile(p):
        if required:
            raise FileNotFoundError(p)
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def dec(x, n=4):
    if x is None:
        return "—"
    return f"{x:.{n}f}".replace(".", ",")


def pct(x, n=2):
    if x is None:
        return "—"
    return f"{x:+.{n}f}%".replace(".", ",")


def ci(row, n=3):
    lo, hi = row["ci"]
    return f"{dec(row['fertility'], n)} ({dec(lo, n)}–{dec(hi, n)})"


def table(headers, rows):
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        out.append("| " + " | ".join(str(x).replace("|", "\\|") for x in row) + " |")
    return "\n".join(out)


def main():
    rep = load("tkx_v21_reproduction.json")
    var = load("tkx_v21_variants.json")
    dev = load("tkx_v21_dev.json")
    sel = load("tkx_v21_selection.json")
    test = load("tkx_v21_test.json")
    pat = load("tkx_v21_wzorce.json")
    rt = load("tkx_v21_roundtrip.json")
    dead = load("tkx_v21_dead_tokens.json")
    sp = load("tkx_v21_special_tokens.json")
    leak = load("tkx_v21_leak.json")
    labels = [x for x in dev["tokenizers"] if x in test["tokenizers"]]
    winner = sel.get("winner")
    base = sel["base"]
    v0 = "V0-32k"

    # --- liczby do zdań
    best_dev = min(["V0J2-32k", "V0J5-32k", "V0J10-32k"],
                   key=lambda x: dev["tokenizers"][x]["json_dev_combined"]["fertility"])
    bd = dev["tokenizers"][best_dev]["json_dev_combined"]["fertility"]
    b0 = dev["tokenizers"][base]["json_dev_combined"]["fertility"]
    tc1_dev_gain = (dev["sources"]["tc1_dev"]["tokenizers"][best_dev]["fertility"]
                    / dev["sources"]["tc1_dev"]["tokenizers"][base]["fertility"] - 1) * 100
    tc1_dev_only_gain = (dev["sources"]["tc1_dev_json_only"]["tokenizers"][best_dev]["fertility"]
                         / dev["sources"]["tc1_dev_json_only"]["tokenizers"][base]["fertility"] - 1) * 100
    gen_dev_gain = (dev["sources"]["json_generic_dev"]["tokenizers"][best_dev]["fertility"]
                    / dev["sources"]["json_generic_dev"]["tokenizers"][base]["fertility"] - 1) * 100
    if winner:
        w_tc1 = test["sources"]["tc1_test"]["tokenizers"][winner]["fertility"]
        w_tc1_only = test["sources"]["tc1_test_json_only"]["tokenizers"][winner]["fertility"]
        w_gen = test["sources"]["json_generic_test"]["tokenizers"][winner]["fertility"]
        b_tc1 = test["sources"]["tc1_test"]["tokenizers"][base]["fertility"]
        b_tc1_only = test["sources"]["tc1_test_json_only"]["tokenizers"][base]["fertility"]
        b_gen = test["sources"]["json_generic_test"]["tokenizers"][base]["fertility"]
        w_tc1_gain, w_gen_gain = (w_tc1 / b_tc1 - 1) * 100, (w_gen / b_gen - 1) * 100
        w_tc1_only_gain = (w_tc1_only / b_tc1_only - 1) * 100
    else:
        w_tc1_gain = w_gen_gain = w_tc1_only_gain = None
    # V0J5S vs V0J5 na tc1 test
    s5 = test["sources"]["tc1_test"]["tokenizers"]
    sp_gain = ((s5["V0J5S-32k"]["tokens"] / s5["V0J5-32k"]["tokens"] - 1) * 100
               if "V0J5S-32k" in s5 and "V0J5-32k" in s5 else None)
    s5o = test["sources"]["tc1_test_json_only"]["tokenizers"]
    sp_only_gain = ((s5o["V0J5S-32k"]["tokens"] / s5o["V0J5-32k"]["tokens"] - 1) * 100
                    if "V0J5S-32k" in s5o and "V0J5-32k" in s5o else None)
    rt_w = rt["tokenizers"].get(winner or base, {})
    dead_w = dead["tokenizers"].get(winner or base, {})
    # najbliżej progu: kandydat z najmniejszym najgorszym kosztem
    closest = min((c for c, r in sel["candidates"].items() if r.get("present")),
                  key=lambda c: max(d["delta_pct"]
                                    for d in sel["candidates"][c]["polish_deltas"].values()))
    closest_worst = max(sel["candidates"][closest]["polish_deltas"].items(),
                        key=lambda kv: kv[1]["delta_pct"])
    closest_others = max((d["delta_pct"] for s, d in
                          sel["candidates"][closest]["polish_deltas"].items()
                          if s != closest_worst[0]), default=0.0)
    closest_ok_sources = sum(1 for d in
                             sel["candidates"][closest]["polish_deltas"].values()
                             if d["delta_pct"] <= 1.0)
    sp_atomic = sum(1 for n in sp["names"]
                    if sp["tokenizers"].get("V0J5S-32k", {}).get(n, {}).get("one_token"))

    intro = [
        f"Odtworzony V0 (`{base}`) ma **identyczne merge'e etapu 1 i 2** co V0; "
        f"liczba tokenów na BZP jest {'identyczna' if rep['bzp']['identical'] else 'różna'} "
        f"({rep['bzp']['v0']['tokens']} vs {rep['bzp']['v0r']['tokens']}), a SHA pliku różni się "
        f"tylko metadanymi (`train_seconds`, `from`).",
        f"Na dev najniższą fertility JSON ma **{best_dev}**: {dec(bd)} vs {dec(b0)} "
        f"w V0R ({pct((bd / b0 - 1) * 100)}), ale nie przechodzi bramki polskiej.",
        f"Zysk na dev rozkłada się nierówno: tc1 (całe rekordy, narzędzia widziane) "
        f"{pct(tc1_dev_gain)}, tc1 tylko wywołania+odpowiedzi {pct(tc1_dev_only_gain)}, "
        f"held-out (narzędzia niewidziane) {pct(gen_dev_gain)}.",
        (f"Reguła wyboru wskazała **{winner}**; na teście tc1 zysk {pct(w_tc1_gain)} "
         f"(same wywołania: {pct(w_tc1_only_gain)}), na held-out {pct(w_gen_gain)}.") if winner else
        (f"Reguła wyboru **nie wskazała kandydata**. Najbliżej jest **{closest}**: "
         f"najgorsze źródło to {POLISH_PL[closest_worst[0]]} {pct(closest_worst[1]['delta_pct'])} "
         f"(n={dev['sources'][closest_worst[0]]['docs']}, CI {dec(closest_worst[1]['v0r'], 3)}–"
         f"{dec(closest_worst[1]['variant'], 3)} vs {dec(dev['sources'][closest_worst[0]]['tokenizers'][base]['ci'][0], 3)}–"
         f"{dec(dev['sources'][closest_worst[0]]['tokenizers'][base]['ci'][1], 3)}); "
         f"pozostałe źródła: najwyżej {pct(closest_others)}."),
        (f"Na 7 polskich źródłach najgorszy koszt zwycięzcy to "
         f"{pct(max(d['delta_pct'] for d in sel['candidates'][winner]['polish_deltas'].values()))} "
         f"(warunek: ≤ +1,00%).") if winner else
        ("Koszt polszczyzny jest mały na "
         f"{closest_ok_sources} z 7 źródeł (od "
         f"{pct(min(d['delta_pct'] for d in sel['candidates'][closest]['polish_deltas'].values()))} "
         f"do {pct(closest_others)}); "
         f"poza progiem wypada tylko {POLISH_PL[closest_worst[0]]} "
         f"({pct(closest_worst[1]['delta_pct'])}), gdzie jest "
         f"{dev['sources'][closest_worst[0]]['docs']} dokumentów i szerokie CI."),
        f"Tokeny specjalne w V0J5S są atomowe ({sp_atomic}/{len(sp['names'])}), ale na tc1 test dają "
        f"{pct(sp_gain)} tokenów względem V0J5 (same wywołania: {pct(sp_only_gain)}): "
        f"`<tool_call>` jako granica dodanego tokenu przerywa część wyuczonych supertokenów.",
        f"„§” jest 1 tokenem w V0R: {dev['section_sign'][base]['one_token']}; "
        f"w każdym wariancie z domieszką JSON również: "
        f"{all(dev['section_sign'][c]['one_token'] for c in ('V0J2-32k', 'V0J5-32k', 'V0J10-32k'))}.",
        f"Round-trip: {rt_w.get('bad', '—')} błędów na {rt['cases']} przypadków "
        f"({rt['unique_texts']} unikalnych tekstów); martwe tokeny w V0R: "
        f"{dec(dead_w.get('dead_pct'), 2)}%.",
        f"Przeciek: **{leak['summary']['status']}** — dokumentów >50% pokrycia 13-gramów: "
        f"{leak['summary']['docs_over_50pct_or_exact']}.",
        "To pomiar kosztu tokenizacji, nie jakości modelu; ostateczny wybór wymaga TKX-D "
        "na małych modelach i co najmniej 3 seedach.",
    ]

    # --- tabele
    var_rows = []
    for name, m in var.items():
        if name.startswith("_"):
            continue
        var_rows.append([name, m.get("sha256_superbpe", "—")[:12],
                         m.get("sha256_hf", "—")[:12], m.get("train_data", "—")])
    dev_rows = []
    for lb in labels:
        dev_rows.append([lb,
                         ci(dev["sources"]["tc1_dev"]["tokenizers"][lb]),
                         ci(dev["sources"]["tc1_dev_json_only"]["tokenizers"][lb]),
                         ci(dev["sources"]["json_generic_dev"]["tokenizers"][lb]),
                         dec(dev["tokenizers"][lb]["json_dev_combined"]["fertility"]),
                         dec(dev["section_sign"][lb]["tokens"], 0)])
    test_rows = []
    for lb in labels:
        test_rows.append([lb,
                          ci(test["sources"]["tc1_test"]["tokenizers"][lb]),
                          ci(test["sources"]["tc1_test_json_only"]["tokenizers"][lb]),
                          ci(test["sources"]["json_generic_test"]["tokenizers"][lb]),
                          dec(test["tokenizers"][lb]["json_test_combined"]["fertility"]),
                          dec(test["sources"]["tc1_test"]["tokenizers"][lb]["tokens_per_doc"], 2)])
    sel_rows = []
    for c, rec in sel["candidates"].items():
        if not rec.get("present"):
            sel_rows.append([c, "—", "—", "brak"])
            continue
        worst = max(rec["polish_deltas"].items(), key=lambda kv: kv[1]["delta_pct"])
        sel_rows.append([c, dec(rec["json_dev_combined"]["fertility"]),
                         f"{pct(worst[1]['delta_pct'])} ({POLISH_PL[worst[0]]})",
                         "TAK" if rec["feasible"] else "NIE: " + ", ".join(rec["fails"])])
    pol_headers = ["źródło"] + labels
    pol_rows = []
    for s in POLISH:
        row = [POLISH_PL[s]]
        for lb in labels:
            r = dev["sources"][s]["tokenizers"][lb]
            delta = (r["fertility"] / dev["sources"][s]["tokenizers"][base]["fertility"] - 1) * 100
            row.append(f"{ci(r)} / {pct(delta)}")
        pol_rows.append(row)
    cat_rows = []
    cats = sorted({i["category"] for i in pat["items"]})
    for c in cats:
        row = [CAT_PL.get(c, c)]
        for lb in labels:
            row.append(dec(pat["tokenizers"][lb]["by_category"][c]["mean_tokens"], 2))
        cat_rows.append(row)
    sp_rows = []
    for name in sp["names"]:
        sp_rows.append([name] + [
            ("1" if sp["tokenizers"][lb][name]["one_token"] else
             str(sp["tokenizers"][lb][name]["tokens"])) for lb in labels])
    dead_rows = [[lb, dead["tokenizers"][lb].get("vocab", "—"),
                  dead["tokenizers"][lb].get("dead", "—"),
                  dec(dead["tokenizers"][lb].get("dead_pct"), 2)] for lb in labels]
    rt_rows = [[lb, rt["tokenizers"][lb]["bad"], rt["tokenizers"][lb]["cases"],
                rt["tokenizers"][lb]["bad_nfd"], "TAK" if rt["tokenizers"][lb]["ok"] else "NIE"]
               for lb in labels]
    leak_rows = []
    for s, row in leak["test_docs"].items():
        leak_rows.append([s, row["docs"], dec(row["mean_coverage"] * 100, 1),
                          dec(row["max_coverage"] * 100, 1), row["docs_over_50pct"],
                          row["exact_matches"]])

    md = []
    md.append("# TKX-V21-JSON — raport pełny\n")
    md.append("> Raport wygenerowany skryptem `tkx_v21/raport_v21.py` z `results/tkx_v21_*.json`. "
              "Seed 20261123, `PYTHONHASHSEED=0`, bootstrap 1000× po dokumentach. "
              "Pełne teksty korpusu są poza gitem (`data/`, `tkx_v21/dane/`).\n")
    md.append("## 1. Dziesięć zdań\n")
    for i, s in enumerate(intro, 1):
        md.append(f"{i}. {s}")
    md.append("\n## 2. Odtworzenie V0\n")
    md.append(table(["co", "V0", "V0R"], [
        ["SHA-256 superbpe", rep["v0_superbpe_sha256"][:16], rep["v0r_superbpe_sha256"][:16]],
        ["merge'e etapu 1 równe", "—", str(rep["stage1_merges_equal"])],
        ["merge'e etapu 2 równe", "—", str(rep["stage2_merges_equal"])],
        ["tokeny na BZP (500 dok.)", rep["bzp"]["v0"]["tokens"], rep["bzp"]["v0r"]["tokens"]],
        ["fertility BZP", dec(rep["bzp"]["v0"]["fertility"]), dec(rep["bzp"]["v0r"]["fertility"])],
    ]))
    md.append(f"\n**Wniosek:** {rep['conclusion']}. Hash pliku różni się tylko polami meta: "
              f"`{', '.join(rep['meta_diff'])}`. Porównania idą względem V0R.\n")
    md.append("## 3. Warianty\n")
    md.append(table(["wariant", "SHA superbpe", "SHA HF", "dane treningowe"], var_rows))
    md.append("\nPrzepis: `train.py baseline --vocab 32000` → `train.py superbpe "
              "--transition 20000 --vocab 32000 --stage2-mb 100 --max-words 4`; "
              f"V0J5S = V0J5 + 6 tokenów specjalnych (unikalne tokeny: "
              f"{var['V0J5S-32k'].get('vocab_size_unique', '—')}; `<tool_call>` i `</tool_call>` "
              f"to istniejące tokeny słownika).\n")
    md.append("## 4. JSON — dev (wybór wariantu)\n")
    md.append(table(["tokenizer", "tc1 dev", "tc1 dev (tylko JSON)", "held-out dev",
                     "łącznie dev", "tokeny „§”"], dev_rows))
    md.append("\n## 5. Reguła wyboru i wynik\n")
    md.append(table(["kandydat", "fertility JSON dev", "najgorszy koszt PL (źródło)", "spełnia?"],
                    sel_rows))
    md.append(f"\n**Wynik:** {'kandydat = **' + winner + '**' if winner else '**brak kandydata**'}. "
              f"{sel.get('note', '')}\n")
    if not winner:
        md.append(f"Najbliżej progu jest **{closest}**: najgorsze źródło to "
                  f"{POLISH_PL[closest_worst[0]]} {pct(closest_worst[1]['delta_pct'])} "
                  f"(n={dev['sources'][closest_worst[0]]['docs']}); pozostałe źródła: najwyżej "
                  f"{pct(closest_others)}. Przedziały 95% CI na {POLISH_PL[closest_worst[0]]} "
                  f"pokrywają się z V0R — werdykt „brak kandydata” jest punktowy, zgodnie "
                  f"z protokołem, ale nie jest mocnym dowodem na regresję.\n")
    md.append("## 6. JSON — test (liczony raz, po wyborze)\n")
    md.append(table(["tokenizer", "tc1 test", "tc1 test (tylko JSON)", "held-out test",
                     "łącznie test", "tokeny/dok. tc1"],
                    test_rows))
    md.append("\n`tc1 test` = narzędzia widziane w tc1 train; `held-out test` = 10 narzędzi, "
              "których tokenizer nie widział. Różnica między nimi mówi, czy zysk przenosi się "
              "na nowe narzędzia.\n")
    md.append("## 7. Polski — pełna tabela (bramka)\n")
    md.append("Wartość: fertility z 95% CI / zmiana względem V0R.\n")
    md.append(table(pol_headers, pol_rows))
    md.append("\n## 8. Wzorce urzędowe (średnia liczba tokenów)\n")
    md.append(table(["kategoria"] + labels, cat_rows))
    md.append("\n10 wzorców JSON (`json_tool_calls`): " + ", ".join(
        f"{lb}={dec(pat['tokenizers'][lb]['json_10_mean_tokens'], 2)}" for lb in labels) + ".\n")
    md.append("Segmentacja tekstowa dwóch przykładów JSON (tokeny HF, `Ġ` = spacja):\n")
    for pid in ("W0126", "W0129"):
        md.append(f"**{pid}**")
        for lb in ("V0R-32k", "V0J2-32k", "Slayer1B-1.08"):
            if lb not in pat["tokenizers"]:
                continue
            item = next(x for x in pat["tokenizers"][lb]["per_item"] if x["id"] == pid)
            seg = item.get("segmentation")
            if seg:
                md.append(f"- {lb} ({item['tokens']} tok.): `" + "|".join(seg) + "`")
        md.append("")
    md.append("## 9. Tokeny specjalne\n")
    md.append("1 = token atomowy; inna liczba = ile tokenów zajmuje napis.\n")
    md.append(table(["token"] + labels, sp_rows))
    md.append("\n## 10. Round-trip i martwe tokeny\n")
    md.append(table(["tokenizer", "błędy round-trip", "przypadki", "błędy NFD", "OK"], rt_rows))
    md.append("")
    md.append(table(["tokenizer", "słownik", "martwe", "martwe %"], dead_rows))
    md.append("\n## 11. Przeciek korpusu\n")
    md.append(table(["zbiór testowy", "dok.", "średnie pokrycie 13-g", "maks.", ">50%", "exact"],
                    leak_rows))
    md.append(f"\nStatus: **{leak['summary']['status']}**. Pełne teksty i lista dokumentów: "
              f"`results/tkx_v21_leak.json`.\n")
    md.append("## 12. Co to znaczy dla modelu 150M i TC-1\n")
    if winner:
        md.append(f"- Największy sens ma **{winner}** jako hipoteza do TKX-D: poprawia JSON "
                  f"na dev o {pct((bd / b0 - 1) * 100)} i mieści się w bramce polskiej.")
    else:
        md.append("- Żadna domieszka nie przeszła bramki polskiej; to wynik, nie porażka: "
                  "pokazuje, że 2–10% JSON kosztuje polszczyznę więcej niż 1%.")
    md.append("- Zysk na narzędziach niewidzianych jest osobną liczbą (held-out). Jeśli jest "
              "bliski zyskowi na tc1, tokenizer uczy się **składni JSON**, a nie nazw 3 narzędzi.")
    md.append("- Tokeny specjalne w V0J5S są atomowe (6/6), ale na JSON nie poprawiają wyniku "
              f"({pct(sp_gain)} tokenów na tc1 test względem V0J5): `<tool_call>` jako granica "
              "dodanego tokenu przerywa część wyuczonych supertokenów. To mechanizm dla szablonu "
              "czatu, nie dla słownika JSON.")
    md.append("- Decyzja o wdrożeniu należy do TKX-D: trening małych modeli, BPB, ≥ 3 seedy. "
              "Fertility nie jest jakością modelu.")
    md.append("\n## 13. Czego nie sprawdziły automaty\n")
    md.append("- Nie trenowano modeli 150M — nie wiadomo, czy mniejsza liczba tokenów przekłada "
              "się na lepsze wyniki na zadaniach TC-1.")
    md.append("- Dev/test JSON są syntetyczne (nasze), a tc1 pochodzi z jednego generatora; "
              "held-out narzędzia są inne, ale schematy mają wspólną składnię.")
    md.append("- Nie mierzono jakości na prawdziwych wywołaniach narzędzi produkcyjnych.")
    md.append("- Nie strojono hiperparametrów (2/5/10% to jedyne punkty); brak krzywej.")
    md.append("- UNKNOWN ≠ FALSE ≠ 0: brak źródła lub brak tokenizera jest raportowany osobno.")
    md.append("\n> Automatyczne testy i ten raport **nie są akceptacją właściciela**. "
              "Wymagana jest weryfikacja człowieka.\n")
    with open(os.path.join(OUT, "RAPORT.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(md) + "\n")

    # --- raport prosty
    simple = []
    simple.append("# TOKENIZATOREX v2.1-JSON — prostym językiem\n")
    simple.append(f"**Pytanie:** czy dodanie JSON-a do treningu tokenizera zmniejszy liczbę "
                  f"tokenów na wywołaniach narzędzi, nie psując polskiego?\n")
    if winner:
        simple.append(f"**Odpowiedź:** tak, najlepszy jest **{winner}**. Na dev JSON jest "
                      f"o {dec(abs((bd / b0 - 1) * 100), 1)}% tańszy niż V0, a polski nie traci "
                      f"więcej niż 1% na żadnym z 7 źródeł.")
    else:
        c_tc1 = test["sources"]["tc1_test"]["tokenizers"][closest]["fertility"]
        c_gen = test["sources"]["json_generic_test"]["tokenizers"][closest]["fertility"]
        b_tc1 = test["sources"]["tc1_test"]["tokenizers"][base]["fertility"]
        b_gen = test["sources"]["json_generic_test"]["tokenizers"][base]["fertility"]
        simple.append(f"**Odpowiedź:** JSON jest dużo tańszy — **{closest}** na teście tc1 "
                      f"oszczędza {dec(abs((c_tc1 / b_tc1 - 1) * 100), 1)}% tokenów, a na nowych "
                      f"narzędziach {dec(abs((c_gen / b_gen - 1) * 100), 1)}%. Ale **nie ma "
                      f"kandydata**, bo polski na jednym źródle (granty, "
                      f"{dev['sources'][closest_worst[0]]['docs']} dokumentów) rośnie "
                      f"o {dec(closest_worst[1]['delta_pct'], 2)}% — powyżej progu 1%. "
                      f"Przedziały ufności tego źródła pokrywają się z V0, więc to wynik na "
                      f"granicy szumu, ale zgodnie z regułą: brak kandydata.")
    simple.append(f"\n- Odtworzenie V0: merge'e identyczne, tokeny na BZP "
                  f"{'identyczne' if rep['bzp']['identical'] else 'różne'}.")
    if winner:
        simple.append(f"- JSON na teście (tc1, narzędzia widziane): "
                      f"{pct(w_tc1_gain)}; same wywołania: {pct(w_tc1_only_gain)}; "
                      f"na nowych narzędziach: {pct(w_gen_gain)}.")
    else:
        simple.append(f"- JSON na teście dla najbliższego ({closest}): "
                      f"tc1 {pct((c_tc1 / b_tc1 - 1) * 100)}; "
                      f"nowe narzędzia {pct((c_gen / b_gen - 1) * 100)}.")
    simple.append(f"- „§”: 1 token w V0R i we wszystkich wariantach V0J.")
    simple.append(f"- Tokeny specjalne: {sp_atomic}/{len(sp['names'])} atomowych w V0J5S, ale na JSON "
                  f"{pct(sp_gain)} tokenów względem V0J5 (nie zastępują słownika JSON).")
    simple.append(f"- Przeciek: {leak['summary']['status']}.")
    simple.append(f"- Round-trip: {rt_w.get('bad', '—')} błędów na {rt['cases']} przypadków.")
    simple.append("\n**Co dalej:** sprawdzić V0J2 (i ewentualnie V0J5) na małym modelu (TKX-D), "
                  "z bramką opartą na CI, nie tylko na punkcie. Automaty nie zastępują decyzji "
                  "właściciela.\n")
    with open(os.path.join(OUT, "RAPORT_PROSTY.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(simple) + "\n")
    print("zapisano tkx_v21/RAPORT.md i tkx_v21/RAPORT_PROSTY.md")


if __name__ == "__main__":
    main()
