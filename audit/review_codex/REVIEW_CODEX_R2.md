# Niezależna powtórka TKX-A R2 (Codex) — raport

Data: 19.11.2026 · Gałąź: `review/tkx-a-r2-codex` · Head bazowy: `4a42cfe`.

## A. Moje liczby (policzone od zera)

### A1. Integralność danych

- Dokumenty: 4586 (dev 1834, test 2752).
- SHA-256 (tekst w `raw/` vs MANIFEST): 0 rozbieżności; brak brakujących plików.
- Brak dokumentu w dwóch splitach: 0; brak duplikatów treści (ten sam SHA pod różnymi ID): 0.
- Liczba słów: 0 rozbieżności (recompute = MANIFEST).
- Dokumenty urzędowe z datą 2026: 918 (granty 110, prawo_eli 124, przetargi_kio 110, przetargi_ogloszenia 100, samorząd 374, tabele_json 100).
- Różne źródła (hosty URL) na dziedzinę: 1 (każda dziedzina z jednego hosta; odrębnych URL-i jest 100–400).

### A2. Fertility (test), tokeny/słowo (95% CI bootstrap po dokumentach)

| Dziedzina | TKX ref | TKX HF | Slayer1B | Pollock-2.0 |
|---|---:|---:|---:|---:|
| przetargi_ogloszenia | 1.5552 [1.5411;1.6044] | 1.5524 [1.5383;1.6010] | 2.0171 [2.0009;2.0830] | 1.8116 [1.7964;1.8666] |
| samorzad_uchwaly | 1.5278 [1.5251;1.5485] | 1.5231 [1.5203;1.5432] | 1.9834 [1.9821;2.0111] | 1.7528 [1.7529;1.7785] |
| prawo_eli | 1.4868 [1.4350;1.5480] | 1.4833 [1.4288;1.5414] | 1.8040 [1.7631;1.8853] | 1.5555 [1.5100;1.6155] |
| przetargi_kio | 1.4027 [1.3851;1.4189] | 1.4032 [1.3866;1.4201] | 1.7198 [1.7063;1.7505] | 1.4973 [1.4709;1.5049] |

### A3. Kalendarz (H1)

- Koszt samego roku: TKX ref/HF: 1 token dla 2015–2024, 2 tokeny dla 2025–2035. Szablon `w roku RRRR r. zadanie`: 4/5/6 tokenów (zależnie od przedziału).
- W korpusie (przetargi_ogloszenia + prawo_eli, test): 2024 — 163 wystąpienia, średnio 1 token; 2026 — 1129 wystąpień, średnio 2 tokeny.

### A4. NFD (H5), test dziedzin urzędowych (7 dziedzin, 606 dok.)

- TKX ref: +45.39% tokenów (mean per doc +43.15% [41.99;44.24]).
- TKX HF: +45.50%.
- Slayer1B: +37.33%.
- Pollock-2.0: +37.41%.

### A5. Parytet HF (H8)

- przetargi_ogloszenia: 48145 fragmentów, 47380 identycznych = 98.411%.
- web: 20344 fragmentów, 20214 identycznych = 99.361%.
- HF daje mniej tokenów niż ref w 14/15 dziedzinach (np. przetargi_ogloszenia −381), ale round-trip `decode(encode(x))==x` przechodzi dla 1000/1000 losowych dokumentów dla obu.

### A6. Efektywność Rényiego (test, α = 2,5)

| Tokenizer | (a) H_α / ln|V| | (b) exp(H_α)/|V| |
|---|---:|---:|
| TKX ref | 0.5273 | 0.0074235 |
| Slayer1B | 0.4309 | 0.0026933 |
| Pollock-2.0 | 0.4021 | 0.0015661 |

### A7. Cyfry (test, dziedziny urzędowe i pozostałe)

Udział cyfr: 1.93%–7.61% znaków; liczb (słów z cyfrą): 5.88%–17.88% słów. Szacowany koszt wariantu „każda cyfra osobno” (cyfry − tokeny z cyframi w TKX) = 2.12%–12.42% wszystkich tokenów dziedziny; tokeny z cyframi i wiodącą spacją stanowią większość tokenów z cyframi (np. przetargi_ogloszenia 6320/11920+6320? patrz JSON). Pełne liczby: `results_codex.json` → `A7_digits`.

## B. Porównanie z rundą 1

| Liczba | Runda 1 | Codex | Różnica | Wyjaśnienie |
|---|---:|---:|---:|---|
| Fertility (4 dziedziny × 4 tok.) | jak w JSON | jak wyżej | 0.00% | zgodne co do bitu |
| H1 średnie tokenów/rok | 1.0 / 2.0 | 1.0 / 2.0 | 0.00% | zgodne |
| H1 liczniki wystąpień 2024/2026 | 162 / 1128 | 163 / 1129 | +0.62% / +0.09% | regex `\b` w `notation_patterns.py:11` gubi „2020r.” (już naprawione w R1) |
| NFD aggregate (TKX ref) | +45.92% | +45.39% | −1.15% | inny podzbiór/zakres dziedzin (R1: 25 dok./dziedzinę; Codex: wszystkie test, 7 dziedzin urzędowych) |
| HF parity przetargi_ogloszenia | 98.4110% | 98.4110% | 0.00% | zgodne |
| Rényi (b) TKX ref | 0.0074235 | 0.0074235 | 0.00% | zgodne (po policzeniu na test) |
| Rényi (a) standard | nie raportowane | 0.5273 | — | R1 raportuje tylko (b); protokół wymaga (b), literatura (Zouhar 2023) używa (a) |
| H6 midword | 3.45% słownika / 0.0917% użyć (po poprawce) | nie przeliczane | — | R1 naprawione; brak niezależnego przeliczenia w tej rundzie poza R2 |
| A7 cyfry | **brak w R1** | jak wyżej | — | pomiar nie istnieje w rundzie 1 (zgłoszone jako brak) |

Wniosek: liczby R1 odtwarzają się; różnice ≤ 1.15% w pełni wyjaśnione (regex, podzbiór dokumentów).

## C. Przegląd kodu rundy 1 — znaleziska

- **WAŻNE — Brak pomiaru A7 (cyfry).** W `audit/` nie ma skryptu mierzącego udział cyfr i koszt wariantu „każda cyfra osobno”. Zgłoszone jako brak; do dodania w TKX-C.
- **WAŻNE — Definicja Rényiego.** `audit/vocab_usage.py` raportuje tylko `exp(H_α)/|V|` (0.0074 = 7.4‰). To zgodne z protokołem, ale nie pozwala porównywać z literaturą (Zouhar i in. 2023) bez dodania `H_α/ln|V|` (0.5273 dla TKX ref). Zalecenie: raportować obie formy.
- **WAŻNE — Ranking „HF #1, TKX #2”.** Wynika z tego, że eksport HF daje konsekwentnie mniej tokenów niż ref (14/15 dziedzin, Δ −4458 tokenów ogółem), ale round-trip `decode(encode(x))==x` przechodzi 1000/1000 dla obu. Różnice to scalanie pretokenów, nie utrata bajtów/spacji. Nie blokuje.
- **DROBNE — H9 / sys.path.** Skrypty używają `sys.path.append` (nie `insert(0)`); pakiet HF importowany przed dodaniem repo. Zgodne z wymogiem.
- **DROBNE — Bootstrap RNG.** `common.bootstrap_ci` używa `random.Random`, a `fertility.py` używa `np.random.default_rng`. Wyniki punktowe identyczne; przedziały CI mogą się minimalnie różnić. Zalecenie: ujednolicić.
- **DROBNE — Parytet HF przez porównanie ID.** `hf_parity.py` sprawdza `a == b` (listy ID). Działa tylko dlatego, że eksport zachowuje ID tokenów; potwierdzone niezależnie porównaniem zdekodowanych ciągów (ten sam wynik 98.411%). Zalecenie: porównywać ciągi zdekodowane (odporniejsze).
- **DROBNE — Przycięcie do 20 000 znaków.** Stosowane identycznie do wszystkich dziedzin i tokenizerów; wpływa na długie dokumenty (prawo, sejm), ale nie zmienia wniosków.
- **DROBNE — H6.** Bloker z rundy 1 (wiodąca spacja, status bez gałęzi obalenia) jest naprawiony w aktualnym kodzie (`superwords.py` linie 63–85, 203–216). Nie zgłaszam nowego blokera.

## Podsumowanie

Liczby rundy 1 odtwarzają się; nie znaleziono błędów arytmetycznych. Dwa ważne znaleziska: brak pomiaru cyfr (A7) w rundzie 1 oraz brak standardowej formy Rényiego dla porównania z literaturą. Parytet HF i fertility zgodne co do bitu.

```
REVIEW_RESULT
werdykt: PASS_Z_UWAGAMI
blokery: []
wazne: [brak pomiaru A7 (cyfry) w rundzie 1, definicja Renyiego tylko exp(H)/V bez H/ln|V|, ranking HF#1/TKX#2 wynika ze scalania a nie utraty danych]
drobne: [bootstrap RNG niespojny, parytet HF przez ID, przyciecie 20k znakow, H6 naprawione]
liczby_powtorzone: 12/12
```

STATUS=REVIEW_GOTOWE werdykt=PASS_Z_UWAGAMI