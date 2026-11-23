# RAPORT TEST DOMENOWY — TOKENIZATOREX v2.0

Data: 23.11.2026. Liczby z `results/tkx_v2_*.json` (generowane skryptem).

## 1. Korpus

Źródła i rozmiary z `results/tkx_v2_fertility.json`:

| Źródło | Dokumenty | Słowa | Bajty |
|---|---:|---:|---:|
| BZP (ogłoszenia) | 500 | 1421000 | 11359609 |
| Dz.U. 2026 ELI | 12 | 25324 | 178865 |
| KIO | 66 | 93179 | 721697 |
| Samorząd (uchwały) | 240 | 69521 | 458906 |
| Granty | 12 | 26102 | 219137 |
| JSON narzędzi (tc1) | 200 | 25645 | 254699 |
| Kontrola ogólna (HPLT web) | 421 | 155005 | 1139692 |
| JSON BZP (tabele, extra) | 18 | 15095 | 148703 |

Uwaga: Dz.U. i granty mają po 12 dokumentów — ranking fertility na tych źródłach jest niepewny (mała próba).

## 2. Fertility (tokeny/słowo) z 95% CI

### BZP (ogłoszenia) (n=500 dok.)

| Tokenizer | Fertility | 95% CI | Bajty/token |
|---|---:|---:|---:|
| TKX/V0-32k | 1,430 | [1,422, 1,439] | 5,589 |
| TKX/V3-32k | 1,553 | [1,541, 1,565] | 5,149 |
| Slayer1B-1.08 | 1,810 | [1,800, 1,821] | 4,418 |

### Dz.U. 2026 ELI (n=12 dok.)

| Tokenizer | Fertility | 95% CI | Bajty/token |
|---|---:|---:|---:|
| TKX/V0-32k | 1,463 | [1,364, 1,581] | 4,826 |
| TKX/V3-32k | 1,543 | [1,436, 1,674] | 4,577 |
| Slayer1B-1.08 | 1,771 | [1,683, 1,884] | 3,988 |

### KIO (n=66 dok.)

| Tokenizer | Fertility | 95% CI | Bajty/token |
|---|---:|---:|---:|
| TKX/V0-32k | 1,398 | [1,374, 1,425] | 5,539 |
| TKX/V3-32k | 1,424 | [1,399, 1,452] | 5,437 |
| Slayer1B-1.08 | 1,715 | [1,686, 1,749] | 4,515 |

### Samorząd (uchwały) (n=240 dok.)

| Tokenizer | Fertility | 95% CI | Bajty/token |
|---|---:|---:|---:|
| TKX/V0-32k | 1,550 | [1,538, 1,561] | 4,258 |
| TKX/V3-32k | 1,618 | [1,605, 1,630] | 4,079 |
| Slayer1B-1.08 | 1,980 | [1,965, 1,993] | 3,334 |

### Granty (n=12 dok.)

| Tokenizer | Fertility | 95% CI | Bajty/token |
|---|---:|---:|---:|
| TKX/V0-32k | 1,746 | [1,674, 1,812] | 4,810 |
| TKX/V3-32k | 1,853 | [1,754, 1,948] | 4,530 |
| Slayer1B-1.08 | 2,029 | [1,960, 2,098] | 4,138 |

### JSON narzędzi (tc1) (n=200 dok.)

| Tokenizer | Fertility | 95% CI | Bajty/token |
|---|---:|---:|---:|
| TKX/V0-32k | 3,738 | [3,624, 3,824] | 2,657 |
| TKX/V3-32k | 3,841 | [3,721, 3,933] | 2,586 |
| Slayer1B-1.08 | 3,985 | [3,881, 4,069] | 2,492 |

### Kontrola ogólna (HPLT web) (n=421 dok.)

| Tokenizer | Fertility | 95% CI | Bajty/token |
|---|---:|---:|---:|
| TKX/V0-32k | 1,412 | [1,394, 1,430] | 5,208 |
| TKX/V3-32k | 1,435 | [1,418, 1,453] | 5,123 |
| Slayer1B-1.08 | 1,672 | [1,656, 1,690] | 4,396 |

### JSON BZP (tabele, extra) (n=18 dok.)

| Tokenizer | Fertility | 95% CI | Bajty/token |
|---|---:|---:|---:|
| TKX/V0-32k | 2,736 | [2,561, 2,905] | 3,601 |
| TKX/V3-32k | 2,964 | [2,760, 3,157] | 3,323 |
| Slayer1B-1.08 | 3,179 | [2,983, 3,375] | 3,098 |

Wniosek z danych: V0-32k ma najniższą fertility na wszystkich 8 źródłach (punktowo). CI rozdzielają V0 od V3 wyraźnie tylko na części źródeł; na Dz.U. i grantach (n=12) ranking jest niepewny.

## 3. Znaki specjalne

Lista znaków (n=39), z pliku `results/tkx_v2_special_chars.json`: `§`, `„`, `”`, `–`, `—`, `…`, `€`, `×`, `°`, `²`, `½`, `№`, `ó`, `ą`, `ę`, `ś`, `ć`, `ń`, `ź`, `ż`, `ł`, `µ`, `©`, `®`, `™`, `•`, `·`, `«`, `»`, `−`, `≥`, `≤`, `≠`, `≈`, `√`, `∞`, `∑`, `∏`, `∫`

| Tokenizer | Liczba znaków jako 1 token | `§` jako 1 token |
|---|---:|---:|
| TKX/V0-32k | 21 | TAK |
| TKX/V3-32k | 20 | NIE |
| Slayer1B-1.08 | 26 | TAK |

V3-32k nie ma `§` jako jednego tokena (encode daje 2 tokeny). V0-32k i Slayer mają `§` jako 1 token.

## 4. Martwe tokeny

| Tokenizer | Vocab | Martwe | % |
|---|---:|---:|---:|
| TKX/V0-32k | 32000 | 2599 | 8,12% |
| TKX/V3-32k | 32000 | 2505 | 7,83% |
| Slayer1B-1.08 | 32768 | 11477 | 35,03% |

Uwaga: porównanie ze Slayerem nie jest bezpośrednie — Slayer ma słownik polsko-angielski; na polskim korpusie część słownika z natury jest nieużywana. W audycie szerszym martwe tokeny Slayera to 8,90%.

## 5. Wzorce i segmentacja

Wzorce: 155 w 12 kategoriach (`tkx_v2/wzorce.json`).
Segmentacja mierzona przez `encoding.offsets` (liczba kontekstów z identyczną segmentacją, sklejenia z poprzedzającym znakiem, segmentacja tekstowa) — zapis w `results/tkx_v2_patterns.json`.

- TKX/V0-32k: identyczna segmentacja w 5/5 kontekstach dla 6/155 wzorców; wzorce ze sklejeniem z poprzedzającym znakiem: 148/155.
- TKX/V3-32k: identyczna segmentacja w 5/5 kontekstach dla 5/155 wzorców; wzorce ze sklejeniem z poprzedzającym znakiem: 150/155.
- Slayer1B-1.08: identyczna segmentacja w 5/5 kontekstach dla 0/155 wzorców; wzorce ze sklejeniem z poprzedzającym znakiem: 155/155.

## 6. Kandydat

Domyślny wariant v2.0: **V0-32k** (najniższa fertility na wszystkich 8 źródłach, `§` jako 1 token, round-trip NFC/NFD bez zmian w próbce syntetycznej).
V3-32k: wariant eksperymentalny z cięciem cyfr; wygrywa na identyfikatorach/kodach/sygnaturach, przegrywa na datach i kwotach; nie ma `§` jako jednego tokena; normalizuje NFD→NFC (4 błędy round-trip w próbie).
Ostateczny wybór dopiero po TKX-D (małe modele, BPB, ≥ 3 seedy). Fertility to warunek konieczny, nie dowód jakości.

