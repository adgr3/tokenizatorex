# RELEASE NOTES - TOKENIZATOREX v2.0

Status: WYDANE.

## Co to jest v2.0

v2.0 to stan po TKX-A + TKX-C + test domenowy na tekstach urzędowych (BZP, Dz.U. ELI, KIO, samorząd, granty, JSON narzędzi, kontrola ogólna). TOKENIZATOREX to SuperBPE: część tokenów łączy kawałki sąsiednich słów (superwordy), co obniża fertility, ale czasem tnie słowo w nienaturalnym miejscu (szczegóły i liczby w `tkx_v2/ZNANE_WADY.md`, sekcja W5).

### SuperBPE — ujawnienie

- TOKENIZATOREX to **SuperBPE**: część tokenów (superwordy) łączy kawałki sąsiednich słów. To obniża fertility, ale czasem tnie słowo w nienaturalnym miejscu.
- Superwordy w słowniku: **V0-32k 4982** (**15,57%** słownika), **V0J2-32k 4817** (**15,05%**). Zaczyna się w środku słowa: **V0 362** (**7,27%** superwordów), **V0J2 343** (**7,12%**); użycie superwordów: **V0 8,06%** tokenów, **V0J2 7,97%**; w tym od środka słowa: **V0 0,28%**, **V0J2 0,27%** (audyt H6 przeliczony na bieżących wariantach, `results/tkx_v2_r6_superwords.json`).
- Red team A: w 172 tekstach urzędowych granice od środka słowa wystąpiły w **13/172** (V0) i **12/172** (V0J2); w 384 parach słów **38/384** i **34/384**; w fuzzingu 20000 napisów **5** przypadków.
- Przykłady (V0/V0J2): `zgodność z` → `z | god | ność z`; `kolejność z` → `ko | lej | ność z`; `informacja z` → `informa | cja z`.
- **Plan v2.1:** superwordy tylko od początku słowa + pomiar kosztu (fertility/latencja).

## Wariant domyślny i kandydaci

Z danych (`results/tkx_v2_fertility.json`): **V0-32k ma najniższą fertility na wszystkich 8 źródłach** (punktowo). CI rozdzielają V0 od V3 wyraźnie tylko na części źródeł; Dz.U. i granty mają n=12, więc ranking jest niepewny.

**Przeciek (miara słowna):** żadne źródło nie przekracza progu 5% dokumentów >50% (najwyżej BZP 3,4% i web 1,9%); tło kalibracyjne na 789 dokumentach po dacie korpusu to 2,15% >50% i 0 exact. Teza o najniższej fertility nie wymaga korekty z powodu przecieku; wynik 13-gramów znakowych był artefaktem wspólnej polszczyzny (dodatek niżej).

### Fertility v2.0 (V0 vs V3 vs base vs Slayer)

| Źródło | Dokumenty | V0-32k | V3-32k | base-32k | Slayer1B-1.08 |
|---|---:|---:|---:|---:|---:|
| BZP (ogłoszenia) | 500 | 1,430 | 1,553 | 1,794 | 1,810 |
| Dz.U. 2026 ELI | 12 | 1,463 | 1,543 | 1,781 | 1,771 |
| KIO | 66 | 1,398 | 1,424 | 1,642 | 1,715 |
| Samorząd (uchwały) | 240 | 1,550 | 1,618 | 1,943 | 1,980 |
| Granty | 12 | 1,746 | 1,853 | 1,943 | 2,029 |
| JSON narzędzi (tc1) | 200 | 3,738 | 3,841 | 4,057 | 3,985 |
| Kontrola ogólna (HPLT web) | 421 | 1,412 | 1,435 | 1,582 | 1,672 |
| JSON BZP (tabele, extra) | 18 | 2,736 | 2,964 | 3,123 | 3,179 |

To tabela v2.0 (test domenowy, `results/tkx_v2_fertility.json` i `results/tkx_v2_r6_measure.json`); nie mylić ze starym benchmarkiem TKX-A w `README.md` (`results/benchmark.json`).

### Uczciwe porównanie: wariant bez superwordów (base-32k)

`TOKENIZATOREX-base-32k` (`tokenizers/tokenizatorex-base-32k.json`) to ten sam trening etapu 1 z **0 merge'ów etapu 2** (log `results/train-bpe-32k.log`: `etap2=0`), czyli ten sam korpus i ustawienia bez superwordów; nie jest to inny trening. Eksport HF zgadza się z plikiem własnym na próbce 100/100 dokumentów. Fertility z 95% CI, ta sama metoda co v2.0:

| Źródło | V0 | base | Slayer | APT3 | Bielik | GPT-4o |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| BZP (ogłoszenia) | 1,430 [1,422; 1,439] | 1,794 [1,783; 1,808] | 1,810 [1,800; 1,821] | 1,663 [1,654; 1,671] | 1,956 [1,943; 1,970] | 2,559 [2,548; 2,570] |
| Dz.U. 2026 ELI | 1,463 [1,364; 1,581] | 1,781 [1,687; 1,898] | 1,771 [1,683; 1,884] | 1,533 [1,462; 1,627] | 1,905 [1,789; 2,068] | 2,379 [2,302; 2,468] |
| KIO | 1,398 [1,374; 1,425] | 1,642 [1,615; 1,673] | 1,715 [1,686; 1,749] | 1,581 [1,555; 1,609] | 1,814 [1,775; 1,860] | 2,390 [2,370; 2,411] |
| Samorząd (uchwały) | 1,550 [1,538; 1,561] | 1,943 [1,930; 1,956] | 1,980 [1,965; 1,993] | 1,771 [1,757; 1,783] | 2,310 [2,292; 2,328] | 2,444 [2,430; 2,458] |
| Granty | 1,746 [1,674; 1,812] | 1,943 [1,869; 2,013] | 2,029 [1,960; 2,098] | 2,040 [1,872; 2,224] | 2,185 [2,069; 2,299] | 2,511 [2,476; 2,541] |
| JSON narzędzi (tc1) | 3,738 [3,624; 3,824] | 4,057 [3,941; 4,146] | 3,985 [3,881; 4,069] | 3,811 [3,707; 3,892] | 4,324 [4,198; 4,424] | 3,754 [3,692; 3,805] |
| Kontrola ogólna (HPLT web) | 1,412 [1,394; 1,430] | 1,582 [1,567; 1,598] | 1,672 [1,656; 1,690] | 1,557 [1,540; 1,574] | 1,661 [1,642; 1,681] | 2,189 [2,170; 2,209] |
| JSON BZP (tabele, extra) | 2,736 [2,561; 2,905] | 3,123 [2,919; 3,314] | 3,179 [2,983; 3,375] | 2,922 [2,745; 3,096] | 3,428 [3,202; 3,648] | 3,612 [3,442; 3,766] |

Bez superwordów base-32k zachowuje przewagę nad Slayerem na **6/8** źródeł (przegrywa na Dz.U. i JSON narzędzi), nad Bielikiem na **8/8**, ale nad APT3 tylko na **1/8**. Łącznie na 8 źródłach V0 ma **19,75%** mniej tokenów niż Slayer, a base **1,36%**; względem APT3 V0 **12,83%** mniej, base **7,14%** więcej; względem Bielika V0 **25,45%** mniej, base **8,36%** mniej.

**Domyślny wariant v2.0 = V0-32k.** Ma `§` jako 1 token i round-trip 0/700 na dokumentach.

**V3-32k = wariant eksperymentalny z cięciem cyfr.** Wygrywa na identyfikatorach, kodach pocztowych, numerach BZP, skrótach i sygnaturach w wzorcach; przegrywa na datach i kwotach; nie ma `§` jako jednego tokena; normalizuje NFD→NFC. O1 FAIL: 4/700 dokumentów (3 BZP + 1 KIO, wszystkie NFD; 4/500 BZP ma NFD); O2 PASS. Na źródłach testowych traci vs V0: BZP +8,54%, Dz.U. +5,43%, KIO +1,87%, samorząd +4,39%, granty +6,18%, JSON narzędzi +2,76%, JSON BZP tabele +8,35%, ogólny +1,68% (liczone z fertility w `results/tkx_v2_fertility.json`).

Ostateczny wybór dopiero po TKX-D (małe modele, BPB, ≥ 3 seedy). Fertility to warunek konieczny, nie dowód jakości (Schmidt i in.).

## TKX-ZOO — szersze porównanie tokenizerów

TKX-ZOO (gałąź `feat/tkx-zoo`, 17 tokenizerów): na 10 źródłach V0-32k wygrywa 6, V0J2-32k 4. Na 8 polskich źródłach żaden PLLuM ani Bielik nie jest tańszy od V0 (0 przypadków). Wśród nowych tokenizerów najbliżej V0 na BZP jest Aster-0.5B z fertility 1,731 przy V0 1,430. Szczegóły: `tkx_zoo/RAPORT.md` i `results/tkx_zoo_fertility.json`.

## Znane wady

Zob. `tkx_v2/ZNANE_WADY.md`. Uwaga: porównanie martwych tokenów ze Slayerem nie jest bezpośrednie (słownik polsko-angielski).

## Jak sprawdzić samemu

```bash
python scripts/sprawdz_sam.py "Twój tekst."
python scripts/sprawdz_sam.py --wszystkie "Twój tekst."
```

Domyślnie lokalne tokenizery TOKENIZATOREX + Slayer; `--wszystkie` dodaje zewnętrzne (wymaga cache/logowania).

## Nie sprawdzono (wprost)

- Bielik-1.5B-v3 (APT4) jest obecny w wynikach fertility; testy downstream nie wykonane. Tokenizer Bielika jest przeliczony w `results/tkx_v2_special_chars.json` i `results/tkx_v2_patterns.json` po zalogowaniu HF.
- Przeciek względem **całego** HPLT (poza próbką treningową tokenizera) — nie wykonano; poniżej jest pomiar względem faktycznego korpusu treningowego tokenizera.

### Przeciek względem korpusu treningowego tokenizera (13-gramy słowne)

Korpus: `audit/tmp/stability_train.txt` (HPLT p2, 400 MB), odtworzony z `audit/stability.py`; SHA-256 `b0e7447c…` zgodny z manifestem v21. Data korpusu ze źródła: kolumna `added` = **2026-07-14** dla wszystkich 159868 dokumentów próbki treningowej. V0 i V0J2 dzielą ten sam etap 1 i korpus, więc wynik jest dla nich wspólny. Próg zapisany przed pomiarem: dokument = przeciek, gdy > 50% jego unikalnych **13-gramów słownych** (NFC, lowercase, `split()`, 13 kolejnych słów) jest w korpusie treningowym albo cały dokument jest dokładnym podciągiem. Źródło: `results/tkx_v2_r6c_slowny_przeciek.json`.

| Źródło | Dokumenty | Exact | > 50% | Max | Po dacie korpusu |
|---|---:|---:|---:|---:|---:|
| BZP (ogłoszenia) | 500 | 0 | 17 | 71,7% | 500/500 |
| Dz.U. 2026 ELI | 12 | 0 | 0 | 1,6% | 7/12 |
| KIO | 66 | 0 | 0 | 2,2% | 66/66 |
| Samorząd (uchwały) | 240 | 0 | 0 | 18,7% | 92/240 |
| Granty | 12 | 0 | 0 | 2,9% | 2/12 |
| JSON narzędzi (tc1) | 200 | 0 | 0 | 0,0% | brak dat |
| Kontrola ogólna (HPLT web) | 421 | 0 | 8 | 80,9% | brak dat |
| JSON BZP (tabele, extra) | 18 | 0 | 0 | 2,9% | 0/18 |
| Granty (149) | 149 | 0 | 0 | 10,8% | 122/149 |
| JSON held-out (100) | 100 | 0 | 0 | 0,0% | brak dat |

BZP (główna liczba 1,43): publikacja **2026-11-01–2026-11-02**, wszystkie **500/500** dokumenty po dacie korpusu **2026-07-14**. Wynik słowny: **17/500** dokumentów > 50% (**3,4%**), exact **0**, max **71,7%**. To tło wspólnego szablonu BZP, nie kopie dokumentów.

**Kalibracja na tekście na pewno nowym** (data publikacji > 2026-07-14):

| Zbiór kontrolny | Dokumenty | > 50% | Max | Exact |
|---|---:|---:|---:|---:|
| wszystkie źródła z datami | 789 | 17 (2,15%) | 71,7% | 0 |
| BZP | 500 | 17 (3,40%) | 71,7% | 0 |
| KIO | 66 | 0 (0,00%) | 2,2% | 0 |
| Samorząd | 92 | 0 (0,00%) | 18,7% | 0 |
| Dz.U. | 7 | 0 (0,00%) | 1,6% | 0 |
| Granty 12 | 2 | 0 (0,00%) | 0,0% | 0 |
| Granty 149 | 122 | 0 (0,00%) | 10,8% | 0 |

Tło: **2,15%** dokumentów na pewno nowych ma > 50% 13-gramów słownych wspólnych z korpusem, exact 0; to wspólny język i szablony urzędowe, nie kopiowanie. Żadne źródło nie przekracza progu 5%.

### Dodatek: dlaczego 13-gramy znakowe myliły

13 znaków to około 2 słowa, więc miara znakowa mierzy wspólną polszczyznę, a nie kopiowanie dokumentów. W R6 dała ona BZP **500/500**, granty 149 **138/149** i web **299/421** dokumentów > 50%, przy 0 exact — mimo że granty 149 miały 122/149 dokumentów po dacie korpusu. To wystarcza, żeby uznać wynik znakowy za artefakt, a nie przeciek.

### Rényi (TokEval) i słowa pocięte na > 1 token

Efektywność Rényiego: α = 2,5 (jak TokEval; wyższe α mocniej karze ogon rozkładu), `H_α = 1/(1−α) · log2(Σ p_i^α)`, efektywność = `H_α / log2(|V|)`. „Słowa > 1 token” = odsetek słów (`\S+`) pokrytych przez więcej niż jeden token na offsetach. Dane: `results/tkx_v2_r6_measure.json`.

| Źródło | V0 | V0J2 | base | Slayer | APT3 | Bielik | GPT-4o |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| BZP (ogłoszenia) | 0,534 | 0,532 | 0,375 | 0,429 | 0,497 | 0,393 | 0,385 |
| Dz.U. 2026 ELI | 0,446 | 0,447 | 0,387 | 0,406 | 0,461 | 0,374 | 0,385 |
| KIO | 0,573 | 0,570 | 0,426 | 0,441 | 0,481 | 0,421 | 0,414 |
| Samorząd (uchwały) | 0,428 | 0,429 | 0,349 | 0,338 | 0,398 | 0,330 | 0,344 |
| Granty | 0,405 | 0,382 | 0,394 | 0,388 | 0,324 | 0,376 | 0,413 |
| JSON narzędzi (tc1) | 0,346 | 0,415 | 0,344 | 0,355 | 0,363 | 0,342 | 0,319 |
| Kontrola ogólna (HPLT web) | 0,560 | 0,561 | 0,458 | 0,467 | 0,527 | 0,462 | 0,440 |
| JSON BZP (tabele, extra) | 0,341 | 0,339 | 0,336 | 0,359 | 0,351 | 0,350 | 0,354 |

| Źródło | V0 | V0J2 | base | Slayer | APT3 | Bielik | GPT-4o |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| BZP (ogłoszenia) | 33,98% | 34,53% | 34,59% | 42,44% | 35,57% | 38,85% | 76,31% |
| Dz.U. 2026 ELI | 34,20% | 34,37% | 40,11% | 44,94% | 35,09% | 41,28% | 69,73% |
| KIO | 35,01% | 35,19% | 36,40% | 42,39% | 34,85% | 38,06% | 73,37% |
| Samorząd (uchwały) | 34,25% | 34,56% | 42,77% | 45,74% | 38,34% | 48,36% | 69,35% |
| Granty | 38,45% | 38,88% | 38,74% | 44,69% | 41,97% | 43,58% | 73,40% |
| JSON narzędzi (tc1) | 71,58% | 69,02% | 71,17% | 74,27% | 70,84% | 72,75% | 90,80% |
| Kontrola ogólna (HPLT web) | 34,82% | 35,12% | 34,23% | 39,49% | 35,34% | 36,26% | 74,36% |
| JSON BZP (tabele, extra) | 46,59% | 46,68% | 45,92% | 52,30% | 46,53% | 47,64% | 82,64% |

## Eksperyment v2.1-JSON (kandydat warunkowy V0J2-32k)

Dane: `results/tkx_v21_*.json` (gałąź `feat/tkx-v2-1-json`, cherry-pick do `feat/tkx-v2-0`). Reguła z protokołu: bramka JSON + brak regresji polskiego > 1% na 7 źródłach, `§` 1 token.

### Chronologia protokołu

Chronologia: protokół → trening → Poprawka 1 (po treningu, przed pomiarem; deklaracja) → pomiar → Poprawka 2 (po fakcie).

| etap | kiedy | co |
|---|---|---|
| Protokół | przed treningiem, commit `5d1e50d` | zapisany przed treningiem; reguła wyboru i test bez podglądania |
| Trening → Poprawka 1 | trening, potem Poprawka 1 po treningu, przed pomiarem (deklaracja) | warianty V0J2/V0J5/V0J10; held-out dostał osobne słownictwo; dane treningowe bez zmian |
| Pomiar → Poprawka 2 | pomiar dev/test po Poprawce 1, potem Poprawka 2 po fakcie | oryginalna reguła: brak kandydata; granty 149: kandydat warunkowy V0J2-32k (nie wybrany według protokołu) |

### Wynik według reguły oryginalnej (na pierwszym miejscu)

Wynik: **brak kandydata** (`results/tkx_v21_selection.json`: `winner = null`). V0J2-32k nie przeszedł bramki polskiej na grantach przy n=12 (reguła oryginalna).

### Poprawka 2 (granty 149)

Na grantach n=149 (`results/tkx_v21_selection_r2.json`): V0R 1,408412, V0J2 1,411248, delta +0,20% (próg ≤ 1%). CI 95% V0R [1,379812, 1,438095], V0J2 [1,382802, 1,440124]. Status: **kandydat warunkowy do TKX-D** (nie awans automatyczny).

### Zysk JSON (V0R vs V0J2, test)

Główna liczba to **JSON held-out -33,04%** (czysty: 0 exact i brak dokumentów > 50% pokrycia w korpusie treningowym JSON). tc1 -23,22% podajemy jako **górną granicę**: 91,0% dokumentów tc1 ma > 50% pokrycia 13-gramów z danych treningowych JSON (red team B, `results/tkx_v2_r6_redteam_b_odtworz.json`).

| Miara | V0R-32k | V0J2-32k | Zmiana |
|---|---:|---:|---:|
| JSON held-out (główna liczba, czysty) | 9,1819 | 6,1485 | -33,04% |
| JSON tc1 test (górna granica) | 3,7376 | 2,8699 | -23,22% |
| JSON tc1 (same wywołania, górna granica) | 4,8415 | 2,6698 | -44,86% |
| 10 wzorców JSON (suma tokenów) | 321 | 135 | -57,94% |
| 8 wzorców bez >50% pokrycia | 234 | 111 | -52,56% |

Przeciek wzorców: **częściowe pokrycie szkieletem** (2/10 > 50%, max 54,4%); 0 exact. Zysk na 10 wzorcach jest częściowo memorization wspólnego szkieletu, dlatego podany osobno dla 8 bez >50%.

### Held-out — rozbicie na formy

| Forma | Dokumenty | Tokeny V0 | Tokeny V0J2 | Zmiana |
|---|---:|---:|---:|---:|
| compact | 49 | 4034 | 2269 | -43,75% |
| pretty | 32 | 3212 | 2294 | -28,58% |
| result | 19 | 1284 | 1149 | -10,51% |
| razem | 100 | 8530 | 5712 | -33,04% |

Duża część zysku to wspólny szkielet wywołania (`<tool_call>`, `"name"`, `"arguments"`); na samych wynikach narzędzi zysk jest znacznie mniejszy.

### Koszt dla polskiego (V0J2 vs V0R, dev, delta %)

| Źródło | Delta % | Próg ≤ 1% |
|---|---:|---:|
| BZP ogłoszenia | +0,22% | TAK |
| Dz.U. ELI | +0,29% | TAK |
| KIO | -0,08% | TAK |
| Samorząd | +0,37% | TAK |
| Granty (n=149) | +0,20% | TAK |
| JSON BZP tabele | -1,32% | TAK |
| Ogólny web | +0,49% | TAK |

Tokeny specjalne (V0J5S) nie poprawiły wyniku względem V0J5 i nie dały kandydata; w 10 wzorcach JSON suma tokenów V0J5S to 144 vs V0J2 135 (`results/tkx_v21_wzorce.json`).

### Formaty dat, kwot i „§” — skrót

Pełne tabele per zapis: `tkx_v21/RAPORT.md`, sekcja 8a. Źródło: `results/tkx_v21_formaty.json` (40 dat, po 40 kwot na zapis, 9 form z „§”).

| Miara | V0 | V0J2 | V3 | Slayer | GPT-4o |
|---|---:|---:|---:|---:|---:|
| Daty (średnia) | 4,18 | 4,06 | 5,90 | 5,77 | 7,03 |
| Kwoty (średnia) | 5,56 | 5,41 | 4,94 | 6,27 | 5,83 |
| `§` (tokeny) | 1 | 1 | 2 | 1 | 1 |

Wniosek: po dodaniu JSON `§` pozostaje 1 tokenem w V0 i V0J2; średnia na datach V0J2 ≤ V0 + 0,1; kwoty bez istotnej zmiany. Kwoty dla „mln” i „tys.” są losowane w realistycznych zakresach (1–500 mln, 1–999 tys.).

## Koszt embeddingu i licencje

Słownik 32000 × d_model 768 = ok. **24,6 mln parametrów** (**16,4%** modelu 150M; przy osobnej macierzy wyjścia — dwa razy tyle: **49,2 mln = 32,8%**).

Wydajemy tylko tokenizer (bez wag modelu). Dane treningowe: HPLT v3 (pakowanie CC0 1.0; HPLT nie rości praw do tekstów) — https://hplt-project.org/datasets/v2.0 ; podzbiór SlayerLab/hplt-v3-pl-cleaned ma licencję 'other / hplt-v3-derived' — https://huggingface.co/datasets/SlayerLab/hplt-v3-pl-cleaned . Repo nie ma osobnego pliku LICENSE — do decyzji właściciela.

## Plan v2.1 i TKX-D

- v2.1: naprawa `§` (V3), skróty prawne, tokeny JSON; mieszanka 10–30% tekstów urzędowych.
- TKX-D: wybór wariantu i rozmiaru słownika (16k/24k/32k) na małych modelach; ≥ 3 seedy; BPB.

## Weryfikacja

`pytest -q` zielone. `python scripts/sprawdz_liczby_v2.py` exit 0 na wszystkich raportach. `python scripts/generuj_raporty_v2.py --check` nie zmienia plików. Liczby w raportach pochodzą z `results/tkx_v2_*.json` i `results/tkx_v21_*.json`. Weryfikacja przez człowieka wymagana.
