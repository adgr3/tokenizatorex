# Znane wady TOKENIZATOREX (v2.0)

Każda wada z dowodem i propozycją naprawy (v2.1). Liczby z `results/*.json`.

## W1. Znak `§` rozbity w wariancie V3-32k

- **Dowód:** `results/tkx_v2_special_chars.json` — V3-32k nie ma `§` jako pojedynczego tokena (`encode` daje 2 tokeny); V0-32k ma 1 token.
- **Przyczyna (hipoteza):** wymuszone tokeny cyfr i ograniczony budżet słownika mogły wypchnąć rzadkie znaki; do potwierdzenia na danych treningowych V3.
- **Naprawa (v2.1):** dopisać `§` na końcu scaleń albo zarezerwować slot specjalny.

## W2. Skróty prawne (Dz. U., Pzp, tj.)

- **Dowód:** `results/tkx_v2_patterns.json` — segmentacja tekstowa pokazuje rozbicia (np. `Dz. U.` jest rozbijane; `Pzp` rozbijane w części wariantów).
- **Naprawa:** dopisać skróty na końcu scaleń; rozważyć trening na mieszance 10–30% tekstów urzędowych.

## W3. JSON wywołań narzędzi

- **Dowód:** na `tc1_json_tools` (200 dok., 25645 słów) V0-32k ma fertility 3,738 vs Slayer 3,985 (`results/tkx_v2_fertility.json`), czyli V0 tańszy na tym korpusie; łącznie 95852 vs 102191 tokenów. Osobno 10 wzorców JSON z `tkx_v2/wzorce.json`: suma tokenów standalone Slayer 298 vs V0 321 (`results/tkx_v2_patterns.json` po kategoriach). To różne miary — nie mieszać.
- **Naprawa:** tokeny dla `<tool_call>` i kluczy JSON; ocena na BPB w TKX-D.

## W4. Angielski

- **Dowód:** TKX-A — fertility 1,97 vs Slayer 1,30 na angielskim (znany kompromis).
- **Status:** akceptowany kompromis; bezpiecznik: brak regresji > 5%.

## W5. Artefakty SuperBPE — ujawnienie
- TOKENIZATOREX to **SuperBPE**: część tokenów (superwordy) łączy kawałki sąsiednich słów. To obniża fertility, ale czasem tnie słowo w nienaturalnym miejscu.
- Superwordy w słowniku: **V0-32k 4982** (**15,57%** słownika), **V0J2-32k 4817** (**15,05%**). Zaczyna się w środku słowa: **V0 362** (**7,27%** superwordów), **V0J2 343** (**7,12%**); użycie superwordów: **V0 8,06%** tokenów, **V0J2 7,97%**; w tym od środka słowa: **V0 0,28%**, **V0J2 0,27%** (audyt H6 przeliczony na bieżących wariantach, `results/tkx_v2_r6_superwords.json`).
- Red team A: w 172 tekstach urzędowych granice od środka słowa wystąpiły w **13/172** (V0) i **12/172** (V0J2); w 384 parach słów **38/384** i **34/384**; w fuzzingu 20000 napisów **5** przypadków.
- Przykłady (V0/V0J2): `zgodność z` → `z | god | ność z`; `kolejność z` → `ko | lej | ność z`; `informacja z` → `informa | cja z`.
- **Plan v2.1:** superwordy tylko od początku słowa + pomiar kosztu (fertility/latencja).
- **Naprawa krótkoterminowa:** audyt słownika i filtrowanie merge (w toku).

## W6. Martwe tokeny

Uwaga: porównanie ze Slayerem nie jest bezpośrednie (słownik polsko-angielski). Na polskim korpusie 35,03% martwych; w audycie szerszym 8,90%.
- **Dowód:** V0-32k 8,12%, V3-32k 7,83%, Slayer 35,03% (`results/tkx_v2_dead_tokens.json`).

## W7. Tokeny specjalne w tekście użytkownika
- **Domyślne zachowanie biblioteki `tokenizers`:** literalny `<|endoftext|>` w tekście użytkownika staje się ID specjalnym **31999**, także przy `add_special_tokens=False`; domyślny `decode` może go pominąć.
- **Tryb zalecany:** `tokenizer.encode_special_tokens = True` (wersja `tokenizers` z lock) rozbija taki napis na zwykłe tokeny; w `transformers` odpowiada temu `split_special_tokens: true` w `tokenizer_config.json` (dodane do `hf/tokenizatorex-32k`, `hf/variants/V0-32k`, `hf/variants/V0J2-32k`).
- `<tool_call>` i `</tool_call>` w V0J2 to **zwykłe tokeny słownika, nie ID specjalne**; nadal mogą wstrzyknąć tekst szablonu, więc szablon czatu nie może traktować tekstu użytkownika jak szablonu.
- **Pomiar:** w tekstach pomiarowych (1469 dok.) nazwy dodane jako `special=True` występują **0** razy; `<tool_call>`/`</tool_call>` występują 320 razy, ale tryb zalecany nie zmienia ich tokenizacji, więc fertility się nie zmienia (`results/tkx_v2_r6_special_tokens.json`).
- **Przed treningiem modelu Ogonek z szablonem czatu to musi być włączone.**

## W8. Przeciek do korpusu treningowego (miara słowna)
- **Miara:** 13-gramy słowne (NFC, lowercase, `split()`, 13 kolejnych słów) vs korpus treningowy tokenizera; próg > 50% unikalnych gramów lub dokładny duplikat. Data korpusu: **2026-07-14** (`added` w HPLT p2).
- **Wynik:** żadne źródło nie przekracza progu 5% dokumentów > 50%. Najwyżej BZP **17/500** (3,4%) i web **8/421** (1,9%); exact **0** wszędzie.
- **Kalibracja na tekście na pewno nowym:** 789 dokumentów z datą > 2026-07-14 ma **17** (2,15%) > 50%, exact 0. BZP: publikacja 2026-11-01–2026-11-02, wszystkie 500/500 po dacie korpusu; 17/500 to wspólny szablon, nie kopie.
- **Uczciwie:** wspólne szablony urzędowe ≠ kopie dokumentów. Miara znakowa z R6 myliła, bo 13 znaków ≈ 2 słowa: granty 149 miały w niej 138/149 > 50%, mimo 122/149 dokumentów po dacie korpusu. Źródło: `results/tkx_v2_r6c_slowny_przeciek.json`; wynik znakowy: `results/tkx_v2_r6_leak.json`.

## Czego nie sprawdzają testy
- Jakość modelu downstream (wymaga TKX-D).
- Morfologia (otwarte pytanie).
- APT4/Bielik-1.5B-v3: tokenizer jest w wynikach fertility; nie wykonano testów downstream.
