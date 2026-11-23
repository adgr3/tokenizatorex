# Znane wady TOKENIZATOREX (v2.0)

Każda wada z dowodem i propozycją naprawy (v2.1). Liczby z `results/tkx_v2_*.json`.

## W1. Znak „§” rozbity w wariancie V3-32k

- **Dowód:** `results/tkx_v2_special_chars.json` — V3-32k nie ma „§” jako pojedynczego tokena; V0/V1/V2 mają.
- **Przyczyna (diagnoza):** wymuszone tokeny 000–999 i 00–99 (V3) wypchnęły rzadkie znaki ze słownika przy limicie 32k; częstość „§” w próbce treningowej HPLT była niska.
- **Naprawa (v2.1):** dopisać „§” (i inne znaki specjalne) na końcu listy scaleń (metoda Herold i in.: nie pogarsza istniejącej tokenizacji) albo zarezerwować sloty specjalne.

## W2. Skróty prawne (Dz. U., Pzp, tj.)

- **Dowód:** `results/tkx_v2_patterns.json` — segmentacja `Dz. U.` to 3 kawałki, `Pzp` → `P|z|p`, `tj.` rozbijane.
- **Naprawa:** dopisać skróty na końcu scaleń; rozważyć trening tokenizera na mieszance 10–30% tekstów urzędowych.

## W3. JSON wywołań narzędzi

- **Dowód:** fertility na `tc1_json_tools` — TOKENIZATOREX droższy niż Slayer v6 (31 vs 29 tokenów na przykład).
- **Naprawa:** tokeny dla `<tool_call>`, kluczy JSON; test domenowy TKX-D na BPB.

## W4. Angielski

- **Dowód:** TKX-A — fertility 1,97 vs Slayer 1,30 na angielskim.
- **Status:** akceptowany kompromis (tokenizer pod polski); bezpiecznik: brak regresji > 5%.

## W5. Artefakty SuperBPE

- Niektóre superwordy zaczynają się w środku słowa (np. `nku węgla`); częste słowa mogą stracić własny token (`Wyda|je`).
- **Naprawa:** audyt słownika (już w TKX-A), ewentualne filtrowanie merge'y w v2.1.

## W6. Martwe tokeny

Uwaga: Slayer ma słownik polsko-angielski, więc na polskim korpusie część jego słownika z natury jest nieużywana.
To nie jest bezpośredni porównanie jakości słowników.

- **Dowód:** `results/tkx_v2_dead_tokens.json`.
- **Naprawa:** próg ≤ 5% słownika; w razie przekroczenia — przyciąć/ponownie wytrenować.

## Czego nie sprawdzają testy

- Jakość modelu downstream (wymaga TKX-D na małych modelach).
- Morfologia (otwarte pytanie, dowody sprzeczne).
- Dostępność APT4 z Bielika v3 (gated) — jeśli brak, UNKNOWN.
PY