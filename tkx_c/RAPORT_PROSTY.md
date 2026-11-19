# TOKENIZATOREX — raport prosty po TKX-C

Data: 19.11.2026 · Szczegóły: `tkx_c/RAPORT_TKX_C.md`

## Co poprawiliśmy

1. **Każda cyfra jest osobnym kawałkiem.** `2024` to teraz `2│0│2│4`, a nie
   `202│4`. Dzięki temu **każdy rok 2015–2035 kosztuje tyle samo** (8 kawałków
   w zdaniu `w roku RRRR r. zadanie`). Wcześniej rok 2024 kosztował 5, a 2030
   już 6 — i każdy nowy rok był „inny”.
2. **NFC w potoku.** Tekst z PDF, który ma „rozłożone” polskie znaki (`ą` jako
   `a` + ogonek), jest teraz normalizowany do NFC **przed** kodowaniem. Dzięki
   temu NFD nie zwiększa liczby tokenów: **+0,0%** (wcześniej +45%).
3. **Jeden kanoniczny enkoder.** Tokenizerem modelu jest eksport HF
   (`hf/variants/.../tokenizer.json`), a nie enkoder Python. Sprawdziliśmy:
   `decode(encode(tekst))` daje z powrotem ten sam tekst na **2752/2752**
   dokumentach testu. Eksport HF i Python zgadzają się w **99,975%**
   (wcześniej 97,08%). Zamrożone 1240 zdań (`tkx_c/golden/`) pilnuje, żeby
   przyszła zmiana kodu nie zmieniła tokenizacji po cichu.

## Ile to kosztuje

Pojedyncze cyfry **wydłużają** tekst. Na 7 dziedzinach urzędowych: **+14,0%**
tokenów (95% CI +13,1%…+15,1%). Najdroższe: uchwały +22,5%, tabele JSON +18,9%,
przetargi +16,8%; najtańsze: literatura +0,03%, web +3,0%, OCR +4,0%.
To mieści się w górnej części przedziału, który przewidział audyt
(+6,7%…+15,0%). Prawdziwy koszt po treningu to ten zmierzony, nie szacunek.

**Zysk:** stały kalendarz, zero tokenów wielocyfrowych, data/CPV dzielone
identycznie w każdym kontekście (spójność 17–24% → 0%), NFD 0%, HF prawie 1:1.
**Cena:** dokumenty z datami/kwotami są o kilkanaście procent dłuższe, więc
w oknie 2048/4096 mieści się ich mniej.

## Co zyskaliśmy w spójności

Ten sam zapis przestaje się dzielić różnie zależnie od otoczenia:

| zapis | przed (V0) | po (V1/V2) |
|---|---:|---:|
| data cyfrowa | 17,1% innych podziałów | **0%** |
| CPV | 23,9% | **0%** |
| przepis | 28,0% | 14,9% |
| kwota | 35,6% | 27,1% |
| znak sprawy | 24,7% | 13,0% |

Nie wszystko jest idealne, ale kierunek jest wyraźny.

## Warianty słownika 16k / 24k / 32k

Zbudowaliśmy 8 wariantów:

| wariant | co to |
|---|---|
| V0-32k | nowa baza **przed** poprawkami (p2, nie kopia v1) |
| V1-32k | same pojedyncze cyfry |
| V2-32k | cyfry + NFC |
| V2-24k / V2-16k | to samo, mniejszy słownik |
| V2-base-32k/24k/16k | bez etapu SuperBPE (kontrola) |

**Nie wybraliśmy jeszcze słownika.** Fertility zawsze faworyzuje większy
słownik (V2-16k 2,168 vs V2-32k 1,920), więc wybór zrobimy w TKX-D na małych
modelach: **BPB** na tych samych bajtach + sonda dat/kwot/CPV/skrótów.
32k zabiera 16,4% parametrów modelu 150M na embeddingi, 16k — 8,2%; to trzeba
wliczyć w budżet.

## Kontekst modelu

Pełne dokumenty (bez cięcia 20 tys. znaków), mediana tokenów:

| dokument | V0 | V2-32k | V2-16k |
|---|---:|---:|---:|
| ogłoszenie przetargowe | 3883 | 4536 | 5306 |
| KIO | 1350 | 1485 | 1682 |
| grant NIW | 10 776 | 11 471 | 13 072 |
| uchwała (PDF) | 2602 | 2858 | 3167 |

W 2048 mieści się 10% ogłoszeń (V0) i 5% po poprawkach; w 4096 — 55% i 30%.
**2048 nie wystarcza na typowe ogłoszenie; 4096 też nie po rozbiciu cyfr.**
To decyzja o oknie i dzieleniu w planie modelu, nie o tokenizerze.

## Ważne zastrzeżenie

**V0 nie jest kopią v1 z audytu.** Mieliśmy za mało wolnej pamięci, żeby
odtworzyć oryginalną próbkę p0 (1,5 GB parquet + shuffle), więc **wszystkie**
warianty, łącznie z V0, wytrenowaliśmy na tej samej próbce p2 (400 MB).
V0 ma 89,3% wspólnego słownika z v1 i fertility 1,6842 vs 1,6825 na
urzędowych — to nowa baza, nie regresja. Powód jest zapisany w protokole
i raporcie.

## Co dalej (TKX-D)

1. Małe modele ~30M na tych samych bajtach, dla V0/V2-16k/V2-24k/V2-32k
   i Slayera.
2. BPB na walidacji + sonda dat/kwot/CPV/skrótów.
3. Wybór tokenizera i słownika **na podstawie BPB**, nie fertility.
4. Wzór: `TokenizerTest-32m-A/B` (BPB 1,0583 vs 1,0622); checkpointy
   Slayer1B 1.09 ładowane w fp32 (bez bf16 na T4/P100).
   Szczegóły: `tkx_c/TKX_D_PLAN.md`.

## Słowniczek

* **Token/kawałek** — najmniejsza jednostka tekstu dla modelu.
* **Fertility** — tokeny na słowo; mniej = krócej, ale **nie** znaczy lepiej
  dla modelu.
* **BPB** — bity na bajt; miara jakości modelu na tych samych bajtach,
  porównywalna między tokenizerami.
* **NFC/NFD** — dwa zapisy polskich liter w Unicode; NFD rozkłada `ą` na
  `a` + ogonek, NFC trzyma `ą` jako jeden znak.
* **Kanoniczny HF** — plik `tokenizer.json`, którego używa trening i ocena
  modelu; to on jest „prawdą”, nie enkoder Python.
* **Golden sequences** — zamrożone ID dla 1240 zdań; jeśli przyszła zmiana
  kodu je zmieni, test CI failuje.
* **Superword** — token obejmujący kilka słów, np. ` w związku z`.
* **Embedding** — macierz zamieniająca token na wektor; jej rozmiar zależy
  od słownika.

## Jedno zdanie

Poprawki **działają** (stały kalendarz, NFD 0%, HF 1:1, spójność zapisów),
ale kosztują **+14% tokenów na urzędowych** — dlatego wybór 16k/24k/32k
odkładamy do TKX-D, gdzie sprawdzimy BPB, a nie fertility.
