# Wykresy i animacje TOKENIZATOREX v2.0

Wszystkie pliki generuje `scripts/wykresy.py` z `results/*.json` i tokenizerów w repo.
Uruchomienie: `python scripts/wykresy.py` (lub `--szybko` dla mniejszych rozmiarów).

## Statyczne (PNG + SVG)

1. `fertility_bzp.png/.svg` — tokeny na słowo na BZP dla tokenizerów z TKX-ZOO + v2, poziomo, posortowane, z CI i rozmiarem słownika.
2. `skad_przewaga.png/.svg` — base-32k → V0 na 8 źródłach, obok APT3 i Slayer.
3. `osiem_zrodel.png/.svg` — small multiples dla 8 źródeł (V0, base-32k, APT3, Slayer, GPT-4o).
4. `koszt_slownika.png/.svg` — % parametrów modelu 150M zajmowany przez embeddingi (32k/128k/200k/262k).
5. `daty_kwoty_paragraf.png/.svg` — średnia liczba tokenów na daty, kwoty i paragrafy.
6. `json_heldout.png/.svg` — JSON: V0 vs V0J2 (tc1 −23%, nowe narzędzia −33%).
7. `znane_wady.png` — ilustracja znanej wady SuperBPE (0,28% użyć, 13/172 tekstów).

## Animacje (GIF)

- `anim/tokenizacja_porownanie.gif` — jedno zdanie urzędowe tokenizowane przez V0 i GPT-4o.
- `anim/fertility_wyscig.gif` — słupki fertility rosną i układają się w kolejności.
- `anim/superbpe_sklejanie.gif` — jak SuperBPE skleja słowa (zgodność z → z | god | ność z).

Źródło danych: `results/tkx_zoo_fertility.json`, `results/tkx_v2_fertility.json`,
`results/tkx_zoo_formats.json`, `results/tkx_zoo_vocab_cost.json`, `results/tkx_v21_test.json`,
`results/tkx_v2_r6_superwords.json`; commit d91a87e.