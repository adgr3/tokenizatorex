# TKX-V21-JSON — raport pełny

> Raport wygenerowany skryptem `tkx_v21/raport_v21.py` z `results/tkx_v21_*.json`. Seed 20261123, `PYTHONHASHSEED=0`, bootstrap 1000× po dokumentach. Pełne teksty korpusu są poza gitem (`data/`, `tkx_v21/dane/`).

## 1. Dziesięć zdań

1. Odtworzony V0 (`V0R-32k`) ma **identyczne merge'e etapu 1 i 2** co V0; liczba tokenów na BZP jest identyczna (2032561 vs 2032561), a SHA pliku różni się tylko metadanymi (`train_seconds`, `from`).
2. Na dev najniższą fertility JSON ma **V0J10-32k**: 2,9406 vs 3,9658 w V0R (-25,85%), ale nie przechodzi bramki polskiej.
3. Zysk na dev rozkłada się nierówno: tc1 (całe rekordy, narzędzia widziane) -23,96%, tc1 tylko wywołania+odpowiedzi -59,15%, held-out (narzędzia niewidziane) -33,80%.
4. Reguła wyboru **nie wskazała kandydata**. Najbliżej jest **V0J2-32k**: najgorsze źródło to granty +3,75% (n=12, CI 1,746–1,811 vs 1,674–1,812); pozostałe źródła: najwyżej +0,49%.
5. Koszt polszczyzny jest mały na 6 z 7 źródeł (od -1,32% do +0,49%); poza progiem wypada tylko granty (+3,75%), gdzie jest 12 dokumentów i szerokie CI.
6. Tokeny specjalne w V0J5S są atomowe (6/6), ale na tc1 test dają +0,22% tokenów względem V0J5 (same wywołania: +4,69%): `<tool_call>` jako granica dodanego tokenu przerywa część wyuczonych supertokenów.
7. „§” jest 1 tokenem w V0R: True; w każdym wariancie z domieszką JSON również: True.
8. Round-trip: 0 błędów na 700 przypadków (700 unikalnych tekstów); martwe tokeny w V0R: 8,11%.
9. Przeciek: **OK** — dokumentów >50% pokrycia 13-gramów: 0.
10. To pomiar kosztu tokenizacji, nie jakości modelu; ostateczny wybór wymaga TKX-D na małych modelach i co najmniej 3 seedach.

## 2. Odtworzenie V0

| co | V0 | V0R |
|---|---|---|
| SHA-256 superbpe | 7ba5543d4e09cfb0 | 616842c119d544d0 |
| merge'e etapu 1 równe | — | True |
| merge'e etapu 2 równe | — | True |
| tokeny na BZP (500 dok.) | 2032561 | 2032561 |
| fertility BZP | 1,4304 | 1,4304 |

**Wniosek:** identyczne merge'e; hash pliku rozni sie tylko metadanymi. Hash pliku różni się tylko polami meta: `train_seconds, from`. Porównania idą względem V0R.

## 3. Warianty

| wariant | SHA superbpe | SHA HF | dane treningowe |
|---|---|---|---|
| V0J2-32k | 90e6253627ec | 00b5537260c3 | data/mixed/V0J2-32k.txt |
| V0J5-32k | b2491a9fdfbe | e46ca54a4480 | data/mixed/V0J5-32k.txt |
| V0J10-32k | d73a56a4af63 | d28400dc215f | data/mixed/V0J10-32k.txt |
| V0J5S-32k | 6fedc0a45b18 | f758ac85f493 | data/mixed/V0J5-32k.txt |

Przepis: `train.py baseline --vocab 32000` → `train.py superbpe --transition 20000 --vocab 32000 --stage2-mb 100 --max-words 4`; V0J5S = V0J5 + 6 tokenów specjalnych (unikalne tokeny: 32004; `<tool_call>` i `</tool_call>` to istniejące tokeny słownika).

## 4. JSON — dev (wybór wariantu)

| tokenizer | tc1 dev | tc1 dev (tylko JSON) | held-out dev | łącznie dev | tokeny „§” |
|---|---|---|---|---|---|
| V0R-32k | 3,524 (3,309–3,714) | 5,136 (4,844–5,557) | 8,382 (7,346–9,697) | 3,9658 | 1 |
| V0-32k | 3,524 (3,309–3,714) | 5,136 (4,844–5,557) | 8,382 (7,346–9,697) | 3,9658 | 1 |
| V0J2-32k | 2,821 (2,704–2,928) | 2,714 (2,641–2,818) | 5,680 (5,141–6,369) | 3,0811 | 1 |
| V0J5-32k | 2,743 (2,629–2,845) | 2,528 (2,460–2,624) | 5,587 (5,061–6,264) | 3,0017 | 1 |
| V0J10-32k | 2,680 (2,578–2,771) | 2,098 (2,033–2,187) | 5,549 (5,033–6,205) | 2,9406 | 1 |
| V0J5S-32k | 2,748 (2,633–2,850) | 2,670 (2,583–2,797) | 5,730 (5,155–6,461) | 3,0193 | 1 |
| Slayer1B-1.08 | 3,790 (3,583–3,969) | 5,484 (5,235–5,835) | 7,075 (6,268–8,102) | 4,0881 | 1 |
| GPT-4o-o200k | 3,687 (3,557–3,797) | 4,879 (4,715–5,116) | 5,972 (5,366–6,757) | 3,8942 | 1 |

## 5. Reguła wyboru i wynik

| kandydat | fertility JSON dev | najgorszy koszt PL (źródło) | spełnia? |
|---|---|---|---|
| V0J2-32k | 3,0811 | +3,75% (granty) | NIE: granty |
| V0J5-32k | 3,0017 | +3,83% (granty) | NIE: granty, general_web |
| V0J10-32k | 2,9406 | +4,23% (granty) | NIE: bzp_ogloszenia, samorzad, granty, general_web |

**Wynik:** **brak kandydata**. brak kandydata spelniajacego warunek polski

Najbliżej progu jest **V0J2-32k**: najgorsze źródło to granty +3,75% (n=12); pozostałe źródła: najwyżej +0,49%. Przedziały 95% CI na granty pokrywają się z V0R — werdykt „brak kandydata” jest punktowy, zgodnie z protokołem, ale nie jest mocnym dowodem na regresję.

## 6. JSON — test (liczony raz, po wyborze)

| tokenizer | tc1 test | tc1 test (tylko JSON) | held-out test | łącznie test | tokeny/dok. tc1 |
|---|---|---|---|---|---|
| V0R-32k | 3,738 (3,624–3,824) | 4,842 (4,719–4,988) | 9,182 (7,913–10,683) | 3,9280 | 479,26 |
| V0-32k | 3,738 (3,624–3,824) | 4,842 (4,719–4,988) | 9,182 (7,913–10,683) | 3,9280 | 479,26 |
| V0J2-32k | 2,870 (2,814–2,915) | 2,670 (2,632–2,709) | 6,149 (5,477–6,977) | 2,9845 | 368,00 |
| V0J5-32k | 2,797 (2,744–2,840) | 2,524 (2,487–2,563) | 6,043 (5,386–6,864) | 2,9104 | 358,63 |
| V0J10-32k | 2,712 (2,666–2,750) | 2,128 (2,078–2,182) | 6,012 (5,369–6,818) | 2,8270 | 347,70 |
| V0J5S-32k | 2,803 (2,750–2,847) | 2,642 (2,598–2,691) | 6,215 (5,505–7,086) | 2,9224 | 359,44 |
| Slayer1B-1.08 | 3,985 (3,881–4,069) | 5,193 (5,091–5,313) | 7,705 (6,691–8,928) | 4,1149 | 510,95 |
| GPT-4o-o200k | 3,754 (3,692–3,805) | 4,682 (4,606–4,769) | 6,459 (5,702–7,371) | 3,8486 | 481,37 |

`tc1 test` = narzędzia widziane w tc1 train; `held-out test` = 10 narzędzi, których tokenizer nie widział. Różnica między nimi mówi, czy zysk przenosi się na nowe narzędzia.

## 7. Polski — pełna tabela (bramka)

Wartość: fertility z 95% CI / zmiana względem V0R.

| źródło | V0R-32k | V0-32k | V0J2-32k | V0J5-32k | V0J10-32k | V0J5S-32k | Slayer1B-1.08 | GPT-4o-o200k |
|---|---|---|---|---|---|---|---|---|
| BZP (ogłoszenia) | 1,430 (1,422–1,439) / +0,00% | 1,430 (1,422–1,439) / +0,00% | 1,434 (1,426–1,443) / +0,22% | 1,443 (1,435–1,452) / +0,86% | 1,460 (1,452–1,469) / +2,06% | 1,443 (1,435–1,452) / +0,86% | 1,810 (1,800–1,821) / +26,51% | 2,559 (2,548–2,570) / +78,88% |
| Dz.U. ELI | 1,463 (1,364–1,581) / +0,00% | 1,463 (1,364–1,581) / +0,00% | 1,468 (1,368–1,587) / +0,29% | 1,472 (1,374–1,588) / +0,60% | 1,475 (1,376–1,594) / +0,80% | 1,472 (1,374–1,588) / +0,60% | 1,771 (1,683–1,884) / +21,01% | 2,379 (2,302–2,468) / +62,56% |
| KIO | 1,398 (1,374–1,425) / +0,00% | 1,398 (1,374–1,425) / +0,00% | 1,397 (1,373–1,422) / -0,08% | 1,407 (1,383–1,433) / +0,62% | 1,411 (1,387–1,436) / +0,87% | 1,407 (1,383–1,433) / +0,62% | 1,715 (1,686–1,749) / +22,67% | 2,390 (2,370–2,411) / +70,91% |
| samorząd | 1,550 (1,538–1,561) / +0,00% | 1,550 (1,538–1,561) / +0,00% | 1,556 (1,544–1,566) / +0,37% | 1,557 (1,544–1,567) / +0,43% | 1,569 (1,556–1,579) / +1,20% | 1,557 (1,544–1,567) / +0,43% | 1,980 (1,965–1,993) / +27,71% | 2,444 (2,430–2,458) / +57,67% |
| granty | 1,746 (1,674–1,812) / +0,00% | 1,746 (1,674–1,812) / +0,00% | 1,811 (1,712–1,907) / +3,75% | 1,812 (1,714–1,907) / +3,83% | 1,819 (1,720–1,913) / +4,23% | 1,812 (1,714–1,907) / +3,83% | 2,029 (1,960–2,098) / +16,23% | 2,511 (2,476–2,541) / +43,83% |
| JSON BZP (tabele) | 2,736 (2,561–2,905) / +0,00% | 2,736 (2,561–2,905) / +0,00% | 2,700 (2,529–2,863) / -1,32% | 2,699 (2,530–2,859) / -1,33% | 2,717 (2,550–2,878) / -0,68% | 2,699 (2,530–2,859) / -1,33% | 3,179 (2,983–3,375) / +16,22% | 3,612 (3,442–3,766) / +32,02% |
| ogólny web | 1,412 (1,394–1,430) / +0,00% | 1,412 (1,394–1,430) / +0,00% | 1,419 (1,401–1,436) / +0,49% | 1,426 (1,408–1,444) / +1,01% | 1,432 (1,414–1,450) / +1,46% | 1,426 (1,408–1,444) / +1,01% | 1,672 (1,656–1,690) / +18,47% | 2,189 (2,170–2,209) / +55,03% |

## 8. Wzorce urzędowe (średnia liczba tokenów)

| kategoria | V0R-32k | V0-32k | V0J2-32k | V0J5-32k | V0J10-32k | V0J5S-32k | Slayer1B-1.08 | GPT-4o-o200k |
|---|---|---|---|---|---|---|---|---|
| adresy | 7,50 | 7,50 | 5,50 | 5,50 | 5,50 | 5,50 | 8,00 | 5,50 |
| CPV | 4,73 | 4,73 | 4,67 | 4,40 | 4,33 | 4,40 | 5,13 | 5,00 |
| daty ISO | 4,93 | 4,93 | 4,07 | 4,07 | 3,93 | 4,07 | 6,00 | 6,00 |
| daty słowne | 4,00 | 4,00 | 4,00 | 4,00 | 5,00 | 4,00 | 6,00 | 8,67 |
| identyfikatory | 8,13 | 8,13 | 7,87 | 8,20 | 7,53 | 8,20 | 7,53 | 6,87 |
| JSON narzędzi | 32,10 | 32,10 | 13,50 | 12,80 | 12,90 | 14,40 | 29,80 | 24,40 |
| kody pocztowe | 3,60 | 3,60 | 3,50 | 3,50 | 3,40 | 3,50 | 3,40 | 3,00 |
| kwoty | 5,27 | 5,27 | 5,33 | 5,33 | 5,33 | 5,33 | 6,33 | 6,20 |
| nazwy firm | 3,20 | 3,20 | 3,20 | 3,20 | 3,30 | 3,20 | 4,50 | 5,50 |
| numery BZP | 9,10 | 9,10 | 5,30 | 5,20 | 5,10 | 5,20 | 10,00 | 9,00 |
| skróty prawne | 4,40 | 4,40 | 4,25 | 4,25 | 4,25 | 4,25 | 5,60 | 6,35 |
| sygnatury | 6,30 | 6,30 | 4,90 | 4,90 | 4,80 | 4,90 | 6,60 | 7,00 |

10 wzorców JSON (`json_tool_calls`): V0R-32k=32,10, V0-32k=32,10, V0J2-32k=13,50, V0J5-32k=12,80, V0J10-32k=12,90, V0J5S-32k=14,40, Slayer1B-1.08=29,80, GPT-4o-o200k=24,40.

Segmentacja tekstowa dwóch przykładów JSON (tokeny HF, `Ġ` = spacja):

**W0126**
- V0R-32k (38 tok.): `<|to|ol|_|ca|ll|>|{|"|na|me|":|Ġ"|szukaj|",Ġ"|ar|gu|ments|":|Ġ|{|"|q|":|Ġ"prze|tar|g|"|}|}|<|/|to|ol|_|ca|ll|>`
- V0J2-32k (12 tok.): `<tool_call>{"name":|Ġ"|szukaj|",Ġ"|arguments":|Ġ{"|q|":|Ġ"prze|tar|g|"}}</tool_call>`
- Slayer1B-1.08 (33 tok.): `<|to|ol|_|call|>|{|"|name|":|Ġ"|szu|kaj|",|Ġ"|arg|uments|":|Ġ{"|q|":|Ġ"|prz|et|arg|"|}}|</|to|ol|_|call|>`

**W0129**
- V0R-32k (21 tok.): `{|"|k|wota|":|Ġ"|1|Ġ23|4,|56|ĠzÅĤ|",Ġ"|termin|":|Ġ"|202|6|-01|-02|"|}`
- V0J2-32k (11 tok.): `{"kwota":|Ġ"1|Ġ23|4,|56|ĠzÅĤ|",Ġ"termin":|Ġ"2026-|01|-02|"}`
- Slayer1B-1.08 (25 tok.): `{|"|kw|ota|":|Ġ"|1|Ġ23|4|,|56|ĠzÅĤ|",|Ġ"|termin|":|Ġ"|20|26|-|01|-|02|"|}`

## 9. Tokeny specjalne

1 = token atomowy; inna liczba = ile tokenów zajmuje napis.

| token | V0R-32k | V0-32k | V0J2-32k | V0J5-32k | V0J10-32k | V0J5S-32k | Slayer1B-1.08 | GPT-4o-o200k |
|---|---|---|---|---|---|---|---|---|
| <\|system\|> | 5 | 5 | 5 | 5 | 5 | 1 | 3 | 5 |
| <\|uzytkownik\|> | 8 | 8 | 8 | 8 | 8 | 1 | 6 | 8 |
| <\|asystent\|> | 7 | 7 | 7 | 7 | 7 | 1 | 5 | 7 |
| <\|narzedzie\|> | 7 | 7 | 7 | 7 | 7 | 1 | 6 | 7 |
| <tool_call> | 7 | 7 | 1 | 1 | 1 | 1 | 6 | 4 |
| </tool_call> | 8 | 8 | 1 | 1 | 1 | 1 | 6 | 4 |

## 10. Round-trip i martwe tokeny

| tokenizer | błędy round-trip | przypadki | błędy NFD | OK |
|---|---|---|---|---|
| V0R-32k | 0 | 700 | 0 | TAK |
| V0-32k | 0 | 700 | 0 | TAK |
| V0J2-32k | 0 | 700 | 0 | TAK |
| V0J5-32k | 0 | 700 | 0 | TAK |
| V0J10-32k | 0 | 700 | 0 | TAK |
| V0J5S-32k | 0 | 700 | 0 | TAK |
| Slayer1B-1.08 | 0 | 700 | 0 | TAK |
| GPT-4o-o200k | 0 | 700 | 0 | TAK |

| tokenizer | słownik | martwe | martwe % |
|---|---|---|---|
| V0R-32k | 32000 | 2595 | 8,11 |
| V0-32k | 32000 | 2595 | 8,11 |
| V0J2-32k | 32000 | 3035 | 9,48 |
| V0J5-32k | 32000 | 3479 | 10,87 |
| V0J10-32k | 32000 | 3736 | 11,68 |
| V0J5S-32k | 32004 | 3486 | 10,89 |
| Slayer1B-1.08 | 32768 | 11453 | 34,95 |
| GPT-4o-o200k | None | None | — |

## 11. Przeciek korpusu

| zbiór testowy | dok. | średnie pokrycie 13-g | maks. | >50% | exact |
|---|---|---|---|---|---|
| tc1_test | 200 | 12,2 | 33,1 | 0 | 0 |
| json_generic_test | 100 | 20,7 | 41,7 | 0 | 0 |

Status: **OK**. Pełne teksty i lista dokumentów: `results/tkx_v21_leak.json`.

## 12. Co to znaczy dla modelu 150M i TC-1

- Żadna domieszka nie przeszła bramki polskiej; to wynik, nie porażka: pokazuje, że 2–10% JSON kosztuje polszczyznę więcej niż 1%.
- Zysk na narzędziach niewidzianych jest osobną liczbą (held-out). Jeśli jest bliski zyskowi na tc1, tokenizer uczy się **składni JSON**, a nie nazw 3 narzędzi.
- Tokeny specjalne w V0J5S są atomowe (6/6), ale na JSON nie poprawiają wyniku (+0,22% tokenów na tc1 test względem V0J5): `<tool_call>` jako granica dodanego tokenu przerywa część wyuczonych supertokenów. To mechanizm dla szablonu czatu, nie dla słownika JSON.
- Decyzja o wdrożeniu należy do TKX-D: trening małych modeli, BPB, ≥ 3 seedy. Fertility nie jest jakością modelu.

## 13. Czego nie sprawdziły automaty

- Nie trenowano modeli 150M — nie wiadomo, czy mniejsza liczba tokenów przekłada się na lepsze wyniki na zadaniach TC-1.
- Dev/test JSON są syntetyczne (nasze), a tc1 pochodzi z jednego generatora; held-out narzędzia są inne, ale schematy mają wspólną składnię.
- Nie mierzono jakości na prawdziwych wywołaniach narzędzi produkcyjnych.
- Nie strojono hiperparametrów (2/5/10% to jedyne punkty); brak krzywej.
- UNKNOWN ≠ FALSE ≠ 0: brak źródła lub brak tokenizera jest raportowany osobno.

> Automatyczne testy i ten raport **nie są akceptacją właściciela**. Wymagana jest weryfikacja człowieka.

