# RUNDA 3 — RED TEAM („adwokat diabła”) — TOKENIZATOREX / TKX-A

Data: 19.11.2026 · Zakres: `split == "test"` · 7 dziedzin oficjalnych (606 dok.)
+ `web` (421) + `wikipedia` (241) + `nauka` (62).

Tokenizery: **TOKENIZATOREX** (`superbpe.SuperBPETokenizer.encode_ordinary`),
**TOKENIZATOREX-HF** (`hf/tokenizatorex-32k/tokenizer.json`,
`add_special_tokens=False`), **Slayer1B**, **Pollock-2.0**, **APT3-1B**
(pliki z `audit/data/tokenizer_files/`).

H9: `tokenizers` (HF) importowany **przed** `sys.path.append(repo)`; nigdzie
nie ma `insert(0, repo_root)`. Skrypty nie modyfikują `audit/*.py` z rundy 1,
`tokenizers/`, `hf/` ani `superbpe.py`. Wszystkie nowe pliki są wyłącznie
w `audit/redteam/` oraz w tym raporcie.

Skrypty i artefakty:

* `audit/redteam/rtlib.py` — wspólne ładowanie danych i tokenizerów,
* `audit/redteam/r3_robust.py` → `r3_robustness.json` — zadanie 1,
* `audit/redteam/r3_worst50.py` → `r3_worst50.json` — zadanie 2,
* `audit/redteam/r3_examples.py` → `r3_examples.txt` — krótkie przykłady,
* `audit/redteam/r3_boilerplate.py` → `r3_boilerplate.json` — zadanie 3,
* `audit/redteam/r3_context2048.py` → `r3_context2048.json` — zadanie 4.

---

## 1. Lista znalezisk (każde z liczbą, przykładem i werdyktem)

### F1. Rankingi są odporne na definicję słowa, jednostkę i obcięcie ogona

Na 10 dziedzinach i 3 alternatywnych definicjach (regex-literowe słowa,
tokeny/bajt UTF-8, obcięcie 10% najdłuższych dokumentów) **top-1 zmienił się
0/30 razy, a zestaw top-2 — 0/30 razy**. Oficjalny agregat (7 dziedzin,
685 753 słowa) ma w każdej definicji tę samą kolejność:
**HF 1,6787 < TKX 1,6825 < Pollock 1,7921 < APT3 1,8612 < Slayer 2,0265**
(dla liter: 1,8279 / 1,8321 / 1,9514 / 2,0267 / 2,2066; dla bajtów:
0,21805 / 0,21856 / 0,23280 / 0,24177 / 0,26324; po drop10:
1,6829 / 1,6866 / 1,7960 / 1,8675 / 2,0326).

Przykład: `granty_ogloszenia` — Pollock wygrywa w każdej wersji
(1,7806 vs TKX 1,7909; litery 2,0465 vs 2,0584; bajty 0,2144 vs 0,2157;
drop10 1,7547 vs 1,7628), a jego przewaga to 0,46–0,60%. Jedyne pierwsze
miejsce TKX (`przetargi_kio`) utrzymuje się we wszystkich trzech wariantach
(1,403 / 1,510 / 0,182).

**Werdykt: NIE ZMIENIA WNIOSKU.**

### F2. Leave-one-source-out nie rusza czołówki

Po usunięciu kolejno każdej z 7 dziedzin oficjalnych agregat (suma tokenów /
suma słów) zawsze daje **HF #1, TKX #2, Pollock #3**; różnica TKX do zwycięzcy
to 0,19–0,27%. Zwycięzca średniej po dziedzinach też jest zawsze ten sam (HF).
Nie ma ani jednego folda, w którym znika przewaga rodziny TKX nad Pollockiem.

Przykład: po usunięciu `tabele_json` — HF 1,6006, TKX 1,6037, Pollock 1,7156.

**Werdykt: NIE ZMIENIA WNIOSKU.**

### F3. Przewaga Pollocka na `granty_ogloszenia` jest realna, nie definicyjna

Pollock jest #1 we wszystkich czterech definicjach; TKX jest **#3**, za HF.
Przewaga Pollocka nad TKX: 0,58% (baseline), 0,58% (litery), 0,60% (bajty),
0,46% (drop10). To nadal mieści się w duchu „praktyczny remis”, ale nie jest
artefaktem `str.split()` ani długich dokumentów.

Przykład: `granty_ogloszenia`, dokument z listą ofert — nagłówek
„Tytuł zadania Oferent NIP Miejscowość Województwo Wynik oceny formalnej”.

**Werdykt: NIE ZMIENIA WNIOSKU (utrwala znane zastrzeżenie).**

### F4. Wikipedia: Pollock wygrywa niezależnie od definicji

Pollock #1, TKX #3, przewaga Pollocka nad TKX: 1,27% (baseline), 1,25%
(litery), 1,26% (bajty), 1,50% (drop10). Żadna alternatywna definicja nie
odwraca tej straty.

Przykład: `wikipedia`, wariant drop10 — Pollock 1,8154 vs TKX 1,8431.

**Werdykt: NIE ZMIENIA WNIOSKU.**

### F5. Nauka: APT3 wygrywa, a TKX jest #4, nie #3

APT3 jest #1 w każdej definicji; TKX jest **#4**, za APT3, Pollockiem i HF.
Przewaga APT3 nad TKX: 3,04% (baseline), 2,95% (litery), 2,98% (bajty),
3,03% (drop10). Pollock i HF wyprzedzają TKX minimalnie (0,04–0,19%), ale
konsekwentnie we wszystkich wariantach.

Przykład: `nauka` — „Opracowanie stanowi syntezę konsekwencji zastosowań ICT
w kulturze społeczeństwa informacyjnego”: długie wyrazy złożone i angielskie
wtrącenia, czyli nie typowa polszczyzna urzędowa.

**Werdykt: NIE ZMIENIA WNIOSKU (korekta pozycji: #4 zamiast #3).**

### F6. „Najgorsze” dokumenty to nie cyfry i tabele, lecz długa proza, OCR i formularze

Spośród 606 dokumentów oficjalnych Slayer1B bije TKX tylko na **6**, a APT3 na
**12**. Maksymalna przewaga: **+14,78%** (francuski OCR, `polona-MTI1NTI1Mzk4`:
2185 vs 1862 tokenów) i **+6,35%** (`prawo_eli`, `eli-DU-2026-408`: 598 vs 560).
Top-50 „najgorszych” dokumentów dla Slayera to 23 × `ocr_prasa` i 18 ×
`granty_ogloszenia`; dla APT3 — 21 × `prawo_eli` i 17 × `ocr_prasa`.

Wspólne cechy top-50 (mediana vs mediana całego zbioru):

| cecha | cały zbiór | top-50 Slayer | top-50 APT3 |
|---|---:|---:|---:|
| znaki | 4 896 | 18 153 | 15 266 |
| udział cyfr | 5,34% | 2,04% | 3,91% |
| średnia długość słowa | 5,81 | 6,21 | 6,08 |
| `rn` na 1000 słów (OCR) | 2,38 | 4,39 | 3,68 |
| angielskie stopwords | 3,02% | 3,90% | 3,93% |
| słowa z cyfrą i literą / 1000 | 7,30 | 3,51 | 3,17 |

Angielskie stopwords to mała lista ~50 słów (`the`, `and`, `of`, `to`, …);
„OCR-like” = słowa zawierające `rn`. Korelacja Spearmana z przewagą konkurenta: długość dokumentu +0,55/+0,43,
średnia długość słowa +0,50/+0,31, OCR +0,30/+0,22, udział cyfr **−0,30/−0,09**.
Czyli TKX wygrywa najmocniej tam, gdzie są cyfry i notacja; przegrywa (lub
wygrywa najmniej) na długiej prozie bez cyfr, z długimi słowami i szumem OCR.

Przykłady (krótkie, generyczne fragmenty):

* OCR francuski: „DU COMMUNISME PARIS PROVINCE MAI 1849. PAULIN ET LHEUREUX…” —
  813 słów, TKX 2185, Slayer 1862.
* OCR niemiecki (fraktur): ciągi typu „erfdjft ni jweimal…” — 2826 słów,
  TKX 9882, Slayer 9063.
* Formularz grantowy z pustymi polami: „Zgłoszenie na konkurs na najlepszą
  pracę” oraz linie `_ _ _ _ _ _ _ _` — 470 słów, TKX 925, Slayer 796.
* Tabela grantowa: „Tytuł zadania Oferent NIP Miejscowość Województwo Wynik
  oceny formalnej” — 584 słowa, TKX 1348, APT3 1321.
* Prawo ELI: „w sprawie ogłoszenia jednolitego tekstu rozporządzenia Ministra
  Zdrowia” — 296 słów, TKX 598, APT3 560.

**Werdykt: NIE ZMIENIA WNIOSKU agregatowego, ale zawęża jego zakres: poza
polską prozą urzędową, na niepolskim OCR i na formularzach z pustymi polami
przewaga TKX może zniknąć.**

### F7. Boilerplate nie jest źródłem przewagi

Usunięcie linii/zdań z 15 fraz („Czytaj więcej”, „Kontakt”, „Menu”, „cookies”
itd.) usuwa 0,79% znaków w wariancie granicznym i 2,33% w wariancie
dosłownym (133 / 199 dokumentów). Oficjalny agregat zmienia się o **mniej niż
0,06%** (wariant graniczny) lub **mniej niż 0,5%** (dosłowny), a kolejność
pozostaje identyczna:

| wariant | TKX | HF | Pollock | Slayer | web TKX |
|---|---:|---:|---:|---:|---:|
| baseline | 1,6825 | 1,6787 | 1,7921 | 2,0265 | 1,4156 |
| graniczny | 1,6818 | 1,6779 | 1,7912 | 2,0256 | 1,4141 |
| dosłowny | 1,6754 | 1,6715 | 1,7855 | 2,0221 | 1,4150 |

Najczęstsze trafienia: „Kontakt” 169, „Czytaj więcej” 46, „Reklama” 33,
„Menu” 20. Przykład: zdanie „Wszystkie potrzebne dane uzyskasz w zakładce
Kontakt.” w `web` — po usunięciu takich linii fertility TKX w `web` spada
o 0,11%, czyli prawie nic.

**Werdykt: NIE ZMIENIA WNIOSKU.**

### F8. W 2048 tokenach typowy przetarg i tak się nie mieści — żaden tokenizer tego nie naprawia

`przetargi_ogloszenia` (60 dok.): mediana TKX **3780** tokenów, p90 **4134**,
maks. **4507**; tylko **1/60 (1,7%)** mieści się w 2048, a na jeden kontekst
przypada **0,581** przeciętnego dokumentu. Slayer: mediana 4866, p90 5238,
0/60 w 2048. Pollock: 4417 / 4790, 0/60. APT3: 4380 / 4739, 0/60.

Proxy „typowe SWZ” (najdłuższe 25% dokumentów `przetargi_ogloszenia`, 15 dok.,
**to nie jest prawdziwy zbiór SWZ**): TKX mediana **3933**, p90 **4084**,
0/15 w 2048; Pollock 4620 / 4725, APT3 4620 / 4691, Slayer 5170 / 5230 —
wszystkie 0/15.

**Werdykt: NIE ZMIENIA WNIOSKU (wzmacnia zastrzeżenie: tokenizer zmniejsza
liczbę tokenów, ale nie rozwiązuje limitu kontekstu).**

### F9. W 2048 na `granty_ogloszenia` TKX nie jest jednoznacznie najlepszy

Mediana i udział dokumentów mieszczących się w 2048 faworyzują TKX/HF, ale
średnia i p90 faworyzują Pollocka:

| miara | TKX | HF | Pollock | Slayer | APT3 |
|---|---:|---:|---:|---:|---:|
| mediana tokenów | **2337** | 2336 | 2570 | 2918 | 2660 |
| średnia | 2728,4 | 2717,4 | **2712,7** | 3174,3 | 3125,4 |
| p90 | 4943,5 | 4899,0 | **4796,5** | 5572,0 | 5909,5 |
| dokumenty w 2048 | **42,4%** | **42,4%** | 40,9% | 40,9% | 40,9% |
| przeciętne dok. na 2048 | 0,751 | 0,754 | **0,755** | 0,645 | 0,655 |

To jest remis zależny od statystyki: „typowy” dokument (mediana) jest tańszy
w TKX, ale ogon (średnia, p90) jest tańszy w Pollocku. Nie można twierdzić,
że TKX jest jednoznacznie lepszy w 2048 na grantach.

**Werdykt: ZMIENIA WNIOSEK lokalnie (granty/2048); nie zmienia agregatu
7 dziedzin ani rankingu fertility.**

---

## 2. Dowody szczegółowe

### 2.1. Oficjalny agregat w czterech definicjach

Wartości „mniej = lepiej”; litery = `[^\W\d_]+`, bajty = UTF-8, drop10 =
bez 10% najdłuższych dokumentów w dziedzinie.

| tokenizer | baseline tok./słowo | litery tok./słowo | bajty tok./bajt | drop10 tok./słowo |
|---|---:|---:|---:|---:|
| TOKENIZATOREX-HF | **1,6787** | **1,8279** | **0,21805** | **1,6829** |
| TOKENIZATOREX | 1,6825 | 1,8321 | 0,21856 | 1,6866 |
| Pollock-2.0 | 1,7921 | 1,9514 | 0,23280 | 1,7960 |
| APT3-1B | 1,8612 | 2,0267 | 0,24177 | 1,8675 |
| Slayer1B | 2,0265 | 2,2066 | 0,26324 | 2,0326 |

### 2.2. LOSO — leave-one-official-domain-out

Agregat pooled po usunięciu jednej dziedziny:

| usunięta dziedzina | #1 | #2 | #3 | różnica TKX do #1 |
|---|---|---|---|---:|
| przetargi_ogloszenia | HF 1,7099 | TKX 1,7140 | Pollock 1,7873 | +0,24% |
| przetargi_kio | HF 1,7232 | TKX 1,7278 | Pollock 1,8398 | +0,27% |
| samorzad_uchwaly | HF 1,6969 | TKX 1,7006 | Pollock 1,7967 | +0,22% |
| granty_ogloszenia | HF 1,6606 | TKX 1,6639 | Pollock 1,7941 | +0,20% |
| prawo_eli | HF 1,7278 | TKX 1,7317 | Pollock 1,8516 | +0,23% |
| ocr_prasa | HF 1,6423 | TKX 1,6467 | Pollock 1,7692 | +0,27% |
| tabele_json | HF 1,6006 | TKX 1,6037 | Pollock 1,7156 | +0,19% |

### 2.3. Domeny specjalnej troski — pełne liczby

`granty_ogloszenia` (Pollock nominalnie lepszy):

| wariant | Pollock | HF | TKX | przewaga Pollocka nad TKX |
|---|---:|---:|---:|---:|
| baseline | 1,7806 | 1,7837 | 1,7909 | 0,58% |
| litery | 2,0465 | 2,0501 | 2,0584 | 0,58% |
| bajty | 0,2144 | 0,2148 | 0,2157 | 0,60% |
| drop10 | 1,7547 | 1,7565 | 1,7628 | 0,46% |

`wikipedia` (znana strata do Pollocka):

| wariant | Pollock | HF | TKX | przewaga Pollocka nad TKX |
|---|---:|---:|---:|---:|
| baseline | 1,7628 | 1,7826 | 1,7852 | 1,27% |
| litery | 1,8545 | 1,8753 | 1,8780 | 1,25% |
| bajty | 0,2273 | 0,2299 | 0,2302 | 1,26% |
| drop10 | 1,8154 | 1,8384 | 1,8431 | 1,50% |

`nauka` (znana strata do APT3; TKX #4):

| wariant | APT3 | Pollock | HF | TKX | przewaga APT3 nad TKX |
|---|---:|---:|---:|---:|---:|
| baseline | 1,9175 | 1,9735 | 1,9750 | 1,9759 | 3,04% |
| litery | 2,0816 | 2,1424 | 2,1440 | 2,1450 | 2,95% |
| bajty | 0,2507 | 0,2580 | 0,2582 | 0,2583 | 2,98% |
| drop10 | 1,9250 | 1,9794 | 1,9821 | 1,9831 | 3,03% |

### 2.4. Najgorsze 50 dokumentów — tabele

Top-5 przewagi Slayera nad TKX:

| dokument | dziedzina | słowa | TKX | Slayer | przewaga | typ |
|---|---|---:|---:|---:|---:|---|
| polona-MTI1NTI1Mzk4 | ocr_prasa | 813 | 2185 | 1862 | +14,78% | OCR francuski |
| grant-1ee84940c27f | granty | 470 | 925 | 796 | +13,95% | formularz z `_ _ _` |
| polona-NzU4NDAyMDA | ocr_prasa | 2826 | 9882 | 9063 | +8,29% | OCR niemiecki |
| polona-ODE2OTAwMTk | ocr_prasa | 2903 | 9835 | 9103 | +7,44% | OCR niemiecki |
| polona-MTEwNTg0NTI3 | ocr_prasa | 2079 | 7384 | 6924 | +6,23% | OCR niemiecki |

Top-5 przewagi APT3 nad TKX:

| dokument | dziedzina | słowa | TKX | APT3 | przewaga | typ |
|---|---|---:|---:|---:|---:|---|
| eli-DU-2026-408 | prawo_eli | 296 | 598 | 560 | +6,35% | proza prawna |
| polona-MTEwNTg0NTI3 | ocr_prasa | 2079 | 7384 | 7018 | +4,96% | OCR niemiecki |
| polona-MTI1NTI1Mzk4 | ocr_prasa | 813 | 2185 | 2120 | +2,97% | OCR francuski |
| polona-NzU4NDAyMDA | ocr_prasa | 2826 | 9882 | 9658 | +2,27% | OCR niemiecki |
| grant-12b940f85884 | granty | 584 | 1348 | 1321 | +2,00% | tabela ofert |

Skład top-50: Slayer — 23 `ocr_prasa`, 18 `granty`, 4 `prawo_eli`,
5 `tabele_json`; APT3 — 21 `prawo_eli`, 17 `ocr_prasa`, 8 `granty`,
3 `tabele_json`, 1 `samorzad_uchwaly`.

### 2.5. Boilerplate — co dokładnie usuwano

Lista fraz: „Czytaj więcej”, „Zobacz także”, „Zobacz też”, „Polityka
prywatności”, „cookies”, „Strona główna”, „Menu”, „Szukaj”, „Newsletter”,
„Reklama”, „Zaloguj”, „Kontakt”, „Dowiedz się więcej”, „Wróć”, „Pobierz”.
Wariant „graniczny” wymaga granicy słowa dla fraz jednowyrazowych (żeby
„Kontakt” nie usuwał „kontaktowy”); wariant „dosłowny” usuwa każdy podciąg.

| miara | baseline | graniczny | dosłowny |
|---|---:|---:|---:|
| usunięte znaki | 0% | 0,79% | 2,33% |
| zmienione dokumenty | 0 | 133 | 199 |
| słowa oficjalne | 685 753 | 682 893 | 672 182 |
| TKX oficjalny | 1,6825 | 1,6818 | 1,6754 |
| HF oficjalny | 1,6787 | 1,6779 | 1,6715 |
| Pollock oficjalny | 1,7921 | 1,7912 | 1,7855 |
| Slayer oficjalny | 2,0265 | 2,0256 | 2,0221 |
| TKX web | 1,4156 | 1,4141 | 1,4150 |

### 2.6. Kontekst 2048 — pełne tabele

`przetargi_ogloszenia` (60 dok., 136 034 słowa):

| tokenizer | średnia | mediana | p90 | maks. | w 2048 | dok. na 2048 | tokeny poza 2048 |
|---|---:|---:|---:|---:|---:|---:|---:|
| TOKENIZATOREX | 3526,0 | 3780 | 4134 | 4507 | 1,7% | 0,581 | 42,0% |
| TOKENIZATOREX-HF | 3519,7 | 3775 | 4114 | 4500 | 1,7% | 0,582 | 41,9% |
| Slayer1B | 4573,2 | 4866 | 5238 | 5819 | 0,0% | 0,448 | 55,2% |
| Pollock-2.0 | 4107,4 | 4417 | 4790 | 5339 | 0,0% | 0,499 | 50,1% |
| APT3-1B | 4072,6 | 4380 | 4739 | 5017 | 0,0% | 0,503 | 49,7% |

`granty_ogloszenia` (66 dok., 100 550 słów):

| tokenizer | średnia | mediana | p90 | maks. | w 2048 | dok. na 2048 | tokeny poza 2048 |
|---|---:|---:|---:|---:|---:|---:|---:|
| TOKENIZATOREX | 2728,4 | 2337 | 4943 | 6173 | 42,4% | 0,751 | 42,5% |
| TOKENIZATOREX-HF | 2717,4 | 2336 | 4899 | 6058 | 42,4% | 0,754 | 42,3% |
| Slayer1B | 3174,3 | 2918 | 5572 | 6991 | 40,9% | 0,645 | 48,6% |
| Pollock-2.0 | 2712,7 | 2570 | 4796 | 6031 | 40,9% | 0,755 | 41,9% |
| APT3-1B | 3125,4 | 2660 | 5910 | 6420 | 40,9% | 0,655 | 48,9% |

Proxy SWZ (najdłuższe 25% `przetargi_ogloszenia`, 15 dok., 39 479 słów;
**proxy, nie prawdziwy SWZ**):

| tokenizer | średnia | mediana | p90 | maks. | w 2048 | dok. na 2048 | tokeny poza 2048 |
|---|---:|---:|---:|---:|---:|---:|---:|
| TOKENIZATOREX | 3920,7 | 3933 | 4084 | 4274 | 0,0% | 0,522 | 47,8% |
| TOKENIZATOREX-HF | 3913,9 | 3925 | 4076 | 4261 | 0,0% | 0,523 | 47,7% |
| Slayer1B | 5076,9 | 5170 | 5230 | 5558 | 0,0% | 0,403 | 59,7% |
| Pollock-2.0 | 4576,6 | 4620 | 4725 | 5057 | 0,0% | 0,447 | 55,3% |
| APT3-1B | 4554,8 | 4620 | 4691 | 4813 | 0,0% | 0,450 | 55,0% |

---

## 3. Co jest odporne

* **Top-1/top-2 na 10 dziedzinach.** 0/30 zmian przy regex-literach,
  tokenach/bajt i drop10. Także 0/30 zmian zestawu top-2.
* **Kolejność oficjalna.** HF < TKX < Pollock < APT3 < Slayer w każdej
  z czterech definicji; różnica HF–TKX to 0,2–0,3%.
* **LOSO.** HF #1, TKX #2 we wszystkich 7 foldach; Pollock #3.
* **Znane słabości.** Granty (Pollock, 0,46–0,60%), Wikipedia (Pollock,
  1,25–1,50%), nauka (APT3, 2,95–3,04%) — wszystkie przeżywają zmiany definicji.
* **Boilerplate.** Usunięcie 15 fraz zmienia fertility o <0,06% (granicznie)
  lub <0,5% (dosłownie); ranking bez zmian. Przewaga TKX nie pochodzi z sieci.
* **Przewaga na cyfrach i tabelach.** Udział cyfr jest ujemnie skorelowany
  z przewagą konkurenta (−0,30 dla Slayera); w `przetargi` TKX ma 1,555 vs
  APT3 1,796 (APT3 +15,5%), a w `tabele_json` 2,629 vs Pollock 2,711
  (Pollock +3,1%).

## 4. Co jest kruche

* **Nazwa „TOKENIZATOREX wygrywa” zależy od utożsamienia referencji z HF.**
  To HF jest #1 w 5/7 dziedzin oficjalnych; referencyjny Python jest #2
  w 5/7 (0,03–0,53% za HF), #1 w KIO i #3 w grantach. Rodzina ta sama, ale
  zdanie „referencja jest najlepsza” jest nieprecyzyjne.
* **Granty w 2048.** Mediana i „fit rate” faworyzują TKX, ale średnia i p90
  faworyzują Pollocka; przewaga TKX w kontekście nie jest jednoznaczna.
* **Niepolski OCR.** 5 z 6 zwycięstw Slayera to OCR francuski/niemiecki;
  maks. +14,78%. Agregat `ocr_prasa` to maskuje (TKX nadal #1 w dziedzinie),
  ale przy większym udziale takich tekstów ranking mógłby się przesunąć.
* **Formularze z pustymi polami.** Jeden dokument grantowy z `_ _ _ _` daje
  Slayerowi +13,95% nad TKX. To wąski, ale realny przypadek.
* **Długa proza bez cyfr i z szumem OCR.** Top-50 „najgorszych” ma medianę
  18,2 tys. znaków (vs 4,9 tys.), 2,0% cyfr (vs 5,3%) i 4,39 `rn`/1000 słów
  (vs 2,38). Przewaga TKX topi się, gdy nie ma notacji do wykorzystania.
* **Wrażliwość wartości absolutnych na skład korpusu.** `tabele_json` po
  drop10 rośnie z 2,629 do 2,783 (+5,9%), mimo że ranking się nie zmienia.
* **Limit 2048.** Typowy przetarg ma 3,5 tys. tokenów (1,7× kontekstu),
  a tylko 1,7% dokumentów się mieści; proxy SWZ ma 3,9 tys. i 0% w 2048.
  Tokenizer zmniejsza koszt, ale nie rozwiązuje problemu kontekstu.

---

## 5. Werdykt końcowy

Rdzeń wniosków rundy 1 **przetrwał** próbę rozbicia: rankingi na 10 dziedzinach
są odporne na definicję słowa, jednostkę i obcięcie 10% ogona, a LOSO nie
zmienia czołówki. Znane słabości (granty/Pollock, Wikipedia/Pollock,
nauka/APT3) są realne i nie znikają pod alternatywnymi definicjami.

Red team znajduje jednak trzy zastrzeżenia, które należy dopisać do raportu:
(1) „wygrywa” to w praktyce HF, nie referencyjny Python; (2) na grantach
w 2048 widać remis zależny od statystyki (mediana vs średnia/p90);
(3) na niepolskim OCR i formularzach z pustymi polami TKX potrafi przegrać
z Slayerem o 14%, choć agregat dziedzinowy tego nie pokazuje.

```
RED_TEAM_RESULT
ranking_changes: none — 0/30 zmian top-1 i 0/30 zmian zestawu top-2 dla (a) regex-liter, (b) tokenów/bajt, (c) drop10; LOSO: HF #1, TKX #2 we wszystkich 7 foldach; granty/wikipedia/nauka bez zmiany zwycięzcy
conclusion_changes: none at the 7-domain aggregate level; one local correction: on granty at 2048 tokens TKX is not unambiguously best (median 2337 and 42.4% fit vs Pollock mean 2712.7 and p90 4796.5); caveats: 6/606 docs where Slayer beats TKX (max +14.78% on non-Polish OCR, +13.95% on a blank grant form) and 12/606 where APT3 beats TKX (max +6.35%)
```
