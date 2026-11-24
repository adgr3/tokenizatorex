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
- BZP 500 (spec1): `<TKX_DANE>/spec1/test.jsonl` (poza repo).
- JSON narzędzi 200 (tc1): `<TKX_DANE>/tc1/test.jsonl` (poza repo).

## Przeciek
13-gramy **słowne** (NFC, lowercase, split()) vs faktyczny korpus treningowy tokenizera (`audit/tmp/stability_train.txt`, HPLT p2, 400 MB; SHA-256 zgodny z manifestem; data korpusu 2026-07-14). Próg: > 50% 13-gramów słownych lub dokładny duplikat. Najwyższy odsetek dokumentów > 50%: 3.4% (1_bzp). Tło na 789 dokumentach po dacie korpusu: 2.15% > 50%, exact 0. Szczegóły: `results/tkx_v2_r6c_slowny_przeciek.json`.

## Licencje / status
Dokumenty urzędowe są publiczne. HPLT/FineWeb-2: ODC-By; Wikipedia: CC BY-SA.
