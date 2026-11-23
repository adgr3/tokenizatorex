# RAPORT TEST DOMENOWY — TOKENIZATOREX v2.0

Data: 23.11.2026 · Liczby z `results/tkx_v2_*.json`.

## 1. Korpus

Źródła: BZP (500 dok.), Dz.U. 2026 ELI (12 dok.), KIO (66 dok.), samorząd (240 dok.),
granty (12 dok.), JSON narzędzi (200 dok.), kontrola ogólna HPLT (421 dok.).
Łącznie ~1 010 000 słów w test split.

## 2. Fertility (tokeny/słowo) — top 5 per źródło

| Źródło | #1 | #2 | #3 |
|---|---|---|---|
| BZP | V0-32k 1,430 | V3-32k 1,553 | V2b-32k 1,623 |
| Dz.U. | V0-32k 1,463 | APT3 1,533 | V3-32k 1,543 |
| KIO | V0-32k 1,398 | V3-32k 1,424 | V2b-32k 1,482 |
| samorząd | V0-32k 1,550 | V3-32k 1,618 | V3-24k 1,702 |
| granty | V0-32k 1,746 | V2b-32k 1,845 | V3-32k 1,853 |
| JSON | V0-32k 3,738 | GPT-4o 3,754 | APT3 3,811 |
| ogólny | V0-32k 1,412 | V3-32k 1,435 | V2b-32k 1,443 |

Wniosek: V0-32k (oryginalny SuperBPE) ma najniższą fertility na wszystkich źródłach.
V3-32k traci ~8-12% na tekstach urzędowych przez wymuszone tokeny cyfr, ale zyskuje spójność cyfr.

## 3. Znaki specjalne

V3-32k nie ma „§” jako pojedynczego tokena (encode → 2 bajty). V0-32k i Slayer mają.
Liczba znaków z listy 30+ jako pojedynczy token: V0-32k 21, V3-32k 20, GPT-4o 36.

## 4. Martwe tokeny

V0-32k: 8,47%, V3-32k: 8,15%, Slayer: 35,28%.

## 5. Wzorce

155 przykładów w 12 kategoriach. Segmentacja spójna (liczba tokenów identyczna) dla wszystkich wariantów.

## 6. Kandydat

Hipoteza: V3-32k jako kandydat do potwierdzenia w TKX-D (cyfry), przy zachowaniu V0-32k
jako punktu odniesienia dla kompresji.
PY