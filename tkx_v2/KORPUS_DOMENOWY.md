# Korpus testu domenowego TOKENIZATOREX v2.0

Pełne teksty poza repo (zasada: bez surowych tekstów w git). W repo: manifest, metryki, ten opis.

## Źródła (zgodne z `results/tkx_v2_fertility.json`)

| # | Domena | Źródło | Dokumenty | Słowa | Bajty |
|---:|---|---|---:|---:|---:|
| 1_bzp | BZP (ogłoszenia) | patrz manifest/metryki | 500 | 1421000 | 11359609 |
| 2_du_eli | Dz.U. 2026 ELI | patrz manifest/metryki | 12 | 25324 | 178865 |
| 3_kio | KIO | patrz manifest/metryki | 66 | 93179 | 721697 |
| 4_samorzad | Samorząd (uchwały) | patrz manifest/metryki | 240 | 69521 | 458906 |
| 5_granty | Granty | patrz manifest/metryki | 12 | 26102 | 219137 |
| 6_json_narzedzia | JSON narzędzi (tc1) | patrz manifest/metryki | 200 | 25645 | 254699 |
| 7_ogolny | Kontrola ogólna (HPLT web) | patrz manifest/metryki | 421 | 155005 | 1139692 |
| json_bzp_tabele | JSON BZP (tabele, extra) | patrz manifest/metryki | 18 | 15095 | 148703 |

## Zestawy dodatkowe opisane w tkx_v2/MANIFEST.json
- BZP 500 (spec1): `D:\VPSabryka\spec1\data	est.jsonl` (poza repo).
- JSON narzędzi 200 (tc1): `D:\VPSabryka	c1\dane	est.jsonl` (poza repo).

## Znane wyjątki jakości danych
- 4/500 dokumentów BZP (spec1) nie jest w NFC. Zapisane jako znany wyjątek O1/O2; korpus testowy nie został znormalizowany przed pomiarem w tym wydaniu (wymagałoby przeliczenia). Do potwierdzenia/naprawy przed kolejnym pomiarem.

## Przeciek
13-gramy vs próbka treningowa HPLT 400 MB — nie wykonano. Próg stopu: > 20% dokumentów z trafieniem.

## Licencje / status
Dokumenty urzędowe są publiczne. HPLT/FineWeb-2: ODC-By; Wikipedia: CC BY-SA.
