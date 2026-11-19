# Użycie słownika (test)

| tokenizer | słownik | użyte typy | martwe | <5 użyć | Rényi H/ln(V) (Zouhar) | exp(H)/V | top-1000 share | Zipf slope |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| TOKENIZATOREX | 32,000 | 31,429 | 571 (1.8%) | 2,756 (8.6%) | 0.5273 | 0.00742 | 52.0% | -1.32 |
| TOKENIZATOREX-HF | 32,000 | 31,416 | 584 (1.8%) | 2,753 (8.6%) | 0.5271 | 0.00740 | 51.9% | -1.32 |
| TOKENIZATOREX-base | 32,000 | 31,298 | 702 (2.2%) | 3,699 (11.6%) | 0.4451 | 0.00316 | 63.3% | -1.38 |
| Slayer1B | 32,768 | 29,861 | 2,907 (8.9%) | 5,525 (16.9%) | 0.4309 | 0.00269 | 62.4% | -1.53 |
| APT3-1B | 31,980 | 31,137 | 843 (2.6%) | 2,682 (8.4%) | 0.5306 | 0.00768 | 57.1% | -1.34 |
| Pollock-2.0 | 49,152 | 44,556 | 4,596 (9.4%) | 8,178 (16.6%) | 0.4021 | 0.00157 | 59.8% | -1.34 |
| Bielik-v3 | 32,128 | 19,782 | 12,346 (38.4%) | 8,476 (26.4%) | 0.4762 | 0.00436 | 90.3% | -2.00 |
| PLLuM-12B | 131,072 | 35,977 | 95,095 (72.6%) | 19,644 (15.0%) | 0.4378 | 0.00133 | 75.5% | -1.90 |
| GPT-4o | 200,019 | 42,223 | 157,796 (78.9%) | 23,722 (11.9%) | 0.4306 | 0.00096 | 72.5% | -1.84 |

Rényi: α = 2,5, częstości z korpusu testowego; podane **obie** formy:
`H_α / ln|V|` (Zouhar i in. 2023) oraz `exp(H_α)/|V|` (forma audytu).
Tokeny specjalne nie są liczone (brak użyć). Rényi jest miarą opisową;
Cognetta i in. (2024) pokazują, że nie przewiduje jakości modelu.
