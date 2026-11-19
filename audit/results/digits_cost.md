# Koszt „każda cyfra osobno” (szacunek)

Dolna granica: metoda Codex A7 (`sum(max(0, cyfry_w_tokenie − 1))`).
Górna granica: każda cyfra osobno + niecyfrowa reszta jako jeden token (Grok).

| dziedzina | udział cyfr w znakach | dolna [% tokenów] | górna [% tokenów] |
|---|---:|---:|---:|
| przetargi_ogloszenia | 4.06% | +5.63% | +17.10% |
| przetargi_kio | 2.41% | +4.51% | +10.52% |
| samorzad_uchwaly | 7.62% | +12.42% | +25.83% |
| granty_ogloszenia | 5.07% | +9.46% | +16.05% |
| prawo_eli | 3.97% | +6.86% | +15.38% |
| ocr_prasa | 1.93% | +2.12% | +4.62% |
| tabele_json | 7.27% | +7.73% | +19.03% |
| web | 0.84% | +1.95% | +3.45% |
| wikipedia | 2.36% | +4.26% | +6.95% |
| literatura | 0.09% | +0.12% | +0.24% |
| prawo | 4.52% | +7.55% | +16.51% |
| sejm | 0.87% | +2.07% | +4.10% |
| nauka | 2.51% | +3.44% | +6.33% |
| dyskusje | 2.50% | +5.42% | +8.44% |
| angielski | 1.57% | +1.97% | +3.75% |

Razem 7 dziedzin urzędowych: dolna +6.68%, górna +15.04% tokenów.

Pełne ogłoszenie (Grok, bez cięcia 20k): mediana 3984 → 4646 tokenów (+16.6%); w 4096 mieści się 53.3% dziś i 33.3% po rozbiciu cyfr.

To jest szacunek, nie tokenizer po retreningu; prawdziwy koszt zmierzy TKX-C.
Liczby różnią się między źródłami, bo Codex liczy na tekście przyciętym do 20 tys.
znaków, a Grok odbudował pełne dokumenty; metody dolna/górna też są różne.
