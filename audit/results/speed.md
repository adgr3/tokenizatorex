# Szybkość kodowania (1 wątek, mediana z 3 powtórzeń)

CPU: Intel64 Family 6 Model 158 Stepping 10, GenuineIntel · 12 rdzeni · Python 3.12.10 · tekst 1.00 MB

| tokenizer | tokeny | s (mediana) | tokeny/s | MB/s |
|---|---:|---:|---:|---:|
| TOKENIZATOREX | 193,168 | 1.10 | 176,114 | 0.91 |
| TOKENIZATOREX-HF | 193,140 | 0.34 | 574,823 | 2.98 |
| TOKENIZATOREX-base | 215,651 | 0.91 | 237,129 | 1.10 |
| Slayer1B | 228,325 | 0.61 | 376,727 | 1.65 |
| APT3-1B | 212,439 | 0.48 | 446,468 | 2.10 |
| Pollock-2.0 | 214,990 | 0.60 | 358,370 | 1.67 |
| Bielik-v3 | 392,489 | 0.71 | 549,193 | 1.40 |
| PLLuM-12B | 305,991 | 0.67 | 457,270 | 1.50 |
| GPT-4o | 297,989 | 0.10 | 3,029,369 | 10.18 |
