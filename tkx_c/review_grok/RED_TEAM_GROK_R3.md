# Recenzja red-team TKX-C, runda 3

Źródło liczb: pliki `tkx_c/review_grok/*.json` policzone na eksporcie HF
`hf/variants/*/tokenizer.json` (enkoder kanoniczny). Gałąź
`review/tkx-c-r3-grok`, commit bazowy `d3a004e0af4a58f2f6091f66343b17a7d2ad30ad`.
Test zamrożony: 2752 dokumenty (`attack1_hierarchy.json`, pole `docs_test`).
Koszt urzędowy: pierwsze 7 dziedzin, 606 dokumentów.
Teksty R3-extra zostały lokalnie; w repozytorium są URL, SHA-256 i liczby.
Nie cytuję treści dokumentów ani danych osobowych z ogłoszeń.

Werdykt przy każdym ataku dotyczy wniosku wykonawcy, nie samego faktu pomiaru.
„Zmienia wniosek” znaczy, że zdanie z raportu albo planu trzeba przepisać.
„Osłabia wniosek” znaczy, że zdanie zostaje, ale nie niesie wagi, jaką mu nadano.

## Atak 1. Hierarchia kodów od lewej

**Co zrobiono.** Na teście urzędowym, po NFC, wzorzec CPV `\d{8}-\d` (ciało 8 cyfr;
granice od lewej: 2 dział, 3 grupa, 4 klasa, 5 kategoria), daty
`\d{1,2}[./-]\d{1,2}[./-]\d{4}`, znaki spraw i kody pocztowe. Podział liczony
z offsetów `Tokenizer.encode`. Plik: `attack1_hierarchy.json`.

**CPV.** Kodów: 856. W tym 336 ma „CPV” w 12 znakach przed kodem.

V2-32k i V2b-32k: 856/856 to same pojedyncze cyfry. Dział, grupa, klasa
i kategoria są prefiksami w 856/856. Prefiks jest zachowany z konstrukcji:
każda cyfra jest granicą.

V3-32k, wszystkie 856:

| kształt ciała | n | udział |
|---|---:|---:|
| 2+2+2+2 | 388 | 45,3% |
| 3+2+3 | 117 | 13,7% |
| 1+2+2+3 | 104 | 12,1% |
| 2+3+3 | 96 | 11,2% |
| 1+3+2+2 | 73 | 8,5% |
| 1+2+3+2 | 58 | 6,8% |
| 3+3+2 | 20 | 2,3% |

Reklamowany podział od prawej `45|233|140` to 96/856. Granicę grupy (pozycja 3)
przecina 557/856 (65,1%). Granicę klasy (pozycja 4) przecina 395/856 (46,1%).
Grupę zachowuje 299/856 (34,9%). W podzbiorze „blisko CPV” grupę przecina
221/336 (65,8%), a kształt 2+3+3 ma 34/336. Sumy „grupa albo klasa” nie dodaję:
te same kody wpadają do obu liczników.

Samotny token `452` jest w słowniku V3 jednym tokenem. W kodzie ośmiocyfrowym
prefiks grupy i tak nie jest tym tokenem, gdy ciało zaczyna się od `45|…`.

**Daty.** n = 486. V3 rozcina rok w 486/486: kształt 1+3 w 459 (94,4%),
2+2 w 27 (5,6%). Liczniki rozcięcia dnia i miesiąca dla V3 nie występują
w pliku, czyli enkoder nie tnie dnia ani miesiąca (dwucyfrowe atomy).
V2 i V2b mają rok 1+1+1+1 w 486/486. Ich rozcięcia dnia (462) i miesiąca (468)
są oczekiwanym skutkiem pojedynczych cyfr i zachowują prefiks. Nie nazywam ich
niezgodnością ze strukturą.

**Znaki spraw.** n = 542, segmentów cyfrowych 1274. V3 tnie 495/1274 segmentów
(38,8%) i 397/542 spraw ma choć jeden taki segment (73,2%). Sprawy z rozciętym
segmentem 4-cyfrowym: 368, tyle samo co V2/V2b, bo rok czterocyfrowy V2 tnie
zawsze, a V3 też (kształt roku w segmencie: 1+3 w 363, 2+2 w 48, razem 411).
V2/V2b tną 1175/1274 segmentów, ale na pojedyncze cyfry, więc każdy prefiks
segmentu jest złożeniem tokenów od lewej.

**Kody pocztowe.** n = 361. Ogon trzycyfrowy jest atomem w 154/361 (42,7%).
Kształt 1+2: 207/361 (57,3%). V2/V2b: ogon 1+1+1 w 361/361. Obietnica
„000–999 są używane jako atomy” pada na teście: `950` w siatce syntetycznej
(`attack2_synthetic.json`) to `9|50`, nie token `950`.

**Werdykt: zmienia wniosek.** Zdanie „V3 = grupy po 3 od prawej
(`45233140 → 45|233|140`)” opisuje helper `split_groups3` w `superbpe.py`,
nie enkoder HF na kodach z testu. Spójność 0% w raporcie (udział kontekstów
o innym podpisie niż najczęstszy, `measure_consistency.py`) nie była tu
mierzona ponownie i nie jest tym samym co zgodność z hierarchią od lewej.
Dla modelu, który ma rozpoznać grupę 452, wada jest realna: token grupy nie
jest prefiksem kodu w 557/856 przypadkach, a V2/V2b dają ten prefiks zawsze.

## Atak 2. Lata w V3

**Co zrobiono.** Siatka syntetyczna na szablonie `w roku {Y} r. zadanie`,
lata 1900–2099, oraz gołe liczby, data ISO, data z kropkami i zapis bez spacji.
Plik: `attack2_synthetic.json`. Lata w teście urzędowym: `attack1_hierarchy.json`.

**Licznik tokenów jest płaski.** Szablon, V3-32k: 6 tokenów dla każdego roku
1900–2099 (200/200) i dla pasma 2015–2035 (21/21). V2-32k i V2b-32k: 8 tokenów,
kształt roku 1+1+1+1. V0-32k nie jest płaski: 2015 ma 4 tokeny i kształt roku `4`,
2000 ma 6 i kształt `2+2`, 2024 i 1999 mają 5 i kształt `3+1`.
Zdanie raportu „kalendarz 2015–2035 płaski: V2b 8, V3 6” się zgadza jako licznik.

**Kształt nie jest jednym prawym grupowaniem.** Pasmo 1900–2099 dzieli się
równo: 100 lat o kształcie 2+2 i 100 o kształcie 1+3. Lata 1990–1999 są
wyłącznie 2+2 (kawałki 1999: ` 19` + `99`). Lata 2000–2040 są wyłącznie 1+3
(kawałki 2024: ` 2` + `024`). Płaskość licznika na 2015–2035 jest własnością
prefiksu `20`, nie ogólną regułą „od prawej”. Prawe grupowanie 1999 to `1|999`;
enkoder daje `19|99`.

**Sąsiednie lata nie dzielą sufiksu.** `024` i `025` są osobnymi atomami.
Wspólny jest tylko wiodący `2` albo ` 2`. Zapis bez spacji (`2024r.`) ma
nadal kształt roku 1+3, ale cały napis ma 3 tokeny, nie 6. Data z kropkami
i ISO dla 2024 też mają kształt roku 1+3 i 6 tokenów całości, bo kropka
jest osobnym cięciem pretokenizera.

Na teście urzędowym (n = 9724 lat): V2/V2b 1+1+1+1 w 9724/9724. V3: 1+3
w 8989 (92,4%), 2+2 w 735 (7,6%). Te 8989 pokrywa się z licznikiem
`equals_right`. Przewaga kształtu 1+3 bierze się z tego, że test jest pełen
lat 20xx, nie z tego, że reguła działa dla każdego roku.

**Siatka 000–999.** Jeden token: 505/1000. Kształt 1+2: 495/1000. Pary 00–99:
100/100 to jeden token. Początek listy porażek: `100` → `1|00`, `101` → `1|01`,
i tak dalej. Helper Pythona złożyłby `100` w jeden token. BPE HF scala najpierw
tańszą parę; trójka wymuszona jako „lewa para + ostatnia cyfra” wtedy nie
powstaje. Stąd token `024` jest w słowniku, ale `950` i `100` enkoder i tak
emituje jako 1+2.

**Który wariant może uogólnić niewidziany rok.** V2 i V2b: rok niewidziany
jest tą samą sekwencją cyfr co rok widziany, znak po znaku. V3: rok 2028 jest
atomem `028`, którego model nie widział jako kontynuacji `024`. V0: część lat
jest całym tokenem, część nie, więc koszt i tożsamość zależą od tego, czy rok
trafił do słownika.

**Sonda TKX-D (konkret).** Na dev, nie na teście. Exact match całego napisu
roku, nie liczba tokenów. Zestaw A: lata 2018–2024 (kontrola, widziane w
tekstach urzędowych tego typu). Zestaw B: 2028–2035 (poza typowym oknem
korpusu testowego). Pary minimalne: `2024` kontra `2027` oraz `1999` kontra
`2000` w tym samym zdaniu `w roku {Y} r.`. Wariant, który myli sufiks albo
przeskakuje próg 2000, nie „odblokował kalendarza”.

**Werdykt: zmienia wniosek.** Licznik 6 kontra 8 zostaje. Wniosek „płaski
kalendarz = model uogólnia niewidziane lata” nie wynika z pomiaru. Token `024`
nie jest podobny do `025` inaczej niż przez wspólną cyfrę z przodu, a próg
1999/2000 zmienia kształt z 2+2 na 1+3.

## Atak 3. Spójność V2b

**Co zrobiono.** Każdy ciąg `\d+` na teście urzędowym i na `web`. Klasa znaku
po lewej i to, czy pierwszy token V2b jest cyfrą ze spacją. Plik:
`attack3_v2b_context.json`.

Ciągów cyfr na urzędowych: 106720. V2b dokleja spację w 52960 (49,6%).
Bez doklejenia: 53760 (50,4%). V2 nie dokleja spacji w 106720/106720.

Znak po lewej na urzędowych:

| lewy znak | n | udział |
|---|---:|---:|
| spacja | 52960 | 49,6% |
| kropka | 18209 | 17,1% |
| nowa linia | 16277 | 15,3% |
| litera | 7651 | 7,2% |
| dywiz | 4561 | 4,3% |
| inny | 4130 | 3,9% |
| ukośnik | 2110 | 2,0% |
| cudzysłów | 519 | 0,5% |
| nawias | 296 | 0,3% |
| początek | 6 | ~0 |
| `nr` bez spacji | 1 | ~0 |

`poz` bez spacji nie występuje w kluczu. Tabulator i NBSP mają licznik 0,
bo czyszczenie korpusu zwija białe znaki w linii do zwykłej spacji. Na surowym
PDF z NBSP doklejenie może padać częściej. To hipoteza: ten test jej nie mierzy.

Ciągi cyfr z co najmniej dwoma wystąpieniami: 2070. V2b ma dwa różne pierwsze
tokeny w 1004/2070 (48,5%). Histogram liczby różnych pierwszych tokenów:
`{2: 1004, 1: 1066}`. V2: 0/2070, histogram `{1: 2070}`. Więcej niż dwa
pierwsze tokeny nie występuje. Niespójność jest binarna: spacja doklejona
albo goła cyfra.

Przykład `2026` (n = 4104): pierwszy token ` 2` w 3426, gołe `2` w 678.
`1`: gołe `1` w 7013, ` 1` w 6304 (n = 13317).

Na `web` (4205 ciągów): doklejone 2647, niedoklejone 1558. Lewa strona to
nie tylko spacja: inny 396, dywiz 259, nowa linia 246, litera 220, kropka 215,
nawias 106, ukośnik 93.

Hipoteza z zadania („nr/poz. bez spacji”) jest na tym teście prawie pusta
(1 + 0). Nowa niespójność jest gdzie indziej: kropka, początek linii, dywiz,
ukośnik, litera, nawias, cudzysłów.

V2b rzeczywiście likwiduje superword kończący się spacją. W ataku 4 najczęstsze
typy obecne w V2 i nieobecne w V3 to właśnie `, `, ` pkt `, ` nr `, ` z `
(duplikaty ze spacją końcową). To osobny, udany cel V2b. Nie jest to ten sam
cel co „ta sama liczba ma jeden pierwszy token”.

**Werdykt: zmienia wniosek.** Zdanie, że liczba w V2b jest zawsze
`·2|0|2|4`, dotyczy napisu ze spacją ASCII przed liczbą. Połowa ciągów
urzędowych tej spacji nie ma, a ten sam napis cyfr dostaje dwa pierwsze tokeny
w 48,5% ciągów powtórzonych. V2 jest tu spójny (0/2070). V2b zamienia starą
niespójność superwordu na nową niespójność pierwszej cyfry.

## Atak 4. Cena wymuszonych grup

**Co zrobiono.** Słowniki V2 i V3 w 16k/24k/32k, użycia na całym teście,
koszt względem V0. Plik: `attack4_vocab.json`. Bootstrap 1000×, seed 20261119,
`common.bootstrap_indices`.

**Martwe i wymuszone.** Gołe grupy 00–99 i 000–999: 1100. Ze spacją: 2210.
Te same 2210 tokenów jest w V3-16k, V3-24k i V3-32k. Martwe wymuszone: 1016
na każdym rozmiarze. Martwe gołe trójki: 500/1000.

| wariant | martwe | udział martwych | udział 1100 gołych | udział 2210 wymuszonych |
|---|---:|---:|---:|---:|
| V2-32k | 644 | 2,013% | 0 | 0 |
| V2-24k | 274 | 1,142% | 0 | 0 |
| V2-16k | 130 | 0,812% | 0 | 0 |
| V3-32k | 1560 | 4,875% | 3,44% | 6,91% |
| V3-24k | 1238 | 5,158% | 4,58% | 9,21% |
| V3-16k | 1125 | 7,031% | 6,88% | 13,81% |

4,88% z raportu odtwarza się (1560/32000 = 0,04875). Przy 16k same wymuszone
grupy to 13,81% słownika, a 1016/1125 martwych tokenów to nieużyte grupy
cyfr. Rodzaje na V3-16k (obecne tak samo na większych): bare2 100/100 użyte
(51696 użyć), bare3 500 użytych i 500 martwych (62 rzadkie, poniżej 5 użyć),
spacja+1 cyfra 10/10, spacja+2 cyfry 100/100, spacja+3 cyfry 484 użyte i 516
martwych. Pół tysiąca gołych trójek jest w słowniku i enkoder ich nie emituje
albo tekst ich nie zawiera. Siatka z ataku 2 rozstrzyga pierwszą przyczynę
dla 495 napisów 000–999: token jest, emisji nie ma.

**Koszt urzędowy względem V0** (tokeny V0 = 1 154 963, słowa = 685 753):

| wariant | tokeny | delta | 95% CI |
|---|---:|---:|---|
| V2-32k | 1 316 574 | +13,993% | [13,08; 15,07] |
| V2b-32k | 1 282 908 | +11,078% | [10,32; 11,96] |
| V3-32k | 1 215 758 | +5,264% | [4,85; 5,72] |

To te same liczby co w raporcie (+13,99 / +11,08 / +5,26). Kolejność
V3 < V2b < V2 trzyma się na każdej z 7 dziedzin. Delty V2 / V2b / V3:
przetargi ogłoszenia 16,76 / 14,37 / 9,53; KIO 8,89 / 6,36 / 2,49;
uchwały 22,44 / 17,26 / 5,41; granty 15,31 / 11,45 / 4,38;
prawo ELI 13,94 / 10,69 / 4,81; OCR prasy 4,02 / 2,37 / 0,80;
tabele JSON 18,93 / 16,83 / 8,89. Procenty zaokrąglone do 0,01 pp z
`delta_pct` w JSON.

**Tekst ubogi w liczby.** V3 kontra V2:

| dziedzina | tokeny V0 | V2 vs V0 | V3 vs V0 | V3 vs V2 |
|---|---:|---:|---:|---:|
| web (421 dok.) | 218 817 | +2,964% | +1,776% | −1,154% |
| wikipedia (241) | 257 505 | +5,798% | +1,357% | −4,198% |
| literatura (230) | 284 788 | +0,026% (CI przechodzi przez 0) | +0,678% | +0,652% [0,573; 0,725] |

Na web i wikipedii V3 jest krótszy od V2: oszczędność na cyfrach przebija
utracone kawałki słów. Na literaturze V3 jest droższy od V2 o 0,65%.
To jest mierzalna cena wypchniętych tokenów zwykłych, i jest mała.

Użycia typów V2 nieobecnych w V3: 84 863 / 3 531 112 = 2,403% całego testu.
Z tego duża część to duplikaty ze spacją końcową (45 450 użyć), czyli stary
nawyk V2, który V2b/V3 miały usunąć. Bez nich, na literaturze: 3002 użycia
zwykłych brakujących typów przy 284 861 tokenach V2 (1,05%). Najczęstsze
zwykłe braki (użycia, V3 składa z 2 tokenów, +1 token na użycie):
`........` 4447, `§` 1991, `łącznik` 462, ` załączniku` 397,
` najkorzyst` 302, `polskie` 264. Dla `§` oba kawałki V3 dekodują się do
U+FFFD: to osobne bajty UTF-8 znaku paragrafu, nie dwa morfemy. Na uchwałach
to realny koszt, nie szum kodowania pliku JSON.

**Werdykt: osłabia wniosek.** 4,88% przy 32k jest prawdą i nie jest pełną ceną.
Przy 16k wymuszone grupy to 13,81% słownika, a 500 z 1100 gołych trójek jest
martwych. Na tekście bez liczb V3 nie jest tańszy od V2. Nie twierdzę, że V3
jest droższy od V2 na web albo wikipedii: pomiar mówi odwrotnie.

## Atak 5. Czy +5,26% jest własnością jednej próbki

**Co zrobiono.** 35 dokumentów spoza hostów korpusu, etykieta R3-extra.
Manifest: `r3_extra_manifest.json` (id, URL, SHA-256, słowa; bez treści).
Pomiar: `attack5_extra.json`. Te same cztery eksporty 32k, ten sam bootstrap
i seed. Słowa = `split()` tekstu, który wszedł do enkodera.

Skład: 32 ogłoszenia TED (XML eForms, polski zamawiający, inny host niż
ezamowienia; ten sam gatunek co przetargi), 1 strona BIP Kraków, 2 akty
dziennika mazowieckiego (PDF, pozycje 1765 i 7371 z 2024). Akty obcięte do
60 000 znaków: 1765 ma 71 stron i 27 528 słów przed obcięciem, do enkodera
weszło 7997 słów; 7371 ma 36 stron i 14 202 słów, weszło 8132. SHA-256 jest
hashem tekstu po obcięciu. Hosty korpusu (dziennik śląski, UZP, NIW,
ezamowienia, API Sejmu, Hugging Face) nie były użyte.

| zestaw | n | słowa | V2 vs V0 | V2b vs V0 | V3 vs V0 |
|---|---:|---:|---:|---:|---:|
| wszystkie | 35 | 90 704 | +13,05% [11,13; 16,12] | +10,65% [9,07; 13,22] | +3,34% [2,92; 3,78] |
| TED | 32 | 74 285 | +13,77% [11,90; 16,78] | +11,18% [9,53; 13,79] | +2,93% [2,69; 3,16] |
| dziennik mazowiecki | 2 | 16 129 | +8,74% [8,45; 9,04] | +7,59% [7,41; 7,76] | +5,75% [5,66; 5,85] |
| BIP Kraków | 1 | 290 | +14,11% | +10,75% | +3,35% |

Tokeny całości: V0 182 528, V2 206 344, V2b 201 976, V3 188 625.
Mediana dokumentu: V2 +15,02%, V2b +12,02%, V3 +2,83%.
Kolejność V3 < V2b < V2 zachodzi w 35/35 dokumentów. Przedział V3 na TED
[2,69; 3,16] nie nachodzi na przedział urzędowy [4,85; 5,72]. Przedziały V2
i V2b nachodzą na liczby z testu zamrożonego. Dwa akty dziennika dają V3
+5,75%, blisko +5,26%, ale n = 2 i tekst jest obcięty. BIP to jedna strona.

**Werdykt: osłabia wniosek.** Kolejność nie jest artefaktem próbki.
Rząd wielkości V2 i V2b też nie. Sama liczba +5,26% dla V3 nie przenosi się
na nowe ogłoszenia TED (+2,93%). To nadal ten sam gatunek, z innego kanału
publikacji, więc nie jest to nowa dziedzina. Drugi gatunek (dziennik
wojewódzki) jest za cienki, żeby sam niósł wniosek.

## Atak 6. Post hoc i ryzyko dopasowania do testu

**Co zrobiono.** Odczyt protokołu, raportu i `TKX_D_PLAN.md`. Planu nie
zmieniam.

Protokół §3: reguły projektuje się na dev, test tylko w pomiarze końcowym.
Protokół §9 pkt 7 i raport §9 mówią wprost, że V2b i V3 doszły 20.11, po
zamrożeniu protokołu, po wynikach V2. To ujawnienie jest. Nie unieważnia
procentów zmierzonych na teście.

`TKX_D_PLAN.md` §1 robi z tego testu kryterium wstępne: „V2b i V3 (najlepszy
rozmiar spośród 16k/24k/32k wyznaczony z kosztu w tokenach z
`digits_cost_new.json`: V3-32k < V2b-32k < V2-32k)”. To samo §1 wkłada
„koszt w tokenach” do decyzji obok BPB i sondy. Niżej ten sam plan mówi, że
fertility i Rényi nie są kryterium wyboru. Te dwa zdania się wykluczają.
Raport §8 i §10 powtarzają, że wybór należy do BPB i sondy, i jednocześnie
§1 planu już skreśla rozmiary na podstawie testu.

Dane tokenizera to HPLT p2, 400 MB (`stability_train.txt`), nie korpus modelu
150M i nie shard p0. Protokół §9 pkt 1 to ujawnia. Plan TKX-D ma trenować
model na innym korpusie. Koszt tokenów z testu TKX-A nie jest BPB na tamtym
korpusie.

**Tekst, który warto dopisać do planu (propozycja, plik planu nietknięty).**

> Zbiór kandydatów i rozmiary słownika zamrażamy przed jakimkolwiek wglądem
> w test TKX-A. W pierwszej rundzie trenujemy tylko 32k: V0, V2, V2b, V3.
> Rozmiarów 16k i 24k nie wybieramy z `digits_cost_new.json`.
> Kolejność V3-32k < V2b-32k < V2-32k jest kosztem tokenów na teście, nie
> rankingiem modelu. Decyzja: najniższy BPB na dev oraz nie gorsza sonda
> (exact match roku, kwoty w dwóch zapisach, grupy i klasy CPV), różnica
> większa niż szum co najmniej dwóch seedów albo bootstrap po dokumentach dev.
> Test TKX-A idzie raz, po wyborze, i nie wraca do listy kandydatów.
> V2b i V3 zaprojektowano po obejrzeniu V2 na tym teście; ich wynik na teście
> nie jest pomiarem z góry. Próbka treningu tokenizera to HPLT p2 400 MB,
> nie korpus modelu. Fertility nie jest kryterium.

**Werdykt: osłabia wniosek.** Ujawnienie post hoc jest uczciwe i zostaje.
Wniosek „wybór rozmiaru jest jeszcze przed nami” jest słabszy, niż mówi
raport, bo §1 planu już wybrał rozmiar kosztem tokenów z testu. Samych
procentów +13,99 / +11,08 / +5,26 to nie przekreśla.

## Atak 7. Literatura a mały model

Źródła otwarte sprawdzone w tej sesji. Nie cytuję prac, których URL nie
otworzyłem.

Singh i Strouse, arXiv:2402.14903 (2024). LLaMa i PaLM tną na pojedyncze
cyfry. GPT-3.5 i GPT-4 mają tokeny 1-, 2- i 3-cyfrowe. Cięcie od prawej,
wymuszane przecinkami w czasie inferencji, poprawia arytmetykę na modelach
granicznych. Luka między kierunkami maleje ze skalą. To arytmetyka wartości
miejsca, nie kody urzędowe o hierarchii od lewej. Kierunek korzystny dla
dodawania jest przeciwny do hierarchii CPV. Mniejsze modele są według tej
pracy bardziej wrażliwe na tokenizację, nie mniej.

Zhou, Wang, Lin i Chen, arXiv:2409.17391, EMNLP 2024 Findings. Trening od
zera: system o podstawie 10 jest konsekwentnie oszczędniejszy danymi niż
podstawa 100 i 1000. Autorzy przypisują to wyższej częstości tokenu.
Podstawy 100 i 1000 gorzej rozróżniają tokeny i gorzej wykonują operacje na
tokenach. Dostrajanie już wytrenowanego modelu wygląda podobnie dla różnych
systemów. To jest argument za V2/V2b przy treningu od zera, nie za V3.

Yang, Hu, Kang, Lin i Zhang, arXiv:2411.03766, ICLR 2025. Modele 0,1B, 0,9B
i 3B trenowane od zera na dodawaniu i mnożeniu. Na 0,9B tokenizer jednocyfrowy
wygrywa w dziedzinie i poza nią; tokenizer trzycyfrowy wypada słabo.
Zdanie z pracy: tokenizery z rosnącą liczbą cyfr w tokenie wyraźnie szkodzą
NUPA modeli poniżej miliarda parametrów. Przy 3B tokenizer dwucyfrowy dorównuje
jednocyfrowemu, trzycyfrowy nadal jest gorszy. To zadania liczbowe, nie BPB
tekstu urzędowego.

Tao i in., arXiv:2407.13623, NeurIPS 2024. Modele od 33M do 3B. Optymalny
rozmiar słownika rośnie z budżetem obliczeń. Autorzy szacują, że Llama 2 70B
powinno mieć co najmniej 216k tokenów zamiast 32k, a skok 32k → 43k podniósł
ARC-Challenge z 29,1 do 32,0 przy tych samych FLOPs. Nie wyciągam z tego
optymalnego rozmiaru dla modelu 30M. Wniosek, który da się przenieść: rozmiar
słownika nie jest darmowy i nie wybiera się go samym kosztem tokenów na jednej
próbce tekstu.

Llama 3, arXiv:2407.21783. Słownik 128k. Kompresja angielskiego z 3,17 do 3,94
znaków na token względem tokenizera Llama 2, czyli model czyta więcej tekstu
za ten sam budżet. To argument o koszcie, nie o tym, że krótszy tekst uczy
lepiej rozpoznawać kody. Praca nie zaleca pojedynczych cyfr.

Czego literatura nie mierzy: BPB polskiego tekstu urzędowego i tekstu prawie
bez cyfr. Nasz pomiar (`attack4_vocab.json`) jest tu lokalny: na literaturze
V3 jest o 0,65% droższy od V2, na web i wikipedii tańszy, bo tam są liczby.
Nikt z cytowanych prac nie pokazał, że grupowanie od prawej pomaga albo szkodzi
perplexity tekstu nieliczbowego.

**Co literatura wspiera u wykonawcy.** Pojedyncze cyfry są rozsądną hipotezą
dla modelu poniżej miliarda parametrów uczonego od zera (Zhou, Yang).
Płaski koszt roku w tokenach jest własnością V2/V2b i nie potrzebuje V3.
Fertility jest kosztem obliczeń (Llama 3), więc raport ma rację, że sam
licznik tokenów nie wybiera wariantu.

**Czego literatura nie wspiera.** „Mniej tokenów ⇒ lepszy tokenizer małego
modelu.” Grupy trzycyfrowe jako sposób na nauczenie kodów: Yang i Zhou mówią
przeciwnie dla zadań liczbowych od zera, Singh mówi o prawym grupowaniu w
arytmetyce dużych modeli, a nasz enkoder V3 i tak nie realizuje tego grupowania
niezawodnie (atak 1 i 2). Przeniesienie zwycięzcy z ~30M na 150M jest hipotezą
w drugą stronę: u Singha luka tokenizacji maleje ze skalą, więc sonda na 30M
może przesadzić z wagą schematu cyfr.

**Werdykt: osłabia wniosek.** Osłabia zdanie, że niższa fertility V3 jest
przesłanką jakości dla małego modelu. Nie obala zdania, że wybór ma zapaść
na BPB i sondzie.

## Atak 8. Czego TKX-C nie domknął

Pięć do dziesięciu miejsc, w których wariant może paść na modelu ~150M albo
w sondzie TKX-D. „Pomiar” = liczba z JSON tej recenzji. „Hipoteza” = skutek
dla wag, którego nie trenowaliśmy.

1. **Pomiar.** 495/1000 napisów 000–999 nie jest jednym tokenem HF
   (`attack2_synthetic.json`). 500/1000 gołych trójek ma zero użyć na całym
   teście (`attack4_vocab.json`). Zdanie „żaden rok/kod nie jest obcy, bo
   000–999 są w słowniku” myli obecność w słowniku z emisją. Kod, którego
   trójka jest w słowniku, a enkoder emituje `1|00`, jest dla modelu obcy
   w tym samym stopniu co brak tokenu.
2. **Pomiar kształtu, hipoteza o wagach.** 1999 → `19|99`, 2000 → `2|000`
   (atak 2). Hipoteza: model 150M nie potraktuje 2000 jako 1999+1, bo nie
   dzieli się żaden token sufiksu.
3. **Pomiar.** Sąsiednie lata 20xx dzielą tylko wiodącą cyfrę. Sufiksy `024`
   i `027` są osobnymi atomami (atak 2). Hipoteza, zgodna z Zhou i Yang:
   rzadki atom trzycyfrowy jest słabo wyuczony przy treningu od zera. Częstości
   sufiksów w próbce p2 nie przeliczałem w tej recenzji.
4. **Pomiar.** Ta sama kwota w dwóch zapisach, V3 (`attack2_synthetic.json`):
   `1234` to `12|34`, a `1 234` to `1|234`; `1234567` to `12|34|567`, a
   `1 234 567` to `1|234|567`; `1999` to `19|99`, a `1 999` to `1|999`;
   `1000000` to `1|00|00|00`, a `1 000 000` to `1|000|000`.
   `12345` / `12 345` akurat się zgadza (`12|345`). V2 i V2b mają tę samą
   sekwencję cyfr w obu zapisach dla każdej z tych par. Hipoteza: sonda
   zgodności kwoty obleje V3 i zda V2/V2b.
5. **Pomiar.** V2b dokleja spację w 49,6% ciągów urzędowych (atak 3).
   Nowa linia: 15,3%. Hipoteza: surowy PDF z NBSP (korpus testowy ma NBSP
   już zwinięte, licznik 0) doklei jeszcze rzadziej.
6. **Pomiar.** Grupa CPV przecięta w 557/856, reklamowane 2+3+3 tylko w
   96/856 (atak 1). Zgodność chunków Python–HF na poziomie całego dokumentu
   może zostać wysoka i jednocześnie psuć właśnie segmentację liczb. Siatka
   495/1000 jest na to dowodem bez powoływania się na plik parity wykonawcy.
7. **Pomiar.** Ogon kodu pocztowego atomowy w 154/361. `950` → `9|50`.
   Sonda „czy 950 jest tokenem, który model widzi w kodzie” pada dla V3.
8. **Pomiar.** V3-16k: 2210/16000 = 13,81% słownika to wymuszone grupy,
   martwe 7,03% (atak 4). Przy budżecie embeddingów modelu ~30M to duży udział
   parametrów na tokeny, których enkoder nie emituje. Hipoteza: BPB V3-16k
   przepłaca te parametry względem V2-32k nawet tam, gdzie fertility V3 jest
   niższa.
9. **Pomiar licznika, hipoteza o szablonie.** Płaski kalendarz V3 to 6 tokenów
   na jednym zdaniu ze spacją przed rokiem. Na teście rok w dacie jest rozcięty
   w 486/486 (atak 1). Sonda, która liczy tokeny szablonu, zaliczy V3.
   Sonda, która żąda napisu roku, może oblać.
10. **Hipoteza plus Singh 2024.** Luka między schematami cyfr maleje ze skalą
    na modelach granicznych. Zwycięzca sondy na ~30M nie musi być zwycięzcą
    na 150M. Plan powinien zapisać, że wynik 30M jest przesiewem, nie werdyktem
    dla 150M.

**Werdykt: osłabia wniosek.** Raport słusznie zostawia wybór na TKX-D.
Lista powyżej odbiera V3 status „bezpiecznego zwycięzcy kosztu” i odbiera
V2b status „spójnej poprawki”. Żadnego z tych wariantów nie skreślam przed
sondą na dev, poza tym, co jest w rekomendacji niżej.

## Co się ostaje, co poprawić

| wniosek z raportu | status |
|---|---|
| Koszt na 7 dziedzinach testu: V2 +13,99%, V2b +11,08%, V3 +5,26% względem V0, z podanymi CI | ostaje się (odtworzone: +13,993 / +11,078 / +5,264) |
| Kolejność V3 < V2b < V2 na urzędowych | ostaje się; na R3-extra też, 35/35 |
| Licznik szablonu 2015–2035: V2b 8, V3 6, V0 schodki | ostaje się jako licznik |
| V2/V2b: zero tokenów wielocyfrowych, prefiks kodu zachowany | ostaje się (CPV 856/856) |
| V2b usuwa superword kończący się spacją | ostaje się (najczęstsze braki V2 względem V3 to właśnie te duplikaty) |
| Post hoc V2b/V3 jest opisany w protokole §9 i raporcie §9 | ostaje się |
| Wybór końcowy należy do BPB i sondy, nie do samego licznika tokenów | ostaje się i jest mocniejszy po atakach 4, 5 i 7 |
| NFC +0,0%, round-trip 2752/2752, golden CI | nie mierzone ponownie; nic w tej recenzji ich nie rusza |
| V3 tnie kody od prawej, `45233140 → 45\|233\|140` | poprawić: na teście 96/856; grupa przecięta w 557/856 |
| Spójność CPV 0% = zgodność ze strukturą kodu | poprawić interpretację: 0% to stabilność między kontekstami, nie hierarchia od lewej |
| Płaski kalendarz = model uogólnia niewidziane lata | poprawić: kształt przeskakuje przy 2000, sufiksy są obcymi atomami |
| V2b daje liczbie zawsze token `·2` | poprawić: 50,4% ciągów urzędowych bez doklejenia; 1004/2070 ciągów ma dwa pierwsze tokeny |
| 4,88% martwych to cena V3; żaden kod nie jest obcy | poprawić: przy 16k martwe 7,03% i wymuszone 13,81%; 495/1000 trójek enkoder nie emituje |
| +5,26% jest stałą kosztem V3 | poprawić: na 32 nowych TED +2,93% [2,69; 3,16] |
| Plan §1: rozmiar z `digits_cost_new.json` i koszt tokenów w kryterium | poprawić; patrz propozycja w ataku 6 |
| Mniej tokenów ⇒ lepszy mały model | poprawić: literatura tego nie mówi; na literaturze V3 jest droższy od V2 o 0,65% |

## Kandydaci do TKX-D

**Trenować w pierwszej rundzie, wszystko 32k, ten sam budżet bajtów:**

- V0-32k jako kontrola „przed poprawkami”.
- V2-32k. Jedyny schemat, który na teście zachowuje każdy prefiks od lewej
  i tożsamość cyfry niezależnie od spacji, kropki i nowej linii. Nie skreślać
  go za +13,99%.
- V2b-32k jako mierzona alternatywa, z jawną wadą: połowa liczb nie dostaje
  doklejonej spacji. Nie traktować go jako domkniętej poprawki spójności.
  Warto go trenować, bo usuwa superword ze spacją i jest tańszy od V2 o około
  3 pp na urzędowych.
- V3-32k jako folia kompresji, nie jako faworyt. W raporcie z rundy zapisać,
  że enkoder HF nie realizuje `split_groups3`. Niższy koszt tokenów nie jest
  głosem za V3.

**Odrzucić teraz, zanim ruszy karta:**

- Wybór zwycięzcy z `digits_cost_new.json`. Kolejność kosztu nie jest
  kolejnością modelu, a +5,26% nie jest stałą (atak 5).
- V3-16k w pierwszej rundzie. 13,81% słownika to wymuszone grupy, 7,03%
  tokenów jest martwych, 500/1000 gołych trójek ma zero użyć. To najgorszy
  stosunek ceny słownika do obietnicy, która i tak nie jest dotrzymana przez
  enkoder. V3-24k (9,21% wymuszone, te same 1016 martwych grup) też nie
  wchodzi do pierwszej rundy. Rozmiar 16k/24k dla V2 można zbadać później,
  jeśli BPB przy 32k będzie nierozstrzygnięte. Nie teraz i nie z fertility
  testu.
- Sondę, która liczy tokeny szablonu `w roku RRRR r.` zamiast exact match
  napisu. Taka sonda zaliczy V3 za płaski licznik i nie zobaczy progu 1999/2000
  ani rozciętej grupy CPV.

**Trzy sondy, na dev, exact match, nie fertility.**

1. **Rok poza oknem.** Kontrola 2018–2024, trzymane 2028–2035, pary
   `2024`/`2027` i `1999`/`2000` w zdaniu `w roku {Y} r.`. Metryka: dokładny
   napis roku. Rozstrzyga, czy V3 w ogóle „odblokował kalendarz”.
2. **Zgodność kwoty.** Ta sama kwota jako `1234567,89 zł` i
   `1 234 567,89 zł` (oraz para `1999` / `1 999`). Metryka: model podaje tę
   samą wartość. V2/V2b mają tę samą sekwencję cyfr; V3 ma inne atomy.
3. **Grupa i klasa CPV.** 50 prawdziwych kodów z dev. Dla ciała
   `45233140` oczekiwane napisy to grupa `452` i klasa `4523`. V2/V2b
   składają każdy taki prefiks z cyfr. W V3 granica grupy jest granicą
   tokenu tylko w 299/856 kodów testu; w 557/856 token przecina te trzy
   cyfry. Sonda ma sprawdzić, czy model i tak wypisze napis grupy.

Dopisek do planu z ataku 6 jest warunkiem, żeby te trzy sondy były wyborem,
a nie komentarzem po fakcie.

STATUS=RED_TEAM_GOTOWE zmienia=3 oslabia=5 nie_zmienia=0
