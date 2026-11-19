# Spójność podziału w kontekstach (test)

Udział (string, kontekst), gdzie segmentacja zapisu różni się od najczęstszej dla tego stringu. Mniej = lepiej.

| kategoria | stringów | TOKENIZATOREX | HF | Slayer1B | Pollock |
|---|---:|---:|---:|---:|---:|
| kwota | 150 | 31.4% | 31.4% | 6.3% | 4.0% |
| data_slowna | 150 | 32.2% | 32.0% | 23.6% | 23.6% |
| data_cyfrowa | 150 | 18.3% | 18.7% | 0.0% | 0.0% |
| rok | 71 | 23.7% | 20.1% | 12.1% | 0.0% |
| rok_z_r | 81 | 26.8% | 26.5% | 39.9% | 28.6% |
| godzina | 150 | 18.3% | 18.3% | 0.0% | 0.0% |
| przepis | 150 | 27.0% | 26.5% | 0.0% | 0.0% |
| publikator | 3 | 42.9% | 42.9% | 28.6% | 28.6% |
| poz | 150 | 57.1% | 57.1% | 42.9% | 0.0% |
| cpv | 150 | 21.7% | 21.6% | 5.1% | 7.1% |
| znak_sprawy | 150 | 27.6% | 27.5% | 7.4% | 5.1% |
| sygnatura_kio | 29 | 42.9% | 42.9% | 0.0% | 42.9% |
| sygnatura_sadu | 1 | 14.3% | 14.3% | 0.0% | 0.0% |
| uchwala | 150 | 23.6% | 23.6% | 0.0% | 0.0% |
| procent | 150 | 28.9% | 28.9% | 24.6% | 29.0% |
| kod_pocztowy | 150 | 12.8% | 12.8% | 0.0% | 0.0% |
| email | 150 | 35.9% | 35.9% | 28.6% | 26.0% |
| url | 150 | 12.6% | 12.1% | 14.3% | 9.0% |
| nip | 20 | 46.4% | 43.6% | 0.0% | 42.9% |

## Skróty urzędowe

| skrót | TOKENIZATOREX | HF | Slayer1B | przykłady różnych podziałów |
|---|---:|---:|---:|---|
| `art.` | 0.0% | 0.0% | 0.0% |  |
| `lit.` | 42.9% | 42.9% | 0.0% | lit·. /  li·t. /  li·t. |
| `Dz.U.` | 42.9% | 42.9% | 0.0% | Dz·.·U. /  Dz.·U. /  Dz.·U. |
| `M.P.` | 0.0% | 0.0% | 0.0% |  |
| `poz.` | 42.9% | 42.9% | 42.9% | po·z. /  poz. /  poz. |

## Werdykt

* H3: POTWIERDZONA (skróty z ≥5%: lit., Dz.U., poz.)
* H4: POTWIERDZONA (kategorie z ≥5%: kwota, data_slowna, data_cyfrowa, rok, rok_z_r, godzina, przepis, publikator, poz, cpv, znak_sprawy, sygnatura_kio, sygnatura_sadu, uchwala, procent, kod_pocztowy, email, url, nip)
