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

## W5. Artefakty SuperBPE
- Niektóre superwordy mogą zaczynać się w środku słowa; częste słowa mogą stracić własny token.
- **Naprawa:** audyt słownika, filtrowanie merge w v2.1.

## W6. Martwe tokeny

Uwaga: porównanie ze Slayerem nie jest bezpośrednie (słownik polsko-angielski). Na polskim korpusie 35,03% martwych; w audycie szerszym 8,90%.
- **Dowód:** V0-32k 8,12%, V3-32k 7,83%, Slayer 35,03% (`results/tkx_v2_dead_tokens.json`).

## Czego nie sprawdzają testy
- Jakość modelu downstream (wymaga TKX-D).
- Morfologia (otwarte pytanie).
- APT4/Bielik-1.5B-v3: tokenizer jest w wynikach fertility; nie wykonano testów downstream.
