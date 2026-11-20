# TOKENIZATOREX — raport prosty po TKX-C

Data: 19.11.2026 · Aktualizacja: 20.11.2026 (V2b, V3) · Szczegóły: `tkx_c/RAPORT_TKX_C.md`

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
4. **Dwa nowe sposoby cięcia liczb (na prośbę właściciela, 20.11).** V2b dokleja
   spację przed liczbą do pierwszej cyfry, więc słowo „roku” ma już tylko jedną
   wersję. V3 dodatkowo tnie liczby na trójki od prawej i ma w słowniku **wszystkie**
   trójki `000`–`999` — żaden rok ani kod nie jest „obcy”. Oba warianty są
   zbudowane dla 16k/24k/32k i przeszły te same testy co V2.

## Skąd część kosztu pojedynczych cyfr

Są dwie proste przyczyny, dla których samo „rozbicie cyfr” kosztuje więcej
kawałków, niż się spodziewaliśmy (`·` oznacza spację):

1. **Spacja przykleja się do poprzedniego słowa.** Gdy po słowie „roku” stoi
   liczba, powstaje kawałek `·roku·` (ze spacją na końcu). Gdy nie stoi — jest
   zwykłe `·roku`. Czyli to samo słowo w dwóch wersjach, co marnuje miejsce
   w słowniku. V2b temu zapobiega: spacja idzie do cyfry (`·2`) i `·roku·`
   nie powstaje.
2. **Spacje w kwotach są osobnymi kawałkami.** W V2 kwota `1 234 567` to
   `1|·|2|3|4|·|5|6|7` — same cyfry i spacje. Całość z groszami i `zł` rośnie
   z 7 kawałków (V0) do 13 (V2). W przykładzie z decyzji było to 9 → 14;
   u nas wychodzi 7 → 13, bo V0 wytrenowaliśmy na innej próbce. Kierunek jest
   ten sam. V2b daje 11 kawałków, a V3 tylko 6.

| wariant | `w roku 2024 r.` | `1 234 567,89 zł` (liczba kawałków) |
|---|---|---:|
| V0 | `w\|·roku\|·202\|4·r.` (4) | 7 |
| V2 | `w\|·roku·\|2\|0\|2\|4\|·r.` (6) | 13 |
| V2b | `w\|·roku\|·2\|0\|2\|4\|·r.` (6) | 11 |
| V3 | `w\|·roku\|·2\|024\|·r.` (5) | **6** |

Widzisz to w tabeli: V3 usuwa obie przyczyny naraz, V2b tylko pierwszą.

## Ile to kosztuje

Pojedyncze cyfry **wydłużają** tekst. Na 7 dziedzinach urzędowych V2 kosztuje
**+14,0%** tokenów (95% CI +13,1%…+15,1%). Najdroższe: uchwały +22,5%, tabele
JSON +18,9%, przetargi +16,8%; najtańsze: literatura +0,03%, web +3,0%,
OCR +4,0%. To mieści się w górnej części przedziału z audytu (+6,7%…+15,0%).

Nowe warianty są tańsze: **V2b +11,1%**, a **V3 +5,3%** względem V0
(na tych samych dokumentach, z przedziałem niepewności). V3 ma w słowniku
4,9% kawałków, których tekst nie używa — to cena za to, że każda trójka cyfr
jest gotowa.

**Zysk we wszystkich trzech wariantach jest ten sam:** kalendarz się nie zmienia
(co roku tyle samo kawałków), NFD 0%, data i CPV zawsze dzielone tak samo,
`decode(encode(x))` zawsze daje oryginał. Różnica jest tylko w cenie.

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
| **V2b-32k/24k/16k** | spacja do pierwszej cyfry, NFC (nowe, 20.11) |
| **V3-32k/24k/16k** | trójki cyfr od prawej + pełny zestaw `000`–`999` (nowe) |

**Nie wybraliśmy jeszcze słownika ani sposobu cięcia liczb.** Fertility zawsze
faworyzuje większy słownik, więc wybór zrobimy w TKX-D na małych modelach:
**BPB** na tych samych bajtach + sonda dat/kwot/CPV/skrótów + koszt w tokenach.
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

1. Małe modele ~30M na tych samych bajtach: V0, V2-16k/24k/32k, V2b, V3
   (najlepszy rozmiar) i tokenizer Slayera; wzór: `TokenizerTest-32m-A/B`.
2. BPB na walidacji + sonda dat/kwot/CPV/skrótów; checkpointy Slayer1B 1.09
   jako punkt odniesienia BPB na tych samych tekstach.
3. Wybór tokenizera, słownika i sposobu cięcia liczb **na podstawie BPB**,
   nie fertility.
4. Liczymy na **wynajętej karcie RTX 5090** (bf16). Agent przygotuje dane i kod
   na zwykłym procesorze i przygotuje dla właściciela kartkę do wynajmu;
   właściciel wynajmuje i daje SSH. Budżet **co najwyżej 5 dolarów**, przy
   4 dolarach stop i pytanie. Każdy wydatek zapisujemy w `results/koszt.jsonl`.
   Na koniec: sumy SHA-256 wyników i „GOTOWE, można kliknąć Destroy” —
   przycisk klika właściciel. Zapas: Kaggle (karta w laptopie się zawiesza).
5. Zwycięski wariant na koniec przetrenujemy na **pełnych danych p0** na Kaggle
   (procesor, ok. 30 GB pamięci). Szczegóły: `tkx_c/TKX_D_PLAN.md`.

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
