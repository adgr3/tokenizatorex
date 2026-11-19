# Red team R3 — TOKENIZATOREX (niezależny przegląd)

Data pomiaru: 19.11.2026. Baza: `audit/tkx-a-19-11` @ `4a42cfe`. Gałąź robocza: `review/tkx-a-r3-grok`. Pliki tylko w `audit/review_grok/`. Skrypty rundy 1 i tokenizery nie były zmieniane.

Rola tego przeglądu: szukać miejsc, w których wniosek rundy 1 jest za mocny albo źle policzony. Liczby poniżej są z plików `audit/review_grok/r3_*.json`, chyba że zdanie wprost mówi, że pochodzi z raportu rundy 1 i nie było liczone od nowa.

Surowe teksty są w `audit/review_grok/raw_extra/` (poza gitem). W repozytorium są URL-e, SHA-256 i liczby. W przykładach nie ma treści dokumentów.

Import: skrypty ładują pakiet HF `tokenizers` zanim dopiszą katalog audytu do `sys.path` (`append`, nie `insert(0)`).

Werdykt przy ataku oznacza, co stało się z wnioskiem rundy 1: **zmienia wniosek**, **osłabia wniosek** albo **nie zmienia**.

## Atak 1. Jedno źródło na dziedzinę

**Werdykt: nie zmienia.**

Na zamrożonym teście ogłoszenia biorą się z jednego API BZP, KIO z uzasadnień UZP, uchwały z HTML dziennika śląskiego, granty z NIW. Do tego doszło po 40 publicznych dokumentów z innego źródła (seed `20261119`, próg 80 słów). Manifest: `r3_extra_manifest.json`. Fertility: `r3_extra_fertility.json`. Sumy czterech nowych źródeł, bez powtórki śląskiego PDF: `r3_extra_four.json`.

| Dziedzina | Źródło R3-extra | Kolejność fertility (mikro) | Najlepszy |
|---|---|---|---|
| Uchwały | PDF ELI Dolnego Śląska, nie Śląsk | HF 1,7200 · ref 1,7329 · APT3 1,7730 · Pollock 1,8288 · Slayer 2,0755 | HF |
| Ogłoszenia | TED, elementy XML z `languageID=POL` | HF 1,3335 · ref 1,3341 · Pollock 1,4491 · APT3 1,5031 · Slayer 1,6481 | HF |
| „KIO” | SAOS, pełny tekst orzeczenia, nie wycinek UZP | ref 1,3545 · HF 1,3550 · Pollock 1,4392 · APT3 1,4620 · Slayer 1,6444 | ref |
| Granty | strony konkursów NCN, nie NIW | HF 1,4844 · ref 1,4846 · Pollock 1,5712 · APT3 1,6841 · Slayer 1,7599 | HF |

Suma tych 160 dokumentów (773 286 słów): HF 1,4407, referencja 1,4431, Pollock 1,5370, APT3 1,5651, Slayer 1,7464. Referencja ma o 6,11% mniej tokenów niż Pollock, o 7,80% mniej niż APT3 i o 17,37% mniej niż Slayer. Na zamrożonym teście urzędowym było to −6,1%, −9,6% i −17,0%. Przewaga wobec Pollocka i Slayera zostaje. Na NCN Pollock już nie wygrywa (na NIW wygrywa). To jest inne źródło, nie zaprzeczenie wyniku NIW.

Zastrzeżenia, które nie odwracają kolejności:

- Slugi NCN w manifeście mają rok 2012 (6), 2013 (3), 2014 (3), 2015 (1), 2020 (1), 2027 (2); 24 identyfikatory nie mają roku. Filtr strony łapał rok ze stopki, więc to nie jest czysty zbiór 2024–2026. Nadal nie jest to NIW. Licznik: `r3_doc_lengths_extra.json`, pole `ncn_year_in_id`.
- W 5 z 40 plików TED występuje napis `ezamowienia`, w 0 napis `BZP`. To sygnał wspólnego gatunku, nie dowód, że to te same postępowania.
- Dolny Śląsk ma krótką medianę (360 słów) i długi ogon (maks. 58 482 słowa). Mikrośrednia jest ciągnięta przez długie akty. Makrośrednia HF to 1,5830, a APT3 (1,7463) jest wtedy za Pollockiem (1,6937). Zwycięzca przy obu średnich to HF.
- Skrypt pomija PDF większe niż 4 MB, więc najdłuższe akty dolnośląskie mogą być nieobecne.
- Orzeczenia SAOS mogą zawierać nazwiska. Tekst zostaje w `raw_extra/` i nie jest cytowany.

Katalog `samorzad_slask_pdf` w tym samym JSON to pełny PDF zamrożonych uchwał śląskich. Nie wchodzi do sumy R3-extra. Jest w ataku 2.

## Atak 2. Przycięcie do 20 tys. znaków

**Werdykt: osłabia wniosek.**

Odbudowa z lokalnego cache, ta sama ekstrakcja co runda 1, bez `[:20000]`: `r3_rebuild_stats.json`, fertility `r3_full_vs_trunc.json`.

| Dziedzina | Znaki testu | Po odbudowie | Prefiks się zgadza | Top-1 po zdjęciu progu |
|---|---:|---:|---:|---|
| Ogłoszenia BZP | 1 057 364 | 1 524 641 | 60/60 | HF, bez zmiany |
| KIO | 696 320 | 996 620 | 66/66 | ref, bez zmiany |
| Uchwały HTML | 454 064 | 454 064 | 240/240 | HF, bez zmiany |
| Granty NIW | 798 796 | 2 579 167 | 66/66 | Pollock, bez zmiany |
| Prawo ELI | 947 209 | 4 360 113 | 12/78 | HF, bez zmiany |
| OCR, 6 skanów | 594 523 | 1 426 186 | 36/36 | HF, bez zmiany |
| Tabele JSON | 489 109 | 517 864 | 0/60 | HF, bez zmiany |

Na żadnej dziedzinie top-1 się nie zmienia. Próg 20 tys. znaków nie jest więc źródłem zwycięstwa TKX. Osłabienie jest gdzie indziej.

Uchwały w ogóle nie były ucięte tym progiem (0 dokumentów na capie, znaki bez zmiany). `text.html` dziennika śląskiego to zwykle pierwsza strona. Ta sama czterdziestka aktów, PDF zamiast HTML (`r3_slask_pdf.json`, 3 PDF pominięte, w tym te ponad 4 MB): HTML ma 72 102 znaków i 11 522 słowa, PDF 458 910 znaków i 71 177 słów (mediana stosunku znaków PDF/HTML 5,79).

| | HTML (strona 1) | Pełny PDF |
|---|---:|---:|
| HF | 1,5295 | 1,8492 |
| ref | 1,5338 | 1,8542 |
| APT3 | 1,7831 | 1,8644 |
| Pollock | 1,7779 | 1,9628 |
| Slayer | 2,0060 | 2,2297 |

Kolejność na HTML: HF, ref, Pollock, APT3, Slayer. Na PDF: HF, ref, APT3, Pollock, Slayer. Zwycięzca zostaje. Luka referencji do APT3 spada z około 14% do 0,55% (HF do APT3: 0,82%). Oba wyniki są poniżej progu 1% z protokołu rundy 1. To jest mikrośrednia (suma/suma), czyli miara audytu, ciągnięta przez długie akty. Makrośrednia na tym PDF nadal daje APT3 o 5,4% więcej tokenów niż HF (1,7823 wobec 1,6911). Bez bootstrapu nie nazywam tej mikro-luki remisem statystycznym. Nazywam ją luką mniejszą niż próg, który audyt sam uznał za istotny. Wniosek „uchwały są wyraźną wygraną TKX” jest za mocny, jeśli akt czyta się w całości.

Granty NIW po zdjęciu progu: Pollock 1,7529, HF 1,7604 (+0,43% tokenów wobec Pollocka), referencja 1,7714 (+1,06%). Na tekście uciętym referencja była gorsza o 0,58%, HF o 0,17%. „Praktyczny remis” przy progu 1% zostaje dla HF. Dla referencji punktowo już go nie ma. Nie liczyłem przedziału ufności.

OCR bez progu 20 tys., nadal tylko pierwsze 6 skanów ALTO: fertility HF rośnie z 1,9151 do 2,0189. Luka do Pollocka (2,0443) to 1,2%. Kolejność bez zmiany.

Prawo: 12/78 dokumentów ma ucięty tekst jako prefiks pełnego. Runda 1 czyści białe znaki samego PDF, a dopiero potem dokleja tytuł. Odbudowa czyści całość. To nie jest czyste „dopisz ogon”. Znaki rosną 4,6 raza i kolejność zostaje (HF 1,4453 wobec Pollocka 1,5109).

Tabele JSON: 2/60 dokumentów testu jest na capie, a prefiks nie zgadza się w żadnym. Zapis rundy 1 to JSON z wcięciem dwóch spacji. Odbudowa puszcza ten JSON przez `clean_text`, które zdejmuje wcięcie. Spadek fertility 2,6294 → 2,5717 nie jest czystym efektem progu. Kolejność bez zmiany. Osobno: tabele biorą się z tego samego API BZP co ogłoszenia (`collect_bzp(..., as_json=True)`). To nie jest siódma, niezależna dziedzina.

## Atak 3. Eksport HF i round-trip

**Werdykt: nie zmienia.**

`r3_roundtrip.json`: 1010 dokumentów urzędowych, wszystkie splity, bez dokładania korpusu web.

| Tokenizer | `decode(encode(x)) == x` |
|---|---:|
| TOKENIZATOREX, HF, base, Slayer, Pollock, Bielik, PLLuM, GPT-4o | 1010/1010 |
| APT3 | 6/1010 |

HF ma mniej tokenów niż referencja i nie gubi znaków. Na tych 1010 dokumentach: referencja 1 961 983 tokeny, HF 1 957 010 (−0,25%). Na zamrożonym teście (606 dok., `r3_fairness.json`): 1 153 793 wobec 1 151 140 (−0,23%), fertility 1,6825 wobec 1,6787. Ranking liczony tak, jak model będzie kodował, czyli HF: na agregacie urzędowym HF, potem referencja, Pollock, APT3, base, Slayer, GPT-4o, PLLuM, Bielik.

APT3 na teście: dokładny round-trip w 0,50% dokumentów, tekst po decode jest dłuższy o 1,34% (5 037 385 → 5 104 862 znaków), nie krótszy. Na wszystkich 1010: +115 302 znaki na niedopasowanych. Klasy znaków (licznik, bez wyrównania napisów): ubyło 30 466 znaków spoza ASCII i 150 innych białych znaków, przybyło 145 768 znaków ASCII i 150 spacji. To wygląda jak NFKC (rozbicie / podstawienie), nie jak wycięcie spacji. Fertility APT3 1,8612 jest liczona na słowach tekstu źródłowego.

Wniosek rundy 1 zostaje: eksport nie jest 1:1 z referencją i trening musi używać jednego enkodera. Dopisek: różnica nie jest utratą znaków ani spacji.

## Atak 4. Bajty na token i ranking bez APT3

**Werdykt: osłabia wniosek.**

Na tym samym tekście suma bajtów UTF-8 jest stała, suma słów też. Kolejność bajtów na token (wyżej = lepiej) jest wtedy odwrotnością kolejności liczby tokenów, a więc i fertility. To tożsamość, nie drugi eksperyment. `r3_fairness.json` ma obie listy identyczne, z APT3 i bez.

Agregat testu urzędowego, fertility i bajty/token:

| | fertility | bajty/token |
|---|---:|---:|
| HF | 1,6787 | 4,5860 |
| ref | 1,6825 | 4,5755 |
| Pollock | 1,7921 | 4,2956 |
| APT3 | 1,8612 | 4,1361 |
| base | 1,9657 | 3,9163 |
| Slayer | 2,0265 | 3,7989 |

Wyłączenie APT3 nie zmienia czołówki: HF, referencja, Pollock. Zdanie o −6,1% wobec Pollocka i −17,0% wobec Slayera na tym teście się zgadza co do liczby. Osłabienie dotyczy zdania o odporności: oś „tokeny albo bajty” w red teamie rundy 1 nie jest osobną osią. Inna jednostka zmienia kolejność dopiero wtedy, gdy ktoś liczy bajty tekstu po stratnym decode. Tego nie robię dla APT3 jako podstawy rankingu, bo decode nie jest tym samym tekstem.

## Atak 5. Rényi

**Werdykt: zmienia wniosek.**

Runda 1 podaje `exp(H_α)/|V|` przy α = 2,5 i nazywa 7,4‰ najmocniejszą przewagą inżynierską wobec Slayera (2,7‰) i Pollocka (1,6‰). W `audit/vocab_usage.py` tak właśnie liczone jest `renyi_efficiency`. Zouhar i in. (2023, arXiv 2306.16842, *Tokenization and the Noiseless Channel*) używają efektywności `H_α / log|V|`, czyli `H_α / H_0`. Rysunek 2 w tej pracy ma oś `H2.5/H0`. Związek `exp(H)/|V| = |V|^(eff − 1)` nie zachowuje porządku między słownikami o różnym `|V|`.

Te same zliczenia, test, 15 dziedzin, 2752 dokumenty (`r3_renyi.json`):

| Tokenizer | \|V\| | martwe | audyt `exp(H)/\|V\|` | Zouhar `H/log\|V\|` |
|---|---:|---:|---:|---:|
| APT3 | 31 980 | 843 | 0,007680 | 0,5306 |
| TOKENIZATOREX | 32 000 | 571 | 0,007424 | 0,5273 |
| HF | 32 000 | 584 | 0,007402 | 0,5271 |
| Bielik-v3 | 32 128 | 12 346 | 0,004359 | 0,4762 |
| base | 32 000 | 702 | 0,003164 | 0,4451 |
| Slayer | 32 768 | 2 907 | 0,002693 | 0,4309 |
| PLLuM | 131 072 | 95 095 | 0,001327 | 0,4378 |
| GPT-4o | 200 019 | 157 796 | 0,000958 | 0,4306 |
| Pollock | 49 152 | 4 596 | 0,001566 | 0,4021 |

Kolejność czołówki jest ta sama przy obu wzorach: APT3, potem TKX, potem HF. APT3 wygrywa metrykę, którą raport nazywa przewagą TKX. Pominięcie APT3 w tym zdaniu nie jest uzasadnione tym, że APT3 jest stratny: metryka i tak jest liczona na identyfikatorach tokenów, nie na wierności napisu. Luka TKX do Pollocka wygląda na 4,74 raza przy wzorze audytu (0,007424 / 0,001566) i na 1,31 raza przy wzorze Zouhara (0,5273 / 0,4021). Pollock jest przy wzorze audytu przed PLLuM i GPT-4o, a przy wzorze Zouhara jest ostatni. `rank_changed` w pliku jest prawdziwe.

Literatura nie pozwala nazwać tej liczby najmocniejszą przewagą inżynierską.

- Zouhar i in., tabela 1: korelacja Pearsona efektywności Rényiego z Bleu 0,78 (p < 0,001), Spearmana 0,66 (p < 0,001), α dobrane do około 2,5. Długość sekwencji: Pearson −0,32 (p = 0,118). Abstrakt mówi o niemieckim→angielskim i 1 mln zdań CommonCrawl. Sekcja 6 tej samej pracy mówi o angielskim→niemieckim CommonCrawl. Kierunek w źródle jest niespójny; korelacja z tabeli 1 jest spójna.
- Cognetta, Zouhar, Moon i Okazaki, arXiv 2402.14614 (pierwsza wersja 2024-02-22, poprawka 2024-02-29), *Two Counterexamples to Tokenization and the Noiseless Channel*. Wzór w pracy to `Eff_α = H_α / log|V|`. Eksperymenty liczą α = 3 (domyślne ustawienie `tokenization-scorer`), nie 2,5. Duplicate BPE we wszystkich opisanych ustawieniach podnosi efektywność Rényiego i obniża Bleu o co najmniej 1 punkt. W ustawieniu 4k/4k, N = 500, k = 5 model nie zszedł się: 10 prób, żadna nie przekroczyła 5 Bleu. Random-Drop w tekście pracy ma dwa sformułowania: przy losowaniu z całego słownika średnie Bleu bywa wyższe, a przy ograniczeniu do 2000 najczęstszych tokenów modele są gorsze od bazy; w dopisku ze słownikiem powiększonym o tyle, ile tokenów wyrzucono, efektywność rośnie, a wynik spada. Nie przepisuję komórek tabel, których nie mam w całości.

Martwe tokeny TKX 571/32 000 = 1,8% zgadzają się z raportem. Ta część zdania zostaje. „Najmocniejsza przewaga inżynierska” nie zostaje. Rényi nie powinno wybierać wariantu TKX-C.

## Atak 6. Kontekst 2048

**Werdykt: nie zmienia.**

Zdanie rundy 1 o przetargu: mediana 3780 tokenów, 1,7% dokumentów mieści się w 2048. Na uciętym teście, tokeny HF (`r3_context_truncated.json`): mediana 3775, p90 4114, w 2048 mieści się 1,7%, w 4096 mieści się 88,3%. To jest ten sam wniosek. 3780 było liczone na tekście uciętym do 20 tys. znaków. Po odbudowie (`r3_context_full.json`) mediana ogłoszenia to 3984, p90 7396, maks. 30 146. W 2048 nadal mieści się 1,7%. W 4096 mieści się już tylko 53,3%. Mediana KIO zostaje 1666 (ogon: p90 z 3918 do 6612). Mediana grantu zostaje 2336, ale p90 rośnie z 4899 do 22 593, a średnia z 2717 do 8790.

Uchwały HTML: mediana 464, p90 589, w 2048 mieści się 100%. To jest pierwsza strona. Pełny PDF tej samej próby śląskiej (`r3_doc_lengths_extra.json`): mediana 2402,5 tokenu HF, p90 7408, w 2048 mieści się 40%, w 4096 mieści się 72,5%, maks. 14 952. Dolny Śląsk (inne źródło, dużo krótkich aktów): mediana 570, p90 4373, w 2048 mieści się 82,5%. Średnia 6449 jest tu myląca, bo jeden akt ma 100 964 tokeny.

Szacunek „każda cyfra osobnym tokenem” nie jest tokenizerem nauczonym od nowa. Dolna granica dokłada `max(0, cyfry_w_tokenie − 1)` do dzisiejszej długości. Górna liczy każdą cyfrę jako token i resztę tego samego tokenu jako jeden token, jeśli nie jest samymi cyframi. Pełne ogłoszenie BZP, HF:

| | mediana | w 2048 | w 4096 |
|---|---:|---:|---:|
| dziś | 3984 | 1,7% | 53,3% |
| dolna granica cyfr | 4239 | 1,7% | 45,0% |
| górna granica cyfr | 4646 | 0% | 33,3% |

Sonda syntetyczna, nie z korpusu (`r3_doc_lengths_extra.json`): `w roku 2024 r. zadanie` ma 4 tokeny, w tym jeden token ` 2024 r.`. To samo dla 2015. Dla 2025, 2026 i 2027 jest 5 tokenów: ` 202` i `5 r.` (albo `6 r.`, `7 r.`). Referencja i HF dają to samo, round-trip się zgadza. Zdanie o zamrożonym kalendarzu zostaje.

Co z tego wynika dla modelu 150M z oknem 2048:

- Typowe ogłoszenie nie mieści się w jednym oknie ani dziś, ani po zdjęciu progu 20 tys. znaków. 4096 mieści medianę pełnego ogłoszenia (3984) i około połowy dokumentów, nie mieści p90 (7396). Po rozbiciu cyfr górny szacunek mediany (4646) wychodzi poza 4096.
- Uchwała „mieści się w całości” tylko jako pierwsza strona HTML. Mediana pełnego aktu śląskiego z tej próby jest tuż nad 2048.
- Pamięć uwagi rośnie z kwadratem długości. Przy tej samej liczbie sekwencji w batchu okno 4096 to około cztery razy tyle aktywacji uwagi co 2048. Przy stałym budżecie tokenów na krok w batchu jest dwa razy mniej dokumentów. Nie mierzyłem VRAM ani czasu kroku.
- Cięcie na kawałki po 2048 jest konieczne dla ogona i tak. Kawałek gubi więź między kwotą a warunkiem, jeśli wpadną do różnych okien. To argument jakościowy, nie wynik treningu.

Wniosek „1,7% ogłoszeń mieści się w 2048” zostaje. Trzeba go czytać jako własność tekstu już uciętego i jako dolne ograniczenie problemu, nie jako opis pełnego PDF.

## Atak 7. Czego audyt nie dociążył przy modelu 150M

**Werdykt: zmienia wniosek.**

Chodzi o kryterium sukcesu, nie o kolejność fertility na zamrożonym teście. Fertility i Rényi nie mówią, czy model 150M przeczyta akt.

1. Pojedyncze cyfry podniosą fertility, czyli metrykę, którą audyt minimalizował. Górny szacunek na pełnym ogłoszeniu to +16,6% tokenów (3984 → 4646), dolny +6,4% (→ 4239). Nadzieja „−1 token na nowy rok” dotyczy dzisiejszego zlepka `2024 r.`, nie świata, w którym każda cyfra jest osobno. Wtedy stary rok też drożeje. Sukces TKX-C to ten sam koszt dla 2024 i 2027 oraz świadomie przyjęty wzrost liczby tokenów, a nie spadek fertility.
2. Uchwała w ewaluacji to pierwsza strona. Na pełnym PDF luka do APT3 spada poniżej 1% w mikrośredniej (atak 2), a mediana długości wychodzi z okna 2048 (atak 6).
3. `tabele_json` to to samo API BZP co ogłoszenia. „7 dziedzin, wygrana na 6” liczy jeden strumień dwa razy.
4. Bajty na token nie są osobnym testem odporności (atak 4). Rényi w postaci z raportu nie jest metryką Zouhara i na tych danych wygrywa je APT3 (atak 5).
5. Słownik 32 000 przy `d_model` 768 to 24 576 000 parametrów embeddingu, czyli 16,4% modelu 150M. Próba 16k / 24k / 32k bez zadania docelowego wybierze większy słownik, bo fertility zwykle spada, a połowa tej różnicy parametrów siedzi w embeddingu. Brakuje choćby proxy: długość sekwencji na stałym korpusie plus udział embeddingu. Nie trenowałem tych słowników.
6. Ogon pełnych dokumentów jest poza każdym oknem, które dziś jest w planie. Grant NIW: p90 22 593 tokenów HF. Prawo ELI: p90 35 118, z zastrzeżeniem że odbudowa nie jest czystym prefiksem (12/78). OCR przy sześciu skanach: p90 28 758. Okno 2048 widzi wtedy mały początek pliku.
7. SuperBPE skleja rok ze skrótem (` 2024 r.` jako jeden token). Reguła „`r.` osobno” i reguła „cyfra osobno” wchodzą sobie w drogę. Po zmianie trzeba powtórzyć sondę z ataku 6, nie tylko fertility.
8. APT3 na tym korpusie nie jest „krótszy, bo zgubił znaki”. Jest dłuższy po decode i prawie nigdy nie wraca do tego samego napisu. Porównanie fertility z APT3 na tekście urzędowym miesza kompresję z inną treścią. Pollock, Slayer, Bielik, PLLuM i GPT-4o round-trip na tych 1010 dokumentach trzymają.
9. **Hipoteza.** Cięcie aktu na kawałki 2048 psuje zadania, w których kwota, termin i podstawa prawna są daleko od siebie. Fertility tego nie zobaczy. Nie mierzyłem tego zadania, bo nie ma modelu.
10. **Hipoteza.** CAPS +106,8% i NFD +45,9% z raportu rundy 1 (tu nie liczone od nowa) uderzą w ogłoszenie pisane wersalikami i w PDF o rozbitej normalizacji mocniej niż różnica TKX wobec Pollocka (−6%). NFC w potoku jest potrzebne. Samo NFC nie rusza wersalików.

## Wnioski z `RAPORT_SLABOSCI.md`

| # | Zdanie | Po tym przeglądzie |
|---|---|---|
| 1 | Na 7 dziedzinach urzędowych TKX najlepszy na 6, remis na 1; zbiorczo 1,6825 wobec Pollocka −6,1% | Liczba 1,6825 i −6,1% na zamrożonym teście się zgadzają. „Remis” grantów zostaje dla HF (+0,43% na pełnym NIW). Referencja na pełnym NIW jest gorsza o 1,06% (bez CI). Uchwały w tej liczbie to pierwsza strona. Cztery nowe źródła dają wobec Pollocka −6,11%, ta sama skala. |
| 2 | Na 15 dziedzinach najlepszy na 11; Wikipedia, nauka, angielski | Nie liczone od nowa. Zostawiam jako wynik rundy 1. |
| 3 | Kalendarz zamrożony: 2015–2024 to 1 token, 2025–2026 to 2; zdanie ma 4 albo 5 tokenów | Potwierdzone sondą, także dla 2027 i dla HF. Zostaje. |
| 4 | Zapisy urzędowe tanie, ale niestabilne (12,8–57,1%) | Nie liczone od nowa. |
| 5 | NFD +45,9%, CAPS +106,8%, tytuły +30,6% | Nie liczone od nowa. Przy modelu 150M to nadal większy problem niż spór o 1% fertility. |
| 6 | HF nie jest 1:1; różnice do −0,52% tokenów | Różnica liczby tokenów jest prawdziwa (−0,23% na teście) i nie jest utratą znaków (1010/1010). Jeden enkoder przy treningu i ocenie zostaje. |
| 7 | Słownik zdrowy, Rényi 7,4‰ to najmocniejsza przewaga inżynierska | 1,8% tokenów martwych zostaje. Reszta zdania do skreślenia: APT3 ma 0,00768 wobec 0,00742, a wzór nie jest efektywnością Zouhara. |
| 8 | H6 obalona w skali: użycie „od środka słowa” 0,04–0,59% | Nie liczone od nowa. |
| 9 | Ranking odporny na 30 kombinacji, w tym tokeny/bajt; boilerplate <0,5% | Kolejność top-1 po zdjęciu APT3 i po zmianie jednostki na bajty się nie zmienia, bo bajty są tożsamością. Ta oś odporności jest pusta. Boilerplate nie był tu liczony od nowa. |
| 10 | Nie mierzono jakości modelu 150M; fertility to nie jakość | Zostaje. Ten przegląd też nie trenował modelu. |

## TKX-C: co w zaplanowanych poprawkach jest nie tak

Plan z raportu, o który pyta to zadanie: pojedyncze cyfry, NFC na wejściu (nie w tokenizerze), test zgodności HF z kryterium 0 różnic, próba słownika 16k/24k/32k.

**Pojedyncze cyfry.** Kierunek jest dobry: sonda pokazuje, że `2024 r.` jest jednym tokenem, a `2025` już nie. Brakuje kryterium. Spadek fertility będzie fałszywym alarmem, bo rozbicie cyfr dodaje tokeny (szacunek +6% do +17% na pełnym ogłoszeniu). Test, którego nie ma w planie: 2024 i 2027 mają ten sam koszt na zdaniu `w roku RRRR r. zadanie`, a wzrost długości jest podany obok, nie schowany. Trzeba ustalić, co się dzieje z tokenem, który dziś skleja rok i `r.`.

**NFC na wejściu.** Zostawienie NFC poza tokenizerem jest zgodne z wiernością bajtową i z tym, co raport już mówi. Brakuje pomiaru na tym korpusie po NFC, zestawionego z NFD z rundy 1, oraz osobnej ścieżki dla wersalików. NFC nie rusza CAPS +106,8%.

**Test HF „0 różnic”.** Dziś HF ma 0 różnic w round-tripie napisu na 1010 dokumentach urzędowych i niezerową różnicę segmentacji wobec referencji (około 0,2–0,3% tokenów). Test „zero różnic identyfikatorów wobec referencji” dziś nie przechodzi i nie mierzy tego, co psuje trening. Test, który ma chronić model, to: jeden wybrany enkoder, `decode(encode(x)) == x` na całym urzędowym, oraz zakaz mieszania referencji z HF w jednym wykresie. Gonienie identycznych identyfikatorów może wyrzucić gęstszą segmentację albo referencję bez zysku dla wierności tekstu.

**Słownik 16k/24k/32k.** Bez zadania docelowego i bez kosztu embeddingu (16k to połowa z 16,4% modelu przy 32k) próba nie rozstrzyga. Nie wybierać wariantu przez Rényi ani przez samą fertility. Dodać do porównania długość na pełnym dokumencie, nie na uciętym do 20 tys. znaków, i uchwałę z PDF, nie z `text.html`.

Czego w tych czterech punktach nie ma, a zmienia decyzję o oknie: 2048 nie mieści mediany pełnego ogłoszenia ani mediany pełnego aktu śląskiego z próby. 4096 mieści medianę ogłoszenia tylko dopóki cyfry zostają zlepione. To jest decyzja o treningu 150M, nie o tokenizerze.

## Ograniczenia

Nie było bootstrapu ani drugiego seeda. Nie trenowano modelu. Szacunek cyfr nie jest tokenizerem po przebudowie słownika. Odbudowa prawa ELI nie jest czystym prefiksem (12/78). Tabele JSON po odbudowie tracą wcięcie. OCR „pełny” to nadal sześć pierwszych skanów. PDF ponad 4 MB są pomijane. NCN nie jest zbiorem tylko z lat 2024–2026. TED i BZP mogą opisywać ten sam próg unijny. Korelacji Rényi z jakością modelu polskiego ten przegląd nie liczył; przywołane prace są o Bleu w tłumaczeniu.

STATUS=RED_TEAM_GOTOWE zmienia=2 oslabia=2 nie_zmienia=3
