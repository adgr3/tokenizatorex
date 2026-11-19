# Odporność na zniekształcenia (test)

Wzrost liczby tokenów względem czystego tekstu (średnia po dziedzinach urzędowych; 95% CI w JSON).

| wariant | TOKENIZATOREX | HF | Slayer1B | APT3 | Pollock | GPT-4o |
|---|---:|---:|---:|---:|---:|---:|
| bez_pl | +16.8% | +16.8% | +12.8% | +15.8% | +18.1% | +0.9% |
| caps | +106.8% | +107.0% | +101.4% | +104.5% | +81.4% | +45.6% |
| title | +30.6% | +30.6% | +21.2% | +20.9% | +21.8% | +12.5% |
| typo_2 | +1.4% | +1.4% | +1.0% | +1.2% | +1.2% | +0.4% |
| typo_5 | +3.7% | +3.7% | +2.5% | +3.0% | +3.2% | +0.9% |
| ocr_2 | +0.9% | +0.9% | +0.7% | +0.8% | +0.9% | +0.3% |
| ocr_5 | +2.3% | +2.3% | +1.7% | +2.0% | +2.2% | +0.6% |
| nfd | +45.9% | +46.0% | +37.8% | +0.0% | +38.1% | +18.0% |
| mixed_en | +19.3% | +19.3% | +7.8% | +17.1% | +15.2% | +5.9% |
| emoji | +5.7% | +5.7% | +4.2% | +2.7% | +7.4% | +1.9% |

## Werdykt H5

* Warianty > 25%: caps, title, nfd
* H5: POTWIERDZONA
* TOKENIZATOREX traci względnie więcej niż:
  * bez_pl vs Slayer1B: +3.9% pkt proc.
  * bez_pl vs APT3-1B: +1.0% pkt proc.
  * bez_pl vs Bielik-v3: +18.7% pkt proc.
  * bez_pl vs PLLuM-12B: +15.0% pkt proc.
  * bez_pl vs TOKENIZATOREX-base: +3.5% pkt proc.
  * caps vs Slayer1B: +5.4% pkt proc.
