# RAPORT RUNDY 1 — pomiary TOKENIZATOREX (TKX-A)

Data: 19.11.2026 · Repo: `adgr3/tokenizatorex`, gałąź `audyt/tkx-a-19-11`,
baza `faf06223806809a79f2df0bd64efbd4c57e2d98e`. Wszystkie liczby pochodzą
z plików `audit/results/*.json` wygenerowanych skryptami z tego repo.
Protokół: `audit/PROTOKOL.md` (zamrożony przed pomiarami; korekty implementacji
w sekcji „Zmiany po fakcie”). Korpus: `audit/data/MANIFEST.json`.

## 1. Streszczenie

1. **Na polszczyźnie urzędowej 2026 TOKENIZATOREX jest najlepszy lub praktycznie
   remisuje.** Na 7 nowych dziedzinach nie przegrywa istotnie z żadnym polskim
   tokenizerem; jedyne nieistotne wyprzedzenie to Pollock na `granty` (1,781 vs
   1,791 tokenu/słowo, CI różnicy zawiera zero).
2. **Na 15 dziedzinach jest najlepszy na 11** (razem z eksportem HF); istotnie
   przegrywa w Wikipedii (Pollock, −1,25%), nauce (APT3, −2,95%) i angielskim
   (GPT-4o 1,68× taniej; to dziedzina poza celem tokenizera).
3. **H1 potwierdzona:** lata 2015–2024 to 1 token, 2025–2026 to 2 tokeny.
   Zdanie-kontrolne `w roku RRRR r. zadanie` ma 4 tokeny dla 2015–2024 i 5 dla
   2025–2026. Nowy rok będzie „nowym” tokenem, bez wspólnych kawałków ze starym.
4. **H2 częściowo potwierdzona:** koszt na cyfrę jest w przybliżeniu stały
   (~0,6 tokenu/cyfrę), ale segmentacja kodów jest niestabilna kontekstowo:
   CPV 21,7%, znak sprawy 27,6%, uchwała 23,6%, NIP 46,4% przypadków inaczej.
5. **H3 potwierdzona:** `lit.`, `Dz.U.`, `poz.` mają różne podziały w 42,9%
   kontekstów; `art.` i `M.P.` w tej matrycy są stabilne.
6. **H4 potwierdzona:** prawie każda kategoria zapisów (19/19) ma ≥5% przypadków
   z innym podziałem zależnie od kontekstu.
7. **H5 potwierdzona:** NFD +45,9%, CAPS +106,8%, tytuły +30,6% tokenów.
   TOKENIZATOREX traci względnie więcej niż Slayer1B (CAPS +5,4 pkt proc.,
   NFD +8,1 pkt proc.). APT3 nie cierpi na NFD, bo normalizuje wejście.
8. **H6 obalona w skali z rekonesansu:** po wyłączeniu tokenów zaczynających się
   spacją i użyciu słownika frekwencyjnego „od środka słowa” zaczyna się 3,5%
   superwordów (1,6–13,2% zależnie od definicji), a ich użycie to 0,04–0,59%
   tokenów — nie 19,4%. Artefakt istnieje (`nk`/`ne przez`), ale jest rzadszy.
9. **H7 częściowo:** 88,2% z top 1000 słów ma własny token (próg 90% nie
   osiągnięty); 2,83% wystąpień częstych słów jest rozbite z superwordem.
10. **H8 potwierdzona mocno:** eksport HF odtwarza 97,27% fragmentów (ID) na
    dziedzinach urzędowych i 99,36% na web (z = −31,0), ale **100% zdekodowanych
    ciągów jest identycznych** — to scalanie, nie utrata tekstu. Różnica tokenów
    sięga −0,52% (tabele) i +0,04% (KIO). Trening i ocena muszą używać tego
    samego enkodera.
11. **Słownik jest zdrowy, ale Rényi jest opisowy:** 1,8% tokenów martwych
    (Slayer 8,9%), natomiast Rényi w obu formach wygrywa APT3 (0,531 i 0,00768
    vs TKX 0,527 i 0,00742). Rényi nie przewiduje jakości modelu (Cognetta i in.
    2024); zdanie o „najmocniejszej przewadze” wycofane.
12. **Cyfry i pełne PDF:** rozbicie cyfr kosztuje +6,7–15,0% tokenów na
    dziedzinach urzędowych (+16,6% na pełnym ogłoszeniu); na pełnym PDF uchwał
    przewaga nad APT3 spada do 0,55% (HF 0,82%). Kontekst 2048 nie mieści
    mediany pełnego ogłoszenia (3984).
13. **Stabilność:** retrening na innym shardzie HPLT daje 89,3% wspólnego
    słownika, ale fertility różni się tylko −0,12%…+1,96%. Wydajność jest
    stabilna, dokładny słownik — nie.
14. **Szybkość:** referencyjny Python 176 tys. tok/s (0,91 MB/s), HF 575 tys.
    tok/s (2,98 MB/s). Referencja jest ~3,3× wolniejsza od eksportu.
15. **Morfologia:** MorphScore precision 0,023 (Slayer 0,082, Bielik 0,135);
    spójność rdzenia 93,3% (Slayer 92,6%). Zgodnie z literaturą to słaby
    predyktor jakości modelu — raportujemy, nie optymalizujemy.

## 2. Korpus (`test` = 60% dokumentów; raport liczy `test`)

| dziedzina | dok. | słów | dev/test | NFD | 2026 |
|---|---:|---:|---|---:|---:|
| `przetargi_ogloszenia` | 100 | 229 135 | 40/60 | 0 | 100% |
| `przetargi_kio` | 110 | 162 038 | 44/66 | 0 | 100% |
| `samorzad_uchwaly` | 400 | 118 752 | 160/240 | 1 | 94% |
| `granty_ogloszenia` | 110 | 167 931 | 44/66 | 0 | 100% |
| `prawo_eli` | 130 | 239 515 | 52/78 | 0 | 95% |
| `ocr_prasa` | 60 | 151 321 | 24/36 | 0 | 0% (przed 1940) |
| `tabele_json` | 100 | 91 215 | 40/60 | 0 | 100% |
| `web` | 701 | 272 772 | 280/421 | 0 | — |
| `wikipedia` | 402 | 260 372 | 161/241 | 0 | — |
| `literatura` | 384 | 285 346 | 154/230 | 0 | — |
| `prawo` (Dz.U.) | 211 | 287 932 | 84/127 | 0 | — |
| `sejm` | 1270 | 274 006 | 508/762 | 0 | — |
| `nauka` | 104 | 264 733 | 42/62 | 1 | — |
| `dyskusje` | 386 | 278 317 | 154/232 | 0 | — |
| `angielski` | 118 | 230 201 | 47/71 | 0 | — |

Razem 4 586 dokumentów i 3 313 586 słów (wszystkie splity). Wszystkie nowe
dziedziny urzędowe mają ≥100 dokumentów i ≥91 tys. słów; `ocr_prasa` 151 tys.
słów. Dokumenty przycięte do 20 tys. znaków; bez NFC.

## 3. Wyniki

### 3.1 Fertility (tokeny/słowo, `test`) — `results/fertility.json`

| dziedzina | TOKENIZATOREX [95% CI] | najlepszy | Slayer1B | Pollock | APT3 |
|---|---|---:|---:|---:|---:|
| przetargi_ogloszenia | 1,555 [1,528; 1,583] | HF 1,552 | 2,017 | 1,812 | 1,796 |
| przetargi_kio | **1,403** [1,383; 1,420] | TOKENIZATOREX | 1,720 | 1,497 | 1,584 |
| samorzad_uchwaly | 1,528 [1,517; 1,540] | HF 1,523 | 1,983 | 1,753 | 1,772 |
| granty_ogloszenia | 1,791 [1,712; 1,866] | Pollock 1,781 | 2,084 | 1,781 | 2,051 |
| prawo_eli | 1,487 [1,421; 1,563] | HF 1,483 | 1,804 | 1,555 | 1,587 |
| ocr_prasa | 1,916 [1,717; 2,148] | HF 1,915 | 2,078 | 1,942 | 1,976 |
| tabele_json | 2,629 [2,504; 2,755] | HF 2,616 | 3,048 | 2,711 | 2,805 |
| web | 1,416 [1,399; 1,433] | HF 1,415 | 1,672 | 1,577 | 1,557 |
| wikipedia | 1,785 [1,736; 1,855] | **Pollock 1,763** | 1,997 | **1,763** | 1,831 |
| literatura | 1,622 [1,590; 1,659] | HF 1,621 | 1,902 | 1,778 | 1,689 |
| prawo (Dz.U.) | 1,511 [1,482; 1,546] | HF 1,506 | 1,847 | 1,592 | 1,572 |
| sejm | 1,292 [1,283; 1,300] | HF 1,292 | 1,588 | 1,392 | 1,418 |
| nauka | 1,976 [1,904; 2,052] | **APT3 1,917** | 2,096 | 1,973 | **1,917** |
| dyskusje | 1,650 [1,615; 1,690] | HF 1,649 | 1,904 | 1,719 | 1,759 |
| angielski | 1,976 [1,956; 1,998] | **GPT-4o 1,179** | 1,294 | 1,762 | 1,815 |

**Istotne różnice (RID: CI parowany bez zera i ≥1%):**
* Wikipedia: Pollock −1,25% (CI różnicy [−0,0420; −0,0047] tok./słowo).
* Nauka: APT3 −2,95% ([−0,0962; −0,0244]).
* Angielski: wszystkie polskie i GPT-4o wyraźnie lepsze (GPT-4o −40,3%).
* **Żadna dziedzina urzędowa nie ma istotnej przegranej.** Granty: Pollock
  −0,58%, ale CI [−0,0401; +0,0228] zawiera zero → nieistotne.
* Eksport HF jest minimalnie lepszy od referencji (0,0–0,5%), ale to ta sama
  rodzina; różnica wynika z pretokenizacji (patrz 3.8).
* **Pełne PDF uchwał (niezależna runda 3):** HTML dziennika to zwykle pierwsza
  strona. Na pełnym PDF przewaga nad APT3 spada do **0,55%** (HF 0,82%) —
  poniżej progu 1%; APT3 jest przy tym stratny (round-trip 6/1010). Na 4 nowych
  źródłach (Dolny Śląsk, TED, SAOS, NCN) przewaga nad Pollockiem to **−6,11%**.
  Źródła: `results/full_pdf_uchwaly.json`, `results/new_sources_four.json`.

### 3.2 Zapisy urzędowe i liczby — `results/notations.json`

Średnia liczba tokenów na wystąpienie (bez kontekstu; mniej = lepiej):

| kategoria | wystąpień | TOKENIZATOREX | Slayer1B | Bielik-v3 | GPT-4o |
|---|---:|---:|---:|---:|---:|
| kwota | 2 175 | **3,87** | 5,23 | 11,42 | 5,47 |
| data słowna | 4 000 | **3,76** | 5,31 | 12,25 | 8,27 |
| data cyfrowa | 624 | **3,82** | 5,35 | 10,93 | 6,00 |
| rok | 4 000 | 1,75 | 1,69 | 5,00 | 2,00 |
| rok + `r.` | 4 000 | **2,01** | 3,62 | 7,00 | 4,00 |
| godzina | 2 541 | **2,22** | 3,00 | 5,42 | 3,00 |
| przepis (`art. … ust. …`) | 4 000 | **4,20** | 5,78 | 9,06 | 7,16 |
| publikator (`Dz.U.`/`M.P.`) | 2 426 | **3,00** | 4,00 | 5,00 | 3,96 |
| `poz.` | 4 000 | 4,27 | 4,92 | 6,33 | 4,41 |
| CPV | 596 | 5,36 | 5,63 | 11,00 | **5,00** |
| znak sprawy | 543 | 6,93 | 7,92 | 10,87 | 7,06 |
| sygnatura KIO | 41 | 6,56 | 6,37 | 9,90 | 6,90 |
| uchwała | 197 | 12,01 | 14,36 | 17,04 | **11,38** |
| procent | 695 | **2,24** | 2,39 | 4,34 | 2,35 |
| kod pocztowy | 363 | **3,01** | 3,69 | 7,00 | 3,00 |
| e-mail | 271 | 9,71 | 10,85 | 11,56 | **8,76** |
| URL | 397 | 22,10 | 24,53 | 27,04 | **19,48** |
| NIP | 29 | 9,41 | 9,10 | 14,10 | **8,10** |

**H1 — kalendarz.** W `przetargi_ogloszenia` + `prawo_eli`:

| rok | wystąpień | TOKENIZATOREX | Slayer1B | szablon `w roku RRRR r. zadanie` |
|---:|---:|---:|---:|---:|
| 2015–2023 | 32–128/rok | **1,00** | 1,00 | 4 |
| 2024 | 163 | **1,00** | 2,00 | 4 |
| 2025 | 460 | **2,00** | 2,00 | 5 |
| 2026 | 1 129 | **2,00** | 2,00 | 5 |

Early (2015–2024) vs late (2025–2026): TOKENIZATOREX 1,000 → 2,000 (2,00×),
HF 1,066 → 2,000, Slayer1B 1,157 → 2,000, Pollock 1,000 → 1,000, GPT-4o 2 → 2.
**H1 potwierdzona** dla TOKENIZATOREX (i Slayera w innej postaci). Skutek: nowe
lata nie dzielą kawałków ze starymi, a `2025`/`2026` są o 1 token droższe.

**H2 — długie liczby.** Korelacja długości liczby (4–13 cyfr) z liczbą tokenów:
0,989 (TOKENIZATOREX), 0,979 (Slayer), 0,967 (GPT-4o) — czyli tokenów rośnie
liniowo, ale koszt na cyfrę jest w przybliżeniu stały (~0,46–0,64). To nie
„rosnący koszt na cyfrę”, tylko **niestabilna segmentacja w kontekście**
(patrz 3.3): CPV 21,7%, znak sprawy 27,6%, uchwała 23,6%, NIP 46,4% innych
podziałów. **H2 częściowo potwierdzona** (chaos kontekstowy tak, rosnący koszt
na cyfrę nie).

### 3.2a Koszt „każda cyfra osobno” — `results/digits_cost.json`

Dolna granica (Codex A7) i górna (Grok) na teście, dokumenty przycięte do 20k:

| dziedzina | udział cyfr | dolna | górna |
|---|---:|---:|---:|
| przetargi_ogloszenia | 4,06% | +5,63% | +17,10% |
| przetargi_kio | 2,41% | +4,51% | +10,52% |
| samorzad_uchwaly | 7,62% | +12,42% | +25,83% |
| granty_ogloszenia | 5,07% | +9,46% | +16,05% |
| prawo_eli | 3,97% | +6,86% | +15,38% |
| ocr_prasa | 1,93% | +2,12% | +4,62% |
| tabele_json | 7,27% | +7,73% | +19,03% |
| web | 0,84% | +1,95% | +3,45% |
| **7 dziedzin urzędowych** | **4,36%** | **+6,68%** | **+15,04%** |

Na pełnym ogłoszeniu: mediana 3984 → 4646 tokenów (+16,6%), w 4096 mieści się
53,3% dziś i 33,3% po rozbiciu. To szacunek, nie tokenizer po retreningu;
prawdziwy koszt zmierzy TKX-C.

### 3.3 Spójność podziału — `results/consistency.json`

Udział par (string, kontekst) z podziałem innym niż najczęstszy dla tego stringu
(7 kontekstów: bare, start, środek, przed kropką, nawias, po spacji, bez spacji):

| kategoria | TOKENIZATOREX | HF | Slayer1B | Pollock |
|---|---:|---:|---:|---:|
| kwota | 31,4% | 31,4% | **6,3%** | 4,0% |
| data cyfrowa | 18,3% | 18,7% | **0,0%** | 0,0% |
| rok + `r.` | 26,8% | 26,5% | 39,9% | 28,6% |
| godzina | 18,3% | 18,3% | **0,0%** | 0,0% |
| przepis | 27,0% | 26,5% | **0,0%** | 0,0% |
| `poz.` | 57,1% | 57,1% | 42,9% | 0,0% |
| CPV | 21,7% | 21,6% | 5,1% | 7,1% |
| znak sprawy | 27,6% | 27,5% | 7,4% | 5,1% |
| uchwała | 23,6% | 23,6% | **0,0%** | 0,0% |
| kod pocztowy | 12,8% | 12,8% | **0,0%** | 0,0% |
| e-mail | 35,9% | 35,9% | 28,6% | 26,0% |

Skróty: `lit.` 42,9%, `Dz.U.` 42,9%, `poz.` 42,9%, `art.` 0%, `M.P.` 0%.
**H3 potwierdzona** (≥2 skróty ≥5%). **H4 potwierdzona** (19/19 kategorii ≥5%).
To jest **największa jakościowa słabość SuperBPE**: ten sam zapis jest dzielony
inaczej zależnie od kontekstu, podczas gdy Slayer1B w wielu kategoriach jest
w 100% stabilny. Przykład (TOKENIZATOREX): `Dz.U.` → `Dz│.│U.` (bare) vs
`│Dz.│U.` (po spacji); `2024 r.` → `202│4·r.` vs `202│4│·r│..`.

### 3.4 Odporność — `results/robustness.json`

Wzrost tokenów względem czystego tekstu, średnia po 7 dziedzinach urzędowych:

| wariant | TOKENIZATOREX | HF | Slayer1B | APT3 | Pollock | GPT-4o |
|---|---:|---:|---:|---:|---:|---:|
| bez polskich znaków | +16,8% | +16,8% | **+12,8%** | +15,8% | +18,1% | **+0,9%** |
| CAPS | +106,8% | +107,0% | +101,4% | +104,5% | +81,4% | **+45,6%** |
| Title Case | +30,6% | +30,6% | +21,2% | +20,9% | +21,8% | **+12,5%** |
| literówki 2% | +1,4% | +1,4% | +1,0% | +1,2% | +1,2% | +0,4% |
| literówki 5% | +3,7% | +3,7% | +2,5% | +3,0% | +3,2% | +0,9% |
| OCR 2% | +0,9% | +0,9% | +0,7% | +0,8% | +0,9% | +0,3% |
| OCR 5% | +2,3% | +2,3% | +1,7% | +2,0% | +2,2% | +0,6% |
| NFD | +45,9% | +46,0% | +37,8% | **+0,0%** | +38,1% | +18,0% |
| PL–EN mieszanka | +19,3% | +19,3% | **+7,8%** | +17,1% | +15,2% | +5,9% |
| emoji | +5,7% | +5,7% | +4,2% | +2,7% | +7,4% | +1,9% |

**H5 potwierdzona.** Progi >25% przekraczają CAPS, Title i NFD. TOKENIZATOREX
traci względnie więcej niż Slayer1B o 5,4 pkt proc. (CAPS), 8,1 pkt proc. (NFD),
9,4 pkt proc. (Title) i 4,0 pkt proc. (bez PL znaków). APT3 nie cierpi na NFD,
bo normalizuje wejście (NFKC), ale to jest stratne i nie jest rozwiązaniem dla
modelu wymagającego wiernego round-tripu.

### 3.5 Morfologia — `results/morphology.json`

MorphScore (publiczny kod `catherinearnett/morphscore`, commit `821fabf4`;
UD_Polish-PDB; 10 916 pozycji po filtrze; freq_scale=True, bez słów 1-tokenowych):

| tokenizer | precision | recall | micro F1 |
|---|---:|---:|---:|
| TOKENIZATOREX | 0,023 | 0,063 | 0,031 |
| Slayer1B | 0,082 | 0,225 | 0,094 |
| Bielik-v3 | **0,135** | **0,395** | **0,147** |
| PLLuM-12B | 0,105 | 0,298 | 0,129 |
| GPT-4o | 0,098 | 0,268 | 0,123 |

Spójność rdzenia (pierwszy token wspólny z formą podstawową, 600 lematów):
TOKENIZATOREX 93,3%, base 91,8%, Slayer 92,6%, Bielik 96,8%, Pollock 85,7%.
**Wniosek:** TOKENIZATOREX jest gorszy od bazowych modeli na granicach morfemów
(bo skleja całe słowa i frazy), ale powyżej base i Slayera w spójności rdzenia.
Zgodnie z literaturą (R² ≈ 0,02) nie przekładamy tego wprost na jakość modelu.

### 3.6 Artefakty SuperBPE — `results/superwords.json`, `results/dziwne_tokeny.md`

* 4 922 superwordy = 15,4% słownika; 6,9% użyć tokenów w korpusie.
* „Od środka słowa” (główne kryterium: token nie zaczyna się spacją, pierwszy
  segment nie jest formą z korpusu ≥5 razy): **170 tokenów = 3,5% superwordów**,
  użycie **0,092%**. Analiza wrażliwości: 1,6% (dowolna forma), 13,2% (top 2000).
  **H6 obalona** — skala 19,4% z rekonesansu nie potwierdza się; użycie <1%.
* Podejrzanych (niesensownych) 24 tokeny = 0,49% superwordów: `Skopiuj i wklej`,
  `owane przez`, `towany przez`, `mentuj obrazkiem`.
* Sensowne końcówki z `się`/`by`/`że`: 146 tokenów.
* Boilerplate: 30 tokenów, 0,012% użyć w naszym korpusie (mało, bo korpus
  urzędowy nie jest stroną WWW; w danych treningowych z sieci może być więcej).
* Rozbijanie top 2000: 23,3% wystąpień ma jakikolwiek podział, 2,83% z udziałem
  superwordu. **H7 nie potwierdzona wg progu ≥90%** (88,2% słów ma własny token),
  ale zjawisko istnieje i jest mierzalne (`Ofer│ta -`, `środowisk│owe lub`).
* 100 najdziwniejszych tokenów w `dziwne_tokeny.md` (kryterium: rzadkość,
  cyfry/interpunkcja, mieszana wielkość liter, superword).

### 3.7 Słownik — `results/vocab_usage.json`

| tokenizer | słownik | martwe | <5 użyć | Rényi H/ln(V) | exp(H)/V | top-1000 |
|---|---:|---:|---:|---:|---:|---:|
| TOKENIZATOREX | 32 000 | **1,8%** | 8,6% | 0,5273 | 0,00742 | 52,0% |
| TOKENIZATOREX-HF | 32 000 | **1,8%** | 8,6% | 0,5271 | 0,00740 | 51,9% |
| TOKENIZATOREX-base | 32 000 | 2,2% | 11,6% | 0,4451 | 0,00316 | 63,3% |
| Slayer1B | 32 768 | 8,9% | 16,9% | 0,4309 | 0,00269 | 62,4% |
| APT3-1B | 31 980 | 2,6% | 8,4% | **0,5306** | **0,00768** | 57,1% |
| Pollock-2.0 | 49 152 | 9,4% | 16,6% | 0,4021 | 0,00157 | 59,8% |
| Bielik-v3 | 32 128 | 38,4% | 26,4% | 0,4762 | 0,00436 | 90,3% |
| PLLuM-12B | 131 072 | 72,6% | 15,0% | 0,4378 | 0,00133 | 75,5% |
| GPT-4o | 200 019 | 78,9% | 11,9% | 0,4306 | 0,00096 | 72,5% |

**APT3 wygrywa obie formy Rényiego** (0,5306 i 0,00768 vs TKX 0,5273 i 0,00742).
1,8% martwych tokenów TKX zostaje faktem, ale Rényi jest miarą opisową i nie
przewiduje jakości modelu (Cognetta i in. 2024). Nie używać go do wyboru
wariantu TKX-C.

### 3.8 Parytet eksportu HF — `results/hf_parity.json`

| dziedzina | identyczne (ID) | identyczne (ciągi) | Δ tokenów (HF − ref) |
|---|---:|---:|---:|
| przetargi_ogloszenia | 98,411% | 100% | −381 (−0,180%) |
| przetargi_kio | 98,065% | 100% | +55 (+0,041%) |
| samorzad_uchwaly | 97,945% | 100% | −339 (−0,309%) |
| granty_ogloszenia | 95,567% | 100% | −726 (−0,403%) |
| prawo_eli | 98,049% | 100% | −479 (−0,234%) |
| ocr_prasa | 96,188% | 100% | −60 (−0,034%) |
| tabele_json | 94,702% | 100% | **−723 (−0,522%)** |
| web | **99,361%** | 100% | −34 (−0,015%) |
| wikipedia | 92,944% | 100% | −375 (−0,146%) |
| literatura | 99,741% | 100% | −53 (−0,019%) |
| sejm | 99,477% | 100% | −63 (−0,031%) |

**H8 potwierdzona:** parytet urzędowy 97,27% (ID) vs web 99,36% (z = −31,0),
wszystkie 7 dziedzin urzędowych <99%. **Po zdekodowaniu 100% fragmentów jest
identycznych** — różnica dotyczy scalania, nie utraty znaków/spacji; kontrolę
dodano po rundzie 2 (`identical_share_decoded`). Dominujące przyczyny różnic: cyfry (szczególnie
4+), kropki/skróty, fragmenty z wieloma spacjami. Eksport jest **nieco bardziej
kompresyjny** niż referencja, bo HF stosuje merge'e w jednym przebiegu na całym
fragmencie; to nie jest „lepszy tokenizer”, tylko inny. Skutek: trening i ocena
muszą używać **tego samego** pliku `tokenizer.json`.

### 3.8a Kontekst 2048/4096 (niezależna runda 3)

Pełny tekst bez cięcia 20k, tokenizer HF: ogłoszenie przetargowe mediana 3984,
p90 7396, w 2048 1,7%, w 4096 53,3%; po rozbiciu cyfr mediana 4646 i w 4096
33,3%. Pełny akt śląski: mediana 2403, p90 7408, w 2048 40%, w 4096 72,5%.
Źródło: `audit/results/context_full.json`,
`results/doc_lengths_extra.json`. To decyzja o oknie modelu, nie o tokenizerze.

### 3.9 Szybkość — `results/speed.json`

1 wątek, 1 MB tekstu, mediana z 3 zimnych przebiegów (cache Python czyszczony):

| tokenizer | tokeny/s | MB/s |
|---|---:|---:|
| TOKENIZATOREX (Python) | 176 114 | 0,91 |
| TOKENIZATOREX-HF | 574 823 | 2,98 |
| TOKENIZATOREX-base | 237 129 | 1,10 |
| Slayer1B | 376 727 | 1,65 |
| APT3-1B | 446 468 | 2,10 |
| Pollock-2.0 | 358 370 | 1,67 |
| Bielik-v3 | 549 193 | 1,40 |
| PLLuM-12B | 457 270 | 1,50 |
| GPT-4o | 3 029 369 | 10,18 |

Referencja Python jest ~3,3× wolniejsza od HF. Dla 300 MB danych treningowych
to różnica minut, nie godzin; dla treningu modelu liczy się HF.

### 3.10 Stabilność — `results/stability.json`

Tymczasowy retrening (audit/tmp, nie zastępuje repo): inny shard HPLT
`bin8_5_p2`, etap 1 = 300 MB, etap 2 = 100 MB, t = 20k, vocab = 32k, max 4 słowa.
Czas 345 s. Pokrycie słownika: 28 576/32 000 = **89,3%** (etap 1: 93,3%).
Fertility na testach: przetargi −1,10%, KIO −0,32%, prawo ELI +1,96%, web −0,12%.
**Wniosek:** wydajność jest stabilna (≤2%), ale dokładny słownik nie (10,7%
innych tokenów). To ryzyko dla reprodukowalności i dla parytetu HF.

## 4. Status hipotez

| # | Hipoteza | Status | Kluczowa liczba (plik) |
|---|---|---|---|
| H1 | kalendarz zamrożony | **POTWIERDZONA** | 2015–2024: 1 tok.; 2025–2026: 2 tok.; szablon 4→5 (`notations.json`) |
| H2 | długie liczby/kody chaotyczne | **CZĘŚCIOWO** | koszt/cyfrę ~0,6 (stały), ale CPV 21,7%, NIP 46,4% innych podziałów (`consistency.json`) |
| H3 | skróty urzędowe niespójne | **POTWIERDZONA** | `lit.` 42,9%, `Dz.U.` 42,9%, `poz.` 42,9% (`consistency.json`) |
| H4 | ten sam zapis różnie w kontekście | **POTWIERDZONA** | 19/19 kategorii ≥5% (`consistency.json`) |
| H5 | odporność NFD/CAPS | **POTWIERDZONA** | NFD +45,9%, CAPS +106,8%, Title +30,6% (`robustness.json`) |
| H6 | 19,4% superwordów od środka | **OBALONA** | 3,5% (1,6–13,2%), użycie 0,09% (`superwords.json`) |
| H7 | częste słowa mają token, problem w superwordach | **CZĘŚCIOWO / NIE** | 88,2% top 1000 ma token; 2,83% rozbitych z superwordem (`superwords.json`) |
| H8 | HF różni się na urzędowych | **POTWIERDZONA** | 97,27% vs 99,36%; z = −31,0 (`hf_parity.json`) |
| H9 | pułapka `sys.path` | **OBSŁUŻONA** | `common.py` importuje HF przed `append`; test `test_h9_*` |

## 5. Problem → skala → przykład → możliwa poprawka

| Problem | Skala (z CI) | Przykład | Możliwa poprawka (TKX-C) |
|---|---|---|---|
| Kalendarz: nowe lata droższe | +1 token na rok 2025+; 2026 2,00 vs 1,00 | `2024 r.` → `202│4·r.`; `2026` → `202│6` | grupowanie cyfr od prawej albo pojedyncze cyfry (Singh i Strouse 2024); `r.` jako token |
| Niestabilna segmentacja zapisów | 12,8–57,1% kontekstów; Slayer 0–28,6% | `Dz.U.` → `Dz│.│U.` vs `│Dz.│U.` | zakaz superwordów zaczynających się w środku słowa; osobny pretokenizator dla zapisów |
| HF nie 1:1 | 94,7–98,4% fragmentów na urzędowych | tabele JSON −0,52% tokenów | ujednolicić pretokenizator eksportu; test parytetu w CI |
| NFD z PDF | +45,9% (Slayer +37,8%) | `ą` → `a` + ogonek | NFC przed kodowaniem (w pipeline, nie w tokenizerze) |
| CAPS | +106,8% (Slayer +101,4%, GPT-4o +45,6%) | `ZAMAWIAJĄCY` | osobny token wielkiej litery / niższy case w pretokenizacji |
| Morfologia | precision 0,023 vs Slayer 0,082 | `Wyda│je` | Picky BPE / morfemowe ograniczenia (eksperyment) |
| Boilerplate w słowniku | 0,012% użyć w naszym korpusie | `Czytaj więcej` | filtr boilerplate'u w danych treningowych (tanie, mały zysk) |
| Słownik zależny od shardu | 89,3% wspólnych tokenów | inne HPLT | mieszanka danych + większy/wielokrotny trening; zamrożenie shardów |

## 6. Ograniczenia

* Fertility ≠ jakość modelu; modelu 150M jeszcze nie trenowano.
* APT3 jest stratny (NFKC), więc jego wynik jest zaniżony kosztem wierności.
* OCR z Polony ma błędy rozpoznawania — celowo.
* ELI 2026 to PDF-y; pypdf może łamać linie — identycznie dla wszystkich.
* Dokumenty przycięte do 20 tys. znaków (jak w README); na pełnym PDF uchwał
  przewaga nad APT3 spada do 0,55% (HF 0,82%), a APT3 jest stratny (6/1010).
* „Tabele JSON” to ten sam strumień BZP co ogłoszenia — nie siódma niezależna
  dziedzina.
* Szacunek cyfr (+6,7–15,0% na urzędowych, +16,6% na pełnym ogłoszeniu) nie jest
  tokenizerem po retreningu; prawdziwy koszt zmierzy TKX-C.
* H6/H1/consistency mają korekty implementacji opisane w „Zmianach po fakcie”;
  H6 jest oznaczone jako post hoc.
* Stabilność to jeden retrening na jednym innym shardzie, nie distribution shift.
* Morfologia: SuperBPE oceniany na izolowanych formach (oficjalny kod MorphScore
  nie ma kontekstu); to może zaniżać wynik superwordów.

## 7. Rundy 2 i 3 — samoocena i niezależne

`REVIEW_R2.md` i `RED_TEAM_R3.md` to **samoocena wykonawcy**, nie niezależne
rundy. Niezależne rundy zrobili osobno Codex i Grok; ich liczby mają
pierwszeństwo.

* **Runda 2 — Codex:** gałąź `review/tkx-a-r2-codex` @ `47e9cb2`;
  `audit/independent/codex/REVIEW_CODEX_R2.md`; werdykt **PASS_Z_UWAGAMI**,
  12/12 liczb powtórzonych. Uwagi: brak pomiaru cyfr, Rényi tylko `exp(H)/|V|`,
  HF #1 wynika ze scalania (ciągi 100%), bootstrap RNG, parytet przez ID.
* **Runda 3 — Grok:** gałąź `review/tkx-a-r3-grok` @ `686cbce`;
  `audit/independent/grok/RED_TEAM_GROK_R3.md`; werdykt **zmienia 2, osłabia 2,
  nie zmienia 3**. Zmienia: Rényi i kryterium sukcesu modelu. Osłabia: pełne PDF
  uchwał i „tokeny albo bajty”. Nie zmienia: 4 nowe źródła, round-trip, 2048, H1.
* Po tych rundach: dodano `digits_cost.py`, obie formy Rényiego, pełne PDF
  uchwał, sekcję o kontekście, parytet HF na ciągach i jeden RNG bootstrapu.
