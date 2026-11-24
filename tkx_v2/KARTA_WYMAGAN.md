# Karta wymagań TOKENIZATOREX v2.0 — tokenizer pod polski model ≤ 150M (polszczyzna urzędowa)

Wersja: 23.11.2026. Powiązane: project-hub #566 (model 150M), #576 (dziennik), TKX-A, TKX-C.

Zasada: nie ma najlepszego tokenizera — jest najlepszy do zadania i rozmiaru modelu. Fertility to warunek konieczny, nie dowód jakości. Ostateczny wybór w TKX-D.

## Macierz zgodności O1–O9 (z danych)

Wartości z `results/*.json` i pomiarów opisanych w raportach. PASS/FAIL nie są zgadywane.

| Wymaganie | V0-32k | V3-32k | Slayer1B-1.08 | Dowód |
|---|---:|---:|---:|---|
| O1 Round-trip `decode(encode(x))==x` | PASS (0/700) | FAIL (4/700: 3 BZP + 1 KIO, NFD) | PASS (0/700) | `results/tkx_v2_roundtrip.json` |
| O2 Brak NFD w słowniku i na wyjściu (100%) | FAIL (zachowuje NFD na wyjściu) | PASS (normalizuje do NFC) | FAIL (zachowuje NFD na wyjściu) | `results/tkx_v2_roundtrip.json` + `tests/test_tkx_v2_r2.py` |
| O3 Znak `§` jako pojedynczy token | PASS (1 token) | FAIL (2 tokeny) | PASS (1 token) | `results/tkx_v2_special_chars.json` |
| O4 Lata 2015–2035 (≤ 2 tokeny/rok w formatach) | UNKNOWN | UNKNOWN | UNKNOWN | nie zmierzono w tym raporcie |
| O5 Kwoty (≤ 6 tokenów/kwota, spójnie) | FAIL (4/15 kwot > 6) | FAIL (2/15) | FAIL (6/15) | `results/tkx_v2_patterns.json` (kategoria kwoty) |
| O6 Daty (≤ 5 tokenów/data) | FAIL (6/15 dat > 5) | FAIL (15/15) | FAIL (15/15) | `results/tkx_v2_patterns.json` (kategoria daty_iso) |
| O7 CPV (≤ 3 tokeny/kod) | FAIL (15/15 kodów > 3) | FAIL (15/15) | FAIL (15/15) | `results/tkx_v2_patterns.json` (kategoria cpv) |
| O8 Martwe tokeny ≤ 5% | FAIL (8,12%) | FAIL (7,83%) | FAIL (35,03%) | `results/tkx_v2_dead_tokens.json` |
| O9 Przeciek 13-gram ≤ 20% | FAIL (max 100.0% dok.) | FAIL (max 100.0% dok.) | UNKNOWN (inny korpus) | `results/tkx_v2_r6_leak.json` (korpus treningowy tokenizera) |

Uwaga: żaden z ocenianych wariantów (V0, V3, Slayer) nie spełnia O5–O8. Progi O5–O8 okazały się nierealne dla wszystkich tokenizerów (także Slayera) → do rewizji w v2.1 z uzasadnieniem, a nie po cichu.

Uwaga O1/O2: wymagania O1 (dokładny round-trip) i O2 (wyjście w NFC) wykluczają się dla wejścia w NFD. Propozycja v2.1: korpus normalizowany do NFC przed tokenizacją (krok preprocessingu), a wymaganie dla tokenizera = dokładny round-trip na wejściu NFC. Wtedy O1 i O2 przestają się gryźć.

## Wymagania (skrót)

- O1: round-trip `decode(encode(x)) == x` 100%.
- O2: brak NFD w słowniku i na wyjściu; 100% dokumentów.
- O3: znak `§` jako pojedynczy token w słowniku i kodowaniu (nie cały wzorzec `§ 362(a)`).
- O4: lata 2015–2035 ≤ 2 tokeny/rok.
- O5–O7: progi tokenów dla kwot/daty/CPV — do rewizji w v2.1.
- O8: martwe tokeny ≤ 5% słownika.
- O9: przeciek 13-gram ≤ 20% dokumentów.

## Bezpieczniki
- Angielski: brak regresji > 5% względem V0-32k (procentowy próg; wartość bazowa do pomiaru w TKX-D).
- JSON narzędzi: nie gorszy niż Slayer (metryka do doprecyzowania: fertility na korpusie vs suma wzorców).

## Definicja gotowe
- `pytest -q` zielone.
- `python scripts/sprawdz_liczby_v2.py` exit 0 na wszystkich raportach (v2 i v21).
- `python scripts/generuj_raporty_v2.py --check` nie zmienia plików.
- Liczby w raportach z `results/*.json` (v2 i v21).
