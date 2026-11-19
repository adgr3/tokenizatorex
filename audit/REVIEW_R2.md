# Niezależna recenzja rundy 2 (rola „Codex”) — TOKENIZATOREX / TKX-A

Data: 19.11.2026 · Recenzent: niezależny agent (Codex) · Repo: `tokenizatorex`
Zakres: pięć liczb z §9 `PROTOKOL.md`, policzone od zera na `split == "test"`.
Środowisko: Python 3.12.10, `tokenizers` 0.23.3, `regex` 2026.11.19, `numpy` 2.5.5,
CPU, bez sieci. H9 obsłużone: pakiet HF `tokenizers` importowany **przed**
`sys.path.append(REPO)`; nigdzie nie ma `insert(0, repo_root)`.

Skrypty R2 (tylko odczyt danych; nic nie modyfikują poza `audit/review/`):

* `audit/review/r2lib.py` — wspólne ładowanie dokumentów i tokenizerów,
* `audit/review/run_fertility.py` → `audit/review/r2_fertility.json`,
* `audit/review/run_h1.py` → `audit/review/r2_h1_calendar.json`,
* `audit/review/run_h5.py` → `audit/review/r2_h5_nfd.json`,
* `audit/review/run_h6.py` → `audit/review/r2_h6_superwords.json`,
* `audit/review/run_h8.py` → `audit/review/r2_h8_hf_parity.json`,
* `audit/review/diag.py` — odtworzenie wyborów R1 (H5), regexu roku (H1) i kryterium H6,
* `audit/review/compare.py` — zestawienie liczb R2 z JSON-ami R1.

Liczby R1 pochodzą wyłącznie z `audit/results/*.json` (nie kopiowałem ich do R2).

---

## 1. Fertility (tokeny / `text.split()`, TEST)

| Dziedzina | Tokenizer | R2 | R1 | Δ wzgl. | Wyjaśnienie |
|---|---|---:|---:|---:|---|
| przetargi_ogloszenia | TOKENIZATOREX | 1.555199 | 1.555199 | +0.0000% | zgodne |
| przetargi_ogloszenia | TOKENIZATOREX-HF | 1.552399 | 1.552399 | +0.0000% | zgodne |
| przetargi_ogloszenia | Slayer1B | 2.017069 | 2.017069 | +0.0000% | zgodne |
| przetargi_kio | TOKENIZATOREX | 1.402656 | 1.402656 | +0.0000% | zgodne |
| przetargi_kio | TOKENIZATOREX-HF | 1.403232 | 1.403232 | +0.0000% | zgodne |
| przetargi_kio | Slayer1B | 1.719827 | 1.719827 | +0.0000% | zgodne |
| granty_ogloszenia | TOKENIZATOREX | 1.790910 | 1.790910 | +0.0000% | zgodne |
| granty_ogloszenia | TOKENIZATOREX-HF | 1.783690 | 1.783690 | +0.0000% | zgodne |
| granty_ogloszenia | Slayer1B | 2.083570 | 2.083570 | +0.0000% | zgodne |

Liczby dokumentów i słów zgadzają się z manifestem: 60/136034, 66/95409, 66/100550.
R2 liczy `len(text.split())` samodzielnie (nie używa pola `words`).

## 2. H1 — koszt lat (TEST: `przetargi_ogloszenia` + `prawo_eli`)

Wystąpienia roku znajdowane regexem `(?<!\d)(20(?:1[5-9]|2[0-6]))(?!\d)`; każde
wystąpienie kodowane jako izolowany string (np. `"2024"`), średnia = tokeny/wystąpienia.

| Wielkość | R2 | R1 | Δ wzgl. | Wyjaśnienie |
|---|---:|---:|---:|---|
| TOKENIZATOREX, 2024 — średnia tokenów | 1.000000 | 1.000000 | +0.0000% | zgodne |
| TOKENIZATOREX, 2024 — wystąpienia | 163 | 162 | +0.6173% | regex R1 gubi `2020r.` itp. (§4.3) |
| TOKENIZATOREX, 2026 — średnia tokenów | 2.000000 | 2.000000 | +0.0000% | zgodne |
| TOKENIZATOREX, 2026 — wystąpienia | 1129 | 1128 | +0.0887% | regex R1 (§4.3) |
| Slayer1B, 2024 — średnia tokenów | 2.000000 | 2.000000 | +0.0000% | zgodne |
| Slayer1B, 2024 — wystąpienia | 163 | 162 | +0.6173% | regex R1 (§4.3) |
| Slayer1B, 2026 — średnia tokenów | 2.000000 | 2.000000 | +0.0000% | zgodne |
| Slayer1B, 2026 — wystąpienia | 1129 | 1128 | +0.0887% | regex R1 (§4.3) |

Wniosek H1 bez zmian: TOKENIZATOREX ma 1 token na 2024 i 2 tokeny na 2026;
Slayer1B ma 2 tokeny na oba lata. R1 ma identyczne średnie. Różnice dotyczą
wyłącznie liczników wystąpień (łącznie R2 2629 vs R1 2609; +0.77%).

## 3. H5 — NFD (pierwsze 25 dok. TEST na dziedzinę, sort po `id`)

Wzrost = `sum(tokeny NFD) / sum(tokeny baseline) - 1`, `unicodedata.normalize("NFD", text)`.

| Dziedzina | Tokenizer | R2 | R1 | Δ wzgl. | Wyjaśnienie |
|---|---|---:|---:|---:|---|
| przetargi_ogloszenia | TOKENIZATOREX | +56.1427% | +56.7963% | -1.1507% | inny podzbiór 25 dok. (14/25 wspólnych) |
| przetargi_ogloszenia | TOKENIZATOREX-HF | +56.2561% | +56.8785% | -1.0942% | inny podzbiór 25 dok. |
| przetargi_ogloszenia | Slayer1B | +42.5664% | +43.2032% | -1.4740% | inny podzbiór 25 dok. |
| przetargi_kio | TOKENIZATOREX | +64.3159% | +64.5408% | -0.3485% | inny podzbiór 25 dok. (12/25) |
| przetargi_kio | TOKENIZATOREX-HF | +64.2767% | +64.5084% | -0.3591% | inny podzbiór 25 dok. |
| przetargi_kio | Slayer1B | +52.6030% | +53.1748% | -1.0752% | inny podzbiór 25 dok. |
| samorzad_uchwaly | TOKENIZATOREX | +34.9373% | +35.9533% | -2.8260% | inny podzbiór 25 dok. (3/25) |
| samorzad_uchwaly | TOKENIZATOREX-HF | +35.0464% | +36.0647% | -2.8236% | inny podzbiór 25 dok. |
| samorzad_uchwaly | Slayer1B | +27.0519% | +28.1131% | -3.7748% | inny podzbiór 25 dok. |
| granty_ogloszenia | TOKENIZATOREX | +42.9448% | +47.9344% | -10.4092% | inny podzbiór 25 dok. (12/25) |
| granty_ogloszenia | TOKENIZATOREX-HF | +43.1214% | +48.0562% | -10.2688% | inny podzbiór 25 dok. |
| granty_ogloszenia | Slayer1B | +35.7868% | +40.5221% | -11.6858% | inny podzbiór 25 dok. |
| prawo_eli | TOKENIZATOREX | +47.5425% | +46.3677% | +2.5335% | inny podzbiór 25 dok. (9/25) |
| prawo_eli | TOKENIZATOREX-HF | +47.6391% | +46.4394% | +2.5833% | inny podzbiór 25 dok. |
| prawo_eli | Slayer1B | +38.8128% | +37.4958% | +3.5124% | inny podzbiór 25 dok. |
| ocr_prasa | TOKENIZATOREX | +34.2780% | +35.7575% | -4.1374% | inny podzbiór 25 dok. (18/25) |
| ocr_prasa | TOKENIZATOREX-HF | +34.2978% | +35.7642% | -4.1002% | inny podzbiór 25 dok. |
| ocr_prasa | Slayer1B | +31.3726% | +32.4934% | -3.4493% | inny podzbiór 25 dok. |
| tabele_json | TOKENIZATOREX | +36.1021% | +34.1021% | +5.8647% | inny podzbiór 25 dok. (14/25) |
| tabele_json | TOKENIZATOREX-HF | +36.2852% | +34.3090% | +5.7599% | inny podzbiór 25 dok. |
| tabele_json | Slayer1B | +31.1359% | +29.4471% | +5.7348% | inny podzbiór 25 dok. |

Agregat (średnia po 7 dziedzinach, tak jak publikuje R1):

| Tokenizer | R2 pooled | R2 mean | R1 mean | Δ (mean) |
|---|---:|---:|---:|---:|
| TOKENIZATOREX | +44.8493% | +45.1805% | +45.9217% | -1.6142% |
| TOKENIZATOREX-HF | +44.9428% | +45.2747% | +46.0029% | -1.5830% |
| Slayer1B | +37.4940% | +37.0470% | +37.7785% | -1.9362% |

Przyczyna różnic jest w 100% wybór dokumentów, nie arytmetyka: R1 losuje 25
dokumentów przez `np.random.default_rng(20261119).choice` (`audit/robustness.py:124-127`),
a R2 — zgodnie z poleceniem — bierze pierwsze 25 po `id`. Po odtworzeniu wyboru R1
(`audit/review/diag.py`) wszystkie 21 wartości zgadzają się **co do bitu**
(diff = 0.0e+00). Wspólnych dokumentów jest 3–18/25 w zależności od dziedziny.
Wniosek H5 bez zmian: NFD podnosi koszt o 27–64%, TOKENIZATOREX/HF rosną względnie
bardziej niż Slayer1B; wszystkie wartości > 25%.

## 4. H6 — superwordy „od środka słowa”

Definicja R2 (jawna, w `audit/review/run_h6.py`):

* superword = `b" " in vocab[t].lstrip(b" ")` (jak `is_superword`),
* „zaczyna się w środku słowa” = pierwszy segment (po usunięciu wiodących spacji,
  do pierwszej spacji) zawiera literę Unicode **i** nie jest samodzielnym słowem
  z korpusu TEST (zbiór wszystkich `text.split()` z 15 dziedzin TEST, bez zmiany
  wielkości liter),
* `share_slownik = podejrzane / wszystkie superwordy`,
* `share_uzycie = suma częstości podejrzanych / wszystkie wystąpienia tokenów`.

| Wielkość | R2 | R1 | Δ wzgl. | Wyjaśnienie |
|---|---:|---:|---:|---|
| superwordy w słowniku | 4922 | 4922 | 0.0000% | zgodne |
| udział superwordów w słowniku | 15.3817% | 15.3817% | 0.0000% | zgodne |
| „od środka” — udział w słowniku | 2.0114% (99) | 23.5677% (1160) | -91.4655% | inna, szersza definicja R1 (§4.1) |
| „od środka” — użycie / wszystkie wystąpienia | 0.0581% | 0.7991% | -92.7307% | ta sama przyczyna |
| „od środka” — użycie / wystąpienia superwordów | 0.8366% | 11.5083% | -92.7307% | ta sama przyczyna |
| wariant R2 bez wiodącej spacji | 1.9301% / 0.0581% | — | — | kontrola odporności definicji |
| wariant „R1 bez wiodącej spacji” | 13.1654% / 0.5926% | — | — | sama poprawka leading-space |

Uwaga: liczba użyć w korpusie zgadza się dokładnie (3 245 161), więc różnica nie
wynika z innego korpusu. Teza H6 mówi o 19.4%; R1 daje 23.6%, R2 2.0% — żadna
z tych dwóch definicji nie odtwarza 19.4%.

## 5. H8 — parytet HF (`przetargi_ogloszenia`, TEST)

Fragmenty `CHUNK_RE.findall(text)` z `superbpe.py`; identyczność =
`SuperBPETokenizer.encode_ordinary(chunk) == HF.encode(chunk, add_special_tokens=False).ids`.

| Wielkość | R2 | R1 | Δ wzgl. | Wyjaśnienie |
|---|---:|---:|---:|---|
| fragmenty | 48145 | 48145 | 0.0000% | zgodne |
| identyczne fragmenty | 47380 | 47380 | 0.0000% | zgodne |
| udział identycznych (po wystąpieniach) | 98.4110% | 98.4110% | 0.0000% | zgodne |
| tokeny ref / HF | 211560 / 211179 | 211560 / 211179 | 0.0000% | zgodne |
| delta HF − ref | -381 | -381 | 0.0000% | zgodne |
| delta względna | -0.1801% | -0.1801% | 0.0000% | zgodne |
| udział identycznych unikalnych fragmentów | 91.4787% | — | — | R2 dodatkowo (R1 nie publikuje) |

Parytet jest identyczny co do liczby. H8 w R1 nie ma błędu arytmetycznego.

---

## 4.1. Błąd/defekt H6 w rundzie 1 (blokujący)

**Plik/lines: `audit/superwords.py:63-74` (kryterium) oraz `audit/superwords.py:182-190` (status).**

1. **Tokeny z wiodącą spacją są liczone jako „zaczynające się w środku słowa”.**
   Linia 64 robi `s = texts[i].lstrip(" ")`, przez co informacja o wiodącej spacji
   znika. Tymczasem token zaczynający się od spacji zaczyna się na granicy słowa,
   a nie w środku. W liczbie 1160 „midword” R1 jest **512 tokenów (44.1%)**
   z wiodącą spacją; w `suspect_examples` widać np. `" to, co"`, `" różnego rodzaju"`,
   `" osób, które"`, `" ubiegłym roku"` — to całe słowa po spacji, nie sufiksy.
   Po prostym wykluczeniu wiodącej spacji (bez zmiany reszty kryterium) zostaje
   648/4922 = **13.1654%** słownika i **0.5926%** użyć, a nie 23.6% / 0.80%.

2. **Kryterium „nie jest samodzielnym słowem” jest przybliżone przez top 2000.**
   Linia 68: `first.lower() not in top_words`. To flaguje zwykłe, samodzielne słowa
   spoza top 2000 (np. `różnego` w `" różnego rodzaju"`, `osób` w `" osób, które"`).
   Metadane w liniach 150–152 deklarują dodatkowo warunek „nie wygląda na całe słowo”,
   ale funkcja `_looks_whole` (linie 208–213) **nigdy nie jest wywoływana** — to
   martwy kod i niezgodność metadanych z implementacją.

3. **Status H6 nie implementuje kryterium obalenia z protokołu.**
   Protokół (§7, H6): potwierdzenie = ≥10% słownika **i** ≥5% użyć; obalenie =
   <5% słownika **lub** <1% użyć; inaczej „niejasna”. Kod (linie 182–190) ustawia
   `confirmed = dict_ok and use_ok`, a potem `niejasna` gdy `dict_ok`, w przeciwnym
   razie `obalona`. Nie sprawdza gałęzi „użycie < 1%”. Przy własnych liczbach R1
   (słownik 23.57%, użycie 0.7991%) protokół daje **„obalona”** (0.7991% < 1%),
   a wynik R1 mówi **„niejasna”**. To błąd logiczny, nie tylko definicyjny.

**Oczekiwana poprawka:** (a) przy liczeniu „starts mid-word” jawnie odrzucać tokeny
`texts[i].startswith(" ")` albo raportować dwie liczby (z i bez wiodącej spacji);
(b) do warunku „samodzielne słowo” użyć pełnego zbioru słów korpusu TEST (lub progu
częstości << top 2000) i usunąć martwe `_looks_whole`; (c) status H6 policzyć
trójstanowo według protokołu, z osobną gałęzią obalenia (`dict < 5% or uses < 1%`).
Po poprawce (a)+(c) H6 = **obalona** również na danych R1 (13.17% słownika,
0.5926% użyć); po poprawce (b) dodatkowo 2.01% słownika.

## 4.2. Różnica H5 — nie błąd, lecz inny podzbiór dokumentów

R1 (`audit/robustness.py:124-127`) losuje 25 dokumentów przez
`np.random.default_rng(SEED).choice`, R2 bierze pierwsze 25 po `id` (wymóg rundy 2).
Po odtworzeniu losowania R1 w `audit/review/diag.py` wszystkie wartości NFD zgadzają
się do 0.0e+00 (21/21). Różnice w tabeli §3 (do 11.7% względem wartości R1) są
więc w pełni wyjaśnione i **nie zmieniają wniosku** (wszystkie wzrosty > 25%).
Nie blokuje.

## 4.3. Regex roku w H1 — drobny błąd zaniżający liczniki (nieblokujący)

**Plik/linia: `audit/notation_patterns.py:11` — `r"\b(?:19|20)\d{2}\b"`.**
W polskim tekście rok bywa zlepiony z literą (`"2020r."`, `"2022r."`); między
cyfrą a literą nie ma granicy `\b`, więc R1 gubi takie wystąpienia. W
`przetargi_ogloszenia` R1 ma 926 wystąpień, R2 946 (19 sztuk w latach 2015–2024
i 1 w 2026); w `prawo_eli` różnicy nie ma. Średnie tokenów na wystąpienie są
identyczne, więc H1 i `early_vs_late` bez zmian. Oczekiwana poprawka:
`(?<!\d)(?:19|20)\d{2}(?!\d)`. Nie blokuje.

---

## 5. Zgodność techniczna i odtwarzalność

* H9: `audit/review/r2lib.py` importuje `tokenizers` przed `sys.path.append(REPO)`;
  `run_h6.py` również importuje `tokenizers` przed `r2lib`. Brak `insert(0, ...)`.
* Wszystkie pięć liczb policzone na `split == "test"`; dokumenty ładowane z
  `audit/data/raw/<domain>/*.json`, sortowane po `id`.
* `TOKENIZATOREX`: `SuperBPETokenizer.load("tokenizers/tokenizatorex-32k.json")`,
  `encode_ordinary`; HF: `Tokenizer.from_file("hf/tokenizatorex-32k/tokenizer.json")`,
  `add_special_tokens=False`; Slayer1B:
  `audit/data/tokenizer_files/SlayerLab__Slayer1B-1.08.json`.
* `audit/review/compare.py` czyta JSON-y R1 tylko do porównania; nie modyfikuje
  plików rundy 1, `tokenizers/`, `hf/` ani `superbpe.py`.

---

```
REVIEW_RESULT
verdict: FAIL
blockers: H6 — (1) 44.1% tokenów oznaczonych jako „midword” ma wiodącą spację, czyli zaczyna się na granicy słowa; raportowane 23.6% nie jest miarą „starts in the middle of a word”; po samej poprawce leading-space 13.17% słownika i 0.59% użyć, po pełnym kryterium 2.01% / 0.058%; (2) status H6 (superwords.py:182-190) nie sprawdza obalenia „użycie < 1%”, więc z własnych liczb R1 (0.7991%) powinno być „obalona”, a jest „niejasna”.
notes: Fertility (9/9), H8 (wszystkie liczby) i średnie H1 2024/2026 odtwarzają się co do bitu. Różnice H5 do 11.7% w pełni wyjaśnione innym podzbiorem 25 dokumentów (R1: rng.choice; R2: pierwsze 25 po id; 21/21 wartości zgodnych po odtworzeniu wyboru R1) — nie zmieniają wniosku. H1: liczniki różnią się o 20 wystąpień z powodu `\b` w `notation_patterns.py:11` (gubi „2020r.”), średnie bez zmian — błąd drobny, nieblokujący. Poza H6 brak błędów arytmetycznych.
```

---

## Poprawka po recenzji (pętla 2)

Sprawdzany był **wyłącznie bloker H6**; pozostałych czterech liczb nie przeliczałem
ponownie (w rundzie 1 były zgodne). Weryfikacja: `audit/superwords.py:60-89`,
`audit/superwords.py:203-216` oraz `audit/results/superwords.json`, a niezależnie
`audit/review/verify_h6_fix.py` (własna implementacja kryterium na tym samym
korpusie TEST; wynik zapisany tylko na stdout).

**1. Błąd wiodącej spacji — naprawiony.** Kod jawnie sprawdza
`starts_with_space = raw.startswith(" ")` i wymaga `not starts_with_space`
(`superwords.py:68,73`). Niezależny skrypt potwierdza: w zbiorze `strict_lex5`
jest **0 tokenów z wiodącą spacją** (wcześniej 512/1160 = 44.1%).

**2. Błąd logiki statusu — naprawiony.** `superwords.py:203-210` implementuje
trójstan dokładnie według protokołu: `potwierdzona` przy `d >= 10% and u >= 5%`,
`obalona` przy `d < 5% or u < 1%`, inaczej `niejasna`. Dla primary
`d = 3.4539%`, `u = 0.0917%` kod poprawnie daje **`obalona`** (`confirmed: false`).
Uwaga: trzeci warunek potwierdzenia z protokołu (niepusta lista 100 dziwnych
tokenów) nie jest sprawdzany w kodzie, ale lista ma 100 pozycji, a przy tych
liczbach i tak aktywuje się gałąź obalenia; nie wpływa to na status.

**3. Zgodność JSON z kodem — pełna.** Niezależne przeliczenie dało identyczne
liczby (diff = 0 we wszystkich polach):

| Wariant | JSON / niezależnie: count | share słownika | usage share |
|---|---:|---:|---:|
| `strict_lex5` (primary) | 170 / 170 | 3.4539% | 0.0917% |
| `any_lex1` | 77 / 77 | 1.5644% | 0.0431% |
| `loose_top2000` | 648 / 648 | 13.1654% | 0.5926% |

Korpus się zgadza: 2752 dokumenty TEST, 3 245 161 użyć tokenów, 4922 superwordy.
`_looks_whole` został usunięty (brak wystąpień w pliku); metadane
`midword_criterion` opisują faktyczne kryterium (bez wiodącej spacji, pierwszy
segment z literą, forma spoza leksykonu ≥ 5, boilerplate wyłączony).

**4. Pozostała różnica względem moich liczb H6 — wyjaśniona definicją leksykonu.**
Moje pierwotne R2: 99/4922 = 2.0114% słownika i 0.0581% użyć, przy definicji
„pierwszy segment nie jest żadną formą z `text.split()` korpusu TEST (case-sensitive,
count ≥ 1)”. Poprawione R1 ma inne leksykony: `any_lex1` (formy literowe,
lowercase, count ≥ 1) = 77/1.5644%, a primary `strict_lex5` (te same formy, ale
count ≥ 5) = 170/3.4539%. Mój wynik 99 leży między nimi: mój zbiór form jest
bardziej restrykcyjny niż `any_lex1` (wielkość liter, interpunkcja), ale znacznie
bardziej permisywny niż próg count ≥ 5. To jest różnica **definicyjna**, nie błąd
ani niespójność implementacji; wszystkie warianty są raportowane.
Użycie pozostaje < 1% w każdym wariancie (0.0431–0.5926%), więc wniosek H6 nie
zależy od wyboru leksykonu.

**5. Wniosek H6 — teraz poprawny.** 19.4% z tezy nie jest odtwarzane: primary
3.45%, najbardziej liberalny wariant 13.17%. Nawet `loose_top2000` (13.17% ≥ 10%)
obala się na użyciu 0.593% < 1%; primary obala się dodatkowo na słowniku 3.45% < 5%.
Status **`obalona`** jest zgodny z protokołem, a użycie < 1% jest odporne na
wszystkie trzy definicje leksykonu.

Bloker H6 uznaję za rozwiązany. Wcześniejszy wpis `REVIEW_RESULT / FAIL` powyżej
pozostaje w historii jako stan przed poprawką; poniżej finalny wynik pętli 2.

```
REVIEW_RESULT
verdict: PASS
blockers: none
notes: H6 blocker resolved — leading-space excluded (0/170), status logic now follows the protocol and yields "obalona"; JSON matches an independent recomputation exactly for strict_lex5/any_lex1/loose_top2000 (170/77/648; 3.45%/1.56%/13.17% dict, 0.0917%/0.0431%/0.5926% usage). Remaining difference vs my earlier 99/2.0114%/0.0581% is fully explained by the lexicon definition (count >= 5 vs all corpus forms); usage <1% in every variant, so H6 is soundly refuted at the 19.4% scale. Other four R1 numbers were not recomputed in this loop; they matched in round 1.
```
