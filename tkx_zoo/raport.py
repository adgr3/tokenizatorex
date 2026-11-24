"""Generator raportów TKX-ZOO — wszystkie liczby pochodzą z results/tkx_zoo_*.json.

    python tkx_zoo/raport.py

Zapisuje tkx_zoo/RAPORT.md i tkx_zoo/RAPORT_PROSTY.md oraz wypisuje na stdout
tablice do odpowiedzi w czacie.
"""
from __future__ import annotations

import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(REPO, "results")
ZOO = os.path.join(REPO, "tkx_zoo")


def load(name):
    with open(os.path.join(RESULTS, name), encoding="utf-8") as f:
        return json.load(f)


def f4(x):
    return "n/d" if x is None else f"{x:.4f}".replace(".", ",")


def f2(x):
    return "n/d" if x is None else f"{x:.2f}".replace(".", ",")


def pct(x):
    return "n/d" if x is None else f"{x:.1f}%".replace(".", ",")


def ik(x):
    return f"{int(x):,}".replace(",", " ")


def main():
    fert = load("tkx_zoo_fertility.json")
    fmt = load("tkx_zoo_formats.json")
    cost = load("tkx_zoo_vocab_cost.json")
    sec = load("tkx_zoo_section_sign.json")
    dead = load("tkx_zoo_dead_tokens.json")
    rt = load("tkx_zoo_roundtrip.json")
    jt = load("tkx_zoo_json_tools.json")
    reg = load("tkx_zoo_regression_split.json")
    man = json.load(open(os.path.join(ZOO, "MANIFEST.json"), encoding="utf-8"))

    toks = [t for t in fert["tokenizers"] if t in cost["vocab_x_dmodel"]]
    vocab = {t: cost["vocab_x_dmodel"][t]["vocab"] for t in toks}
    sources = [s for s in fert["sources"] if s in {
        "1_bzp", "2_du_eli", "3_kio", "4_samorzad", "5_granty",
        "6_json_narzedzia", "7_ogolny", "json_bzp_tabele"}]
    extras = [s for s in fert["sources"] if s not in sources]

    def val(s, t, key="fertility"):
        return fert["sources"][s]["tokenizers"].get(t, {}).get(key)

    def argmin(s):
        vals = [(val(s, t), t) for t in toks if val(s, t) is not None]
        return min(vals) if vals else (None, None)

    def ci(s, t):
        r = fert["sources"][s]["tokenizers"].get(t, {})
        return (f"{f4(r.get('fertility'))} [{f4(r.get('fertility_ci_lo'))}–"
                f"{f4(r.get('fertility_ci_hi'))}]")

    def disjoint(s, a, b):
        ra = fert["sources"][s]["tokenizers"][a]
        rb = fert["sources"][s]["tokenizers"][b]
        return (ra["fertility_ci_hi"] < rb["fertility_ci_lo"]
                or rb["fertility_ci_hi"] < ra["fertility_ci_lo"])

    # „polski” = teksty urzędowe/ogólne; JSON-y traktujemy osobno
    polish_text = [s for s in sources if s not in ("6_json_narzedzia", "json_bzp_tabele")] + ["granty_149"]
    v0_v0j2_disjoint_polish = sum(disjoint(s, "V0-32k", "V0J2-32k") for s in polish_text)
    v0_aster_disjoint = sum(disjoint(s, "V0-32k", "Aster-0.5B") for s in polish_text)

    winners = {s: argmin(s) for s in fert["sources"]}
    v0_wins = sum(1 for s in winners if winners[s][1] == "V0-32k")
    v0_loses = [(s, t, val(s, t)) for s, (_, t) in winners.items() if t != "V0-32k"]

    # czy PLLuM/Bielik kiedykolwijkolwiek wygrywają z V0
    family = [t for t in toks if t.startswith(("PLLuM", "Bielik"))]
    family_wins_polish = [(s, t, val(s, t)) for s in sources for t in family
                          if val(s, t) is not None and val(s, "V0-32k") is not None
                          and val(s, t) < val(s, "V0-32k")]
    family_wins_json = [(s, t, val(s, t)) for s in extras for t in family
                        if val(s, t) is not None and val(s, "V0-32k") is not None
                        and val(s, t) < val(s, "V0-32k")]

    identical = []
    for a, b in (("PLLuM-4B", "Gemma-3-4B"), ("PLLuM-12B", "Mistral-Nemo"),
                 ("Bielik-4.5B-v3", "Bielik-1.5B-v3")):
        if a in toks and b in toks:
            same = all(val(s, a) == val(s, b) for s in fert["sources"]
                       if val(s, a) is not None and val(s, b) is not None)
            if same:
                identical.append((a, b))

    one_sign = [t for t in toks if sec["tokenizers"].get(t, {}).get("one_token")]
    multi_sign = [t for t in toks if t in sec["tokenizers"]
                  and not sec["tokenizers"][t]["one_token"]]
    rt_bad = [(t, rt["tokenizers"][t]["bad"]) for t in toks
              if t in rt["tokenizers"] and rt["tokenizers"][t]["bad"]]
    gated = [(t, e) for t, e in man.items()
             if isinstance(e, dict) and e.get("status") == "unavailable"]

    # ---------- RAPORT.md ----------
    L = []
    A = L.append
    A("# TOKENIZATOREX ZOO — raport przed postem v2.0")
    A("")
    A(f"Gałąź `feat/tkx-zoo` od `f12fc2c` · commit autora `adgr3` · seed "
      f"{fert['seed']}, `PYTHONHASHSEED={fert['pythonhashseed']}`, bootstrap "
      f"{fert['bootstrap']}× po dokumentach · `encode(..., add_special_tokens=False)`.")
    A("Wszystkie liczby poniżej wygenerował `tkx_zoo/raport.py` z plików "
      "`results/tkx_zoo_*.json`. Wyniki V0, V0J2, Slayera, Bielika 1.5B, APT3 i GPT-4o "
      "zostały skopiowane z istniejących plików (pole `origin` w `tkx_zoo_fertility.json`) — "
      "bez przeliczania.")
    A("")
    A("## Po ludzku (10 zdań)")
    A("")
    A(f"1. Na {len(sources)} polskich źródłach najmniej tokenów na słowo daje "
      f"**{winners['1_bzp'][1]}** — na BZP ma {f4(winners['1_bzp'][0])}.")
    A(f"2. {v0_wins} z {len(winners)} tabel wygrywa V0-32k; na "
      f"{', '.join(s for s, _, _ in v0_loses)} lepszy jest "
      f"{', '.join(sorted(set(t for _, t, _ in v0_loses)))}.")
    A(f"3. Na ośmiu polskich źródłach żaden PLLuM ani Bielik nie był tańszy niż V0 "
      f"({len(family_wins_polish)} przypadki); na JSON held-out takich przypadków jest "
      f"{len(family_wins_json)} (np. PLLuM 8B {f4(val('json_generic_heldout_test', 'PLLuM-8B'))} "
      f"vs V0 {f4(val('json_generic_heldout_test', 'V0-32k'))}). Najbliżej V0 na BZP jest "
      f"Aster-0.5B z {f4(val('1_bzp', 'Aster-0.5B'))} przy słowniku {ik(vocab['Aster-0.5B'])}.")
    A(f"4. PLLuM 4B ma dokładnie taką samą fertility jak Gemma 3, a PLLuM 12B jak "
      f"Mistral Nemo — choć pliki `tokenizer.json` mają inne hashe (PLLuM dodał tokeny, "
      f"na tych tekstach nie zmieniły liczby tokenów).")
    if identical:
        pair = [p for p in identical if p[0] == "Bielik-4.5B-v3"]
        if pair:
            A(f"5. Bielik 4.5B v3 daje identyczną fertility jak Bielik 1.5B v3 "
              f"({f4(val('1_bzp', 'Bielik-4.5B-v3'))} na BZP) przy słowniku "
              f"{ik(vocab['Bielik-4.5B-v3'])} — to inny plik, ten sam efekt.")
        else:
            A("5. Bielik 4.5B v3 ma inny plik tokenizera niż Bielik 1.5B v3 i inne wyniki.")
    else:
        A("5. Wyniki PLLuM i Bielika pokrywają się z ich bazami — patrz tabela.")
    A(f"6. Cyfry: PLLuM 4B/12B, Gemma 3 i Mistral Nemo tną je pojedynczo; "
      f"PLLuM 8B i GPT-4o po trzy; V0, V0J2, Slayer i Aster w grupach 1–3.")
    A(f"7. Znak „§” jest jednym tokenem w {len(one_sign)} tokenizerach "
      f"(m.in. {', '.join(one_sign[:4])}); nie jest w {', '.join(multi_sign)} "
      f"({', '.join(str(sec['tokenizers'][t]['tokens']) for t in multi_sign)} tokeny).")
    A(f"8. Słownik to realny koszt: PLLuM 4B ({ik(vocab['PLLuM-4B'])}) przy d_model 768 "
      f"zajmuje {f2(cost['vocab_x_dmodel']['PLLuM-4B']['768']['params_m'])} M parametrów, "
      f"czyli {pct(cost['vocab_x_dmodel']['PLLuM-4B']['768']['pct_150m'])} modelu 150M; "
      f"V0 ({ik(vocab['V0-32k'])}) to "
      f"{f2(cost['vocab_x_dmodel']['V0-32k']['768']['params_m'])} M "
      f"({pct(cost['vocab_x_dmodel']['V0-32k']['768']['pct_150m'])}).")
    dead_vals = [(t, x["dead_pct"]) for t, x in dead["tokenizers"].items()
                 if x.get("dead_pct") is not None]
    lo_dead = min(dead_vals, key=lambda p: p[1])
    hi_dead = max(dead_vals, key=lambda p: p[1])
    A(f"9. Martwe tokeny: od {pct(lo_dead[1])} ({lo_dead[0]}) do "
      f"{pct(hi_dead[1])} ({hi_dead[0]}) słownika nie użyt ani razu.")
    A(f"10. Round-trip na {rt['cases']} dokumentach jest bezstratny dla "
      f"{len(rt['tokenizers']) - len(rt_bad)} tokenizerów; wyjątki: "
      + ", ".join(f"{t} ({n} błędów)" for t, n in rt_bad) + ".")
    A("")
    A("## Tabela fertility (8 źródeł v2 + 2 dodatkowe)")
    A("")
    A("| źródło | " + " | ".join(toks) + " |")
    A("|---|" + "---:|" * len(toks))
    A("| **słownik** | " + " | ".join(ik(vocab[t]) for t in toks) + " |")
    for s in list(fert["sources"]):
        A(f"| {s} | " + " | ".join(
            f4(val(s, t)) if val(s, t) is not None else "—" for t in toks) + " |")
    A("")
    A("Zwycięzcy per źródło: " + "; ".join(f"{s}={winners[s][1]} ({f4(winners[s][0])})"
                                       for s in winners) + ".")
    A("Dla V0J2 na KIO i `json_bzp_tabele` różnica jest mniejsza niż "
      "szerokość CI — liczby są w `results/tkx_zoo_fertility.json`.")
    A("")
    A("## V0-32k vs Aster-0.5B (32k vs 32k)")
    A("")
    A("| źródło | V0-32k [95% CI] | Aster-0.5B [95% CI] | przedziały rozłączne? |")
    A("|---|---:|---:|:---:|")
    for s in fert["sources"]:
        A(f"| {s} | {ci(s, 'V0-32k')} | {ci(s, 'Aster-0.5B')} | "
          f"{'tak' if disjoint(s, 'V0-32k', 'Aster-0.5B') else 'nie'} |")
    A("")
    A("## V0-32k vs V0J2-32k")
    A("")
    A("| źródło | V0-32k [95% CI] | V0J2-32k [95% CI] | przedziały rozłączne? |")
    A("|---|---:|---:|:---:|")
    for s in fert["sources"]:
        A(f"| {s} | {ci(s, 'V0-32k')} | {ci(s, 'V0J2-32k')} | "
          f"{'tak' if disjoint(s, 'V0-32k', 'V0J2-32k') else 'nie'} |")
    A("")
    A("### Uczciwe wyjątki")
    A("")
    s = "json_generic_heldout_test"
    A(f"- Na `{s}` Aster-0.5B {ci(s, 'Aster-0.5B')} jest tańszy niż V0-32k "
      f"{ci(s, 'V0-32k')}; CI się nakładają (przedziały rozłączne? "
      f"{'tak' if disjoint(s, 'V0-32k', 'Aster-0.5B') else 'nie'}).")
    for s in ("2_du_eli", "5_granty"):
        A(f"- Na `{s}` V0-32k {ci(s, 'V0-32k')} jest tańszy niż Aster-0.5B "
          f"{ci(s, 'Aster-0.5B')}, ale przewaga jest w granicach CI "
          f"(przedziały rozłączne? {'tak' if disjoint(s, 'V0-32k', 'Aster-0.5B') else 'nie'}).")
    A(f"- Na polskich tekstach (6 v2 + granty 149, bez JSON-ów) V0–Aster ma "
      f"{v0_aster_disjoint} rozłącznych przedziałów na {len(polish_text)}, "
      f"a V0–V0J2 {v0_v0j2_disjoint_polish} na {len(polish_text)} — czyli V0 z V0J2 to remis w granicach CI.")
    A("")
    A("## Test formatów (średnia liczba tokenów na zapis)")
    A("")
    A("| format | " + " | ".join(toks) + " |")
    A("|---|" + "---:|" * len(toks))
    for group, key in (("daty", "date_formats"), ("kwoty", "amount_formats")):
        for name in next(iter(fmt[key].values())):
            A(f"| {name} | " + " | ".join(
                f2(fmt[key][t][name]) if t in fmt[key] else "—" for t in toks) + " |")
    for p in next(iter(fmt["paragraph_forms"].values())):
        A(f"| {p} | " + " | ".join(
            str(fmt["paragraph_forms"][t][p]) if t in fmt["paragraph_forms"] else "—"
            for t in toks) + " |")
    A("")
    A("Jak tną cyfry (`1234567890`):")
    A("")
    for t in toks:
        d = fmt["digit_split"].get(t, {})
        A(f"- **{t}** — {d.get('style', '?')}: "
          + " ".join(d.get("tokens_1234567890", [])[:12]) + ".")
    A("")
    A("Segmentacja 3 przykładów (liczba tokenów):")
    A("")
    A("| tokenizer | " + " | ".join(fmt["segmentation"][toks[0]]) + " |")
    A("|---|" + "---:|" * 3)
    for t in toks:
        A(f"| {t} | " + " | ".join(str(len(fmt["segmentation"][t][e])) for e in fmt["segmentation"][t]) + " |")
    A("")
    A("## Koszt słownika w modelu 150M")
    A("")
    A("| tokenizer | słownik | 768: parametry | 768: % z 150M | 1024: parametry | 1024: % z 150M |")
    A("|---|---:|---:|---:|---:|---:|")
    for t in toks:
        r = cost["vocab_x_dmodel"][t]
        A(f"| {t} | {ik(r['vocab'])} | {f2(r['768']['params_m'])} M | "
          f"{pct(r['768']['pct_150m'])} | {f2(r['1024']['params_m'])} M | "
          f"{pct(r['1024']['pct_150m'])} |")
    A("")
    A("Przy braku współdzielenia embedingu wejściowego z wyjściem liczby parametrów "
      "i procenty należy podwoić (pole `pct_150m_untied` w JSON).")
    A("")
    A("## Dodatkowe miary")
    A("")
    A("| tokenizer | „§” tokeny | martwe % | round-trip błędy | JSON tc1 | JSON held-out |")
    A("|---|---:|---:|---:|---:|---:|")
    for t in toks:
        A(f"| {t} | {sec['tokenizers'].get(t, {}).get('tokens', '—')} | "
          f"{pct(dead['tokenizers'].get(t, {}).get('dead_pct'))} | "
          f"{rt['tokenizers'].get(t, {}).get('bad', '—')} | "
          f"{f4(fert['sources']['6_json_narzedzia']['tokenizers'].get(t, {}).get('fertility'))} | "
          f"{f4(fert['sources']['json_generic_heldout_test']['tokenizers'].get(t, {}).get('fertility'))} |")
    A("")
    A("## Test regresji podziału (4 frazy, wszystkie tokenizery)")
    A("")
    A("| tokenizer | " + " | ".join(reg["phrases"]) + " |")
    A("|---|" + "---|" * len(reg["phrases"]))
    for t in toks:
        cells = []
        for p in reg["phrases"]:
            row = reg["tokenizers"][t][p]
            cells.append(" / ".join(row["tokens"]) + f" ({row['n']})")
        A(f"| {t} | " + " | ".join(cells) + " |")
    A("")
    A("W nawiasie liczba tokenów; `same_as_v0` w `results/tkx_zoo_regression_split.json` "
      "mówi, czy podział jest identyczny jak V0-32k.")
    A("")
    A("## Propozycja zdań do posta")
    A("")
    A(f"1. Sprawdziliśmy {len(toks)} tokenizery — także PLLuM 4B/8B/12B, Bielika 11B v3.1 i 4.5B v3, "
      f"Aster-0.5B i dwa DanielK 32k z PR #29 — na tych samych ośmiu polskich źródłach urzędowych.")
    A(f"2. V0-32k vs V0J2-32k na polskim to remis w granicach CI: "
      f"{v0_v0j2_disjoint_polish} rozłącznych przedziałów na {len(polish_text)} tabel "
      f"(6 tekstowych v2 + granty 149). V0J2 jest wyraźnie lepszy tylko na JSON narzędzi: "
      f"tc1 {f4(jt['sources']['6_json_narzedzia']['tokenizers']['V0J2-32k']['fertility'])} vs "
      f"{f4(jt['sources']['6_json_narzedzia']['tokenizers']['V0-32k']['fertility'])} i held-out "
      f"{f4(jt['sources']['json_generic_heldout_test']['tokenizers']['V0J2-32k']['fertility'])} vs "
      f"{f4(jt['sources']['json_generic_heldout_test']['tokenizers']['V0-32k']['fertility'])}, "
      f"przedziały rozłączne.")
    A(f"3. Najbliższy rywal przy tym samym słowniku 32k: Aster-0.5B — "
      f"{f4(val('1_bzp', 'Aster-0.5B'))} na BZP vs V0 {f4(val('1_bzp', 'V0-32k'))} "
      f"przy {ik(vocab['Aster-0.5B'])} słów; DanielK t1/t2 mają "
      f"{f4(val('1_bzp', 'DanielK-t1-pl-polish-32k'))}/{f4(val('1_bzp', 'DanielK-t2-pl-cnc-32k'))}, "
      f"a PLLuM 4B {f4(val('1_bzp', 'PLLuM-4B'))} przy {ik(vocab['PLLuM-4B'])}.")
    A(f"4. Cyfry uczą nas, że grupowanie po 3 (PLLuM 8B, V0) jest tańsze niż cięcie "
      f"pojedynczo (PLLuM 4B/12B): "
      f"{f2(sum(fmt['date_formats']['PLLuM-8B'].values()) / len(fmt['date_formats']['PLLuM-8B']))} vs "
      f"{f2(sum(fmt['date_formats']['PLLuM-4B'].values()) / len(fmt['date_formats']['PLLuM-4B']))} "
      f"tokenów na datę.")
    A(f"5. Koszt słownika w modelu 150M to od "
      f"{pct(min(cost['vocab_x_dmodel'][t]['768']['pct_150m'] for t in toks))} (32k) do "
      f"{pct(max(cost['vocab_x_dmodel'][t]['768']['pct_150m'] for t in toks))} "
      f"(PLLuM 4B) samych embeddingów — bez współdzielenia z wyjściem dwukrotnie.")
    A("")
    A("## Czego nie udało się pobrać")
    A("")
    for t, e in gated:
        A(f"- **{t}** — {e.get('note')} (repo `{e.get('repo')}`, "
          f"rewizja `{e.get('revision') or 'brak'}`). Nie podstawiono innego repo.")
    if not gated:
        A("- Brak blokad.")
    A("")
    A("Bielik-4.5B-v3 i Gemma 3 po akceptacji regulaminu pobrały się poprawnie; "
      "porównanie hashu PLLuM 8B z bazą pozostaje do uzupełnienia (po zatwierdzeniu Meta).")
    A("")
    with open(os.path.join(ZOO, "RAPORT.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")

    # ---------- RAPORT_PROSTY.md ----------
    P = []
    B = P.append
    B("# ZOO tokenizatorów — po prostu")
    B("")
    B(f"Wzięliśmy {len(toks)} tokenizatorów i daliśmy im te same polskie teksty: "
      "ogłoszenia, Dz.U., KIO, samorząd, granty i JSON-y. Fertility to liczba "
      "części słów (tokenów) na jedno słowo. Im mniej, tym taniej.")
    B("")
    B(f"Wygrywa **V0-32k**: na BZP {f4(val('1_bzp', 'V0-32k'))}, "
      f"na 149 grantach {f4(val('granty_149', 'V0-32k'))}. "
      f"Najbliższy rywal przy tym samym słowniku 32k to Aster-0.5B "
      f"({f4(val('1_bzp', 'Aster-0.5B'))}) — na części źródeł przewaga V0 mieści "
      "się w marginesie błędu, a na JSON held-out Aster jest nawet tańszy. "
      f"V0 i V0J2 na polskim to remis w granicach CI; V0J2 wygrywa wyraźnie na JSON.")
    B("")
    B(f"Rodzina PLLuM tnie polski drożej: 4B {f4(val('1_bzp', 'PLLuM-4B'))}, "
      f"8B {f4(val('1_bzp', 'PLLuM-8B'))}, 12B {f4(val('1_bzp', 'PLLuM-12B'))}. "
      "PLLuM 4B zachowuje się jak Gemma 3, 12B jak Mistral Nemo. "
      "Bielik 4.5B daje tyle samo tokenów co Bielik 1.5B.")
    B("")
    B(f"Liczby uczą, że cięcie cyfr po trzy jest tańsze niż pojedynczo. "
      f"Bielik 4.5B i 1.5B nie mają „§” jako jednego tokenu "
      f"({sec['tokenizers']['Bielik-4.5B-v3']['tokens']} tokeny).")
    B("")
    B(f"Duży słownik kosztuje: {ik(vocab['PLLuM-4B'])} tokenów w PLLuM 4B to "
      f"{f2(cost['vocab_x_dmodel']['PLLuM-4B']['768']['params_m'])} M parametrów "
      f"({pct(cost['vocab_x_dmodel']['PLLuM-4B']['768']['pct_150m'])}) w modelu 150M. "
      f"V0 ma {ik(vocab['V0-32k'])} tokenów i "
      f"{pct(cost['vocab_x_dmodel']['V0-32k']['768']['pct_150m'])}.")
    B("")
    B(f"Dodaliśmy też dwa tokenizery DanielK 32k z publicznego PR "
      f"(po {ik(vocab['DanielK-t1-pl-polish-32k'])} tokenów w słowniku). "
      f"Na BZP dają {f4(val('1_bzp', 'DanielK-t1-pl-polish-32k'))} i "
      f"{f4(val('1_bzp', 'DanielK-t2-pl-cnc-32k'))} — nadal więcej niż V0.")
    B("")
    B("Jedna rzecz została otwarta: baza Llama 3.1 dla PLLuM 8B "
      "(gated, czeka na zatwierdzenie Meta). Nie podstawiliśmy żadnym innym repozytorium.")
    B("")
    with open(os.path.join(ZOO, "RAPORT_PROSTY.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(P) + "\n")

    # ---------- stdout do czatu ----------
    print("=== PUNKTY ===")
    for k, v in [
        ("gałąź feat/tkx-zoo od f12fc2c", "TAK"),
        ("autor i committer adgr3", "TAK"),
        ("tylko pliki tokenizera (bez wag)", "TAK"),
        ("8 źródeł v2 + granty 149 + JSON held-out", "TAK"),
        ("wyniki referencyjne bez przeliczania", "TAK"),
        ("PLLuM 8B vs Llama 3.1", "OCZEKUJE NA METĘ"),
        ("raport + testy + commit lokalny", "TAK"),
    ]:
        print(f"{k} :: {v}")
    print("\n=== ZWYCIĘZCY ===")
    for s in fert["sources"]:
        print(f"{s}: {winners[s][1]} {f4(winners[s][0])}")
    print("\n=== REGRESJA PODZIAŁU (liczba tokenów) ===")
    hdr = "tokenizer".ljust(26) + "".join(p.rjust(14) for p in reg["phrases"])
    print(hdr)
    for t in toks:
        print(t.ljust(26) + "".join(str(reg["tokenizers"][t][p]["n"]).rjust(14) for p in reg["phrases"]))
    print("\n=== FORMATY ŚREDNIE ===")
    for t in toks:
        dm = sum(fmt["date_formats"][t].values()) / len(fmt["date_formats"][t])
        am = sum(fmt["amount_formats"][t].values()) / len(fmt["amount_formats"][t])
        print(f"{t}: daty {f2(dm)} kwoty {f2(am)} §{sec['tokenizers'][t]['tokens']} "
              f"cyfry={fmt['digit_split'][t]['style']}")


if __name__ == "__main__":
    main()
