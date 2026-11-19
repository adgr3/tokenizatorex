# PROTOKÓŁ AUDYTU TKX-A — TOKENIZATOREX, mocne i słabe strony

Wersja: 1.0 (zamrożona przed pomiarami) · Data: 19.11.2026 · Repo: `adgr3/tokenizatorex`,
gałąź `audyt/tkx-a-19-11`, baza `faf06223806809a79f2df0bd64efbd4c57e2d98e`.
Wykonawca: agent audytu (OpenCode) z podagentami. Recenzent rundy 2: niezależny agent
(rola „Codex”) — nie czyta skryptów rundy 1 przed własnym pomiarem.

Ten dokument jest **zamrożony przed policzeniem czegokolwiek**. Każda zmiana po
rozpoczęciu pomiarów trafia do sekcji „Zmiany po fakcie”, a wyniki nią dotknięte
są oznaczane jako **post hoc**.

---

## 1. Cel i pytania

1. W czym TOKENIZATOREX (enkoder referencyjny `superbpe.py` i eksport HF) jest
   naprawdę mocny na polszczyźnie ogólnej i urzędowej (przetargi, samorząd,
   granty, prawo)?
2. W czym jest słaby, jak duża jest strata (z niepewnością) i co to znaczy dla
   modelu 150M?
3. Które słabości warto naprawiać w TKX-C, a których nie?

Audyt **tylko mierzy**. Nie zmienia `superbpe.py`, `tokenizers/`, `hf/` ani
`export_hf.py`. Nowy kod wyłącznie w `audit/`.

## 2. Porównywane tokenizery (zawsze ten sam zestaw)

| Etykieta | Źródło | Enkoder |
|---|---|---|
| TOKENIZATOREX | `tokenizers/tokenizatorex-32k.json` | referencyjny `superbpe.py` (`encode_ordinary`) |
| TOKENIZATOREX-HF | `hf/tokenizatorex-32k/tokenizer.json` | Hugging Face |
| TOKENIZATOREX-base | `tokenizers/tokenizatorex-base-32k.json` | referencyjny `superbpe.py` |
| Slayer1B | HF `SlayerLab/Slayer1B-1.08` | HF |
| APT3-1B | HF `Azurro/APT3-1B-Base` | HF (stratny: NFKC itd. — raportowany z adnotacją) |
| Pollock-2.0 | HF `SlayerLab/pollock-2.0-polishdynaword-150m` | HF |
| Bielik-v3 (APT4) | HF `speakleash/Bielik-11B-v3.1-Instruct` | HF, tylko jeśli `hf auth whoami` działa |
| PLLuM-12B | HF `CYFRAGOVPL/PLLuM-12B-chat-2512` | HF |
| GPT-4o | `tiktoken` `o200k_base` | tiktoken |

Wszystkie enkodery wywołujemy **bez tokenów specjalnych**
(`add_special_tokens=False`, `disallowed_special=()`). Dla każdego zapisujemy
plik i SHA-256 w `audit/results/tokenizers_manifest.json`. Slayer1B musi mieć
SHA-256 `0640d3bd3674d7a6e59c540d945a2ad275a12e1bcaeb6007c37a90751f9815dd`.

Bielik v3: dostęp sprawdzony przez `hf auth whoami` (działa); jeśli pobranie
zawiedzie w trakcie, status `UNKNOWN (brak dostępu)` i audyt idzie dalej.

## 3. Korpus (rundа 0, zamrażany przed pomiarami)

### 3.1 Dziedziny nowe

| Dziedzina | Źródło publiczne | Cel |
|---|---|---|
| `przetargi_ogloszenia` | e-Zamówienia / BZP API `mo-board/api/v1/notice`, 2026 | ≥ 100 dok., ≥ 100 tys. słów |
| `przetargi_kio` | orzeczenia.uzp.gov.pl, uzasadnienia KIO, 2026 | ≥ 100 dok., ≥ 100 tys. słów |
| `samorzad_uchwaly` | Dziennik Urzędowy Woj. Śląskiego (API ELI), uchwały 2026 | ≥ 100 dok., ≥ 100 tys. słów |
| `granty_ogloszenia` | NIW (strony, aktualności, publiczne PDF-y regulaminów/ogłoszeń), 2026 | ≥ 100 dok., ≥ 100 tys. słów |
| `prawo_eli` | API ELI Sejmu, Dz.U. 2026 (`text.pdf`) | ≥ 100 dok., ≥ 100 tys. słów |
| `ocr_prasa` | Polona (BN), domena publiczna, OCR z ALTO | ≥ 50 tys. słów, jeśli się da |
| `tabele_json` | e-Zamówienia/BZP 2026, te same pola w JSON (ogłoszenia o wyniku) | ≥ 50 tys. słów |

Warunek czasu: dla dziedzin urzędowych **≥ 50% dokumentów z 2026 r.** (w praktyce
wszystkie nowe dziedziny poza OCR są z 2026). OCR to prasa przed 1940 r.
(historia języka), więc nie podlega temu warunkowi.

### 3.2 Dziedziny istniejące (zgodność z README)

`web` (held-out HPLT v3, shard `bin8_5_p1`, **inny niż trening**), `wikipedia`,
`literatura`, `prawo` (Dz.U.), `sejm`, `nauka`, `dyskusje` (SlayerLab/polish-dynaword),
`angielski` (wikitext-103 test). Po ~2 MB na dziedzinę, ten sam sposób próbkowania
co `prepare_benchmark.py` (seed 7, dokument ≤ 20 tys. znaków; dla angielskiego
akapity sklejane w dokumenty ~10 tys. znaków).

### 3.3 Definicja dokumentu, czyszczenie, zamrożenie

Dokument = jeden rekord źródła (jedno ogłoszenie, jedno uzasadnienie, jedna
uchwała, jeden akt, jeden numer prasy, jedna strona/PDF, jeden rekord parquet).
Czyszczenie: `\r\n`→`\n`, zwijanie białych znaków w linii, maks. jedna pusta
linia, strip. **Bez NFC/NFKC** — inaczej zamaskowalibyśmy H5. Unicode zostaje
tak, jak w źródle; osobno liczymy dokumenty w NFD.
Dokument przycinany do **20 000 znaków** (jak w README), żeby jeden akt nie
zdominował dziedziny; przycięcie dotyczy wszystkich dziedzin i wszystkich
tokenizerów identycznie. Dokumenty < 50 słów odrzucane (i liczone).

Podział: losowo **po dokumentach**, `dev` 40% / `test` 60%, seed **20261119**.
`dev` do szukania słabości (później TKX-C), `test` zamrożony do pomiarów
końcowych. Raport liczy `test`; `dev` tylko jako kontrola i do projektowania
poprawek.

Zamrożenie: `audit/data/MANIFEST.json` — dla każdego dokumentu: URL, data,
dziedzina, podział, liczba słów, SHA-256, flaga NFD, źródło. Teksty zostają
lokalnie (`audit/data/raw/`, w `.gitignore`). Manifest i ten protokół są
commitowane **przed** pomiarami.

## 4. Definicje i metryki

* **Słowo** = `str.split()` (jak w README).
* **Fertility** = liczba tokenów / liczba słów.
* **Bajty/token** = bajty UTF-8 tekstu / liczba tokenów.
* **Znaki/token** = znaki (code points) / liczba tokenów.
* **Fragment** (HF parity) = fragment po `CHUNK_PATTERN` z `superbpe.py`
  (granice `. ! ? ; : …` i nowe linie).
* **Superword** = token zawierający spację poza wiodącymi spacjami
  (`is_superword` z `superbpe.py`).
* **Token martwy** = 0 użyć na całym korpusie audytowym; **bardzo rzadki** = < 5 użyć.
* **Efektywność Rényiego** = `exp(H_α) / |V|`, `H_α = 1/(1-α) · log Σ p_i^α`,
  α = 2,5, częstości z korpusu (tokeny specjalne wyłączone).

## 5. Niepewność i reguła istotności

* 95% przedział ufności: **bootstrap po dokumentach**, 1000 powtórzeń, seed
  **20261119**, percentyle 2,5 / 97,5. Dla fertility, bajtów/token, znaków/token.
* Różnice między tokenizerami: **bootstrap parowany** na tych samych dokumentach
  (1000 powtórzeń, ten sam seed); raportujemy różnicę tokenów na słowo oraz
  stosunek tokenów, z 95% CI.
* **Reguła „istotnej różnicy” (RID):** różnica jest istotna, gdy 95% CI parowany
  nie zawiera zera **i** względna różnica wynosi ≥ 1% (dla fertility: ≥ 1%
  wartości odniesienia). Mniejsze różnice są praktycznie bez znaczenia.
* Dla odsetek (spójność, parytet, superwordy) podajemy przedział Wilsona 95%
  lub bootstrap po dokumentach; „istotne” = rozłączne przedziały lub RID.

## 6. Progi „słabości” (zamrożone)

(a) TOKENIZATOREX przegrywa **istotnie** (RID) z którymkolwiek polskim
    tokenizerem w dziedzinie urzędowej (fertility wyżej).
(b) Wariant odporności zwiększa liczbę tokenów o **> 25%** (bezwzględnie względem
    czystego tekstu, mediana dokumentowa lub suma — raportujemy oba).
(c) Ten sam zapis ma **> 1 sposób podziału w ≥ 5% wystąpień** (mierzone na
    wystąpieniach z korpusu i na matrycy kontekstów).
(d) Parytet HF: **< 99%** fragmentów z identyczną segmentacją w dziedzinie.

Dodatkowo raportujemy (bez progu): ranking dziedzin, H1 (lata), H2 (długość
kodów), H6/H7 (artefakty SuperBPE), H8 (przyczyny różnic HF).

## 7. Hipotezy H1–H8 — kryteria

Dla każdej: **potwierdzona** = kryterium potwierdzenia spełnione na `test`;
**obalona** = spełnione kryterium obalenia; inaczej **niejasna**. Liczby
zawsze z pliku JSON.

| # | Hipoteza | Potwierdzenie | Obalenie |
|---|---|---|---|
| H1 | Tokenizer „zamraża kalendarz”: lata spoza danych treningowych są droższe i inaczej dzielone | Średnia liczba tokenów na wystąpienie dla lat 2027–2029 istotnie (RID) wyższa niż dla 2015–2024; lub ≥ 2 różnych podziałów roku w ≥ 5% wystąpień | Brak istotnej różnicy 2015–2024 vs 2027–2029 **i** jeden dominujący podział roku (≥ 95%) |
| H2 | Długie liczby/kody tną się chaotycznie | Liczba tokenów na cyfrę rośnie z długością kodu (korelacja dodatnia) **i** odsetek kodów z > 1 podziałem ≥ 5% | Liczba tokenów na cyfrę nie rośnie istotnie i dominujący podział ≥ 95% |
| H3 | Skróty urzędowe niespójne | `art.`, `lit.`, `Dz.U.`, `M.P.`, `poz.` mają > 1 podziału w ≥ 5% wystąpień w co najmniej 2 kategoriach | Wszystkie kategorie mają dominujący podział ≥ 95% |
| H4 | Ten sam zapis tnie się różnie zależnie od kontekstu | W matrycy kontekstów odsetek wystąpień z podziałem innym niż najczęstszy ≥ 5% dla ≥ 1 kategorii | Wszystkie kategorie < 5% |
| H5 | Odporność: NFD +70%, CAPS +172% itd.; TOKENIZATOREX traci względnie więcej | Wzrost tokenów > 25% (próg 6b) dla NFD lub CAPS; względny wzrost większy niż u ≥ 1 polskiego tokenizera | Wszystkie warianty ≤ 25% lub TOKENIZATOREX ma najmniejszy względny wzrost |
| H6 | 19,4% superwordów zaczyna się w środku słowa (w słowniku); ważone użyciem | Odsetek „podejrzanych” (kryteria w protokole) ≥ 10% w słowniku **i** ≥ 5% użyć; lista 100 dziwnych tokenów niepusta | Odsetek < 5% w słowniku lub użycia < 1% |
| H7 | Częste słowa mają własny token; problem tylko wewnątrz superwordów | ≥ 90% z top 1000 słów ma własny token, ale ≥ 1% wystąpień tych słów jest rozbite wewnątrz superwordów | ≥ 1% top 1000 rozbitych poza superwordami lub < 90% ma własny token |
| H8 | Eksport HF różni się częściej na zapisach urzędowych niż na zwykłym tekście | Parytet HF < 99% fragmentów w ≥ 1 dziedzinie urzędowej i istotnie niżej niż w `web` | Parytet ≥ 99% we wszystkich dziedzinach lub brak różnicy urzędowe vs web |

H9 (pułapka `sys.path` / katalog `tokenizers/`) nie jest hipotezą, tylko
wymogiem technicznym: skrypty importują pakiet HF **przed** dopisaniem repo do
`sys.path` (`append`, nie `insert(0)`), co jest testowane.

## 8. Co dokładnie liczymy (skrypty rundy 1)

| Plik | Co mierzy | Wynik |
|---|---|---|
| `fertility.py` | tokeny/słowo, bajty/token, znaki/token, CI, ranking, pary parowane | `results/fertility.json` |
| `notations.py` | regexowe kategorie zapisów urzędowych, tokeny/wystąpienie, rozkłady, H1 (lata 2015–2026), H2 | `results/notations.json` |
| `consistency.py` | matryca kontekstów dla zapisów, odsetek innego podziału, H3/H4 | `results/consistency.json` |
| `robustness.py` | bez PL znaków, CAPS, Title, literówki 2/5%, OCR-szum 2/5%, NFD, PL–EN, emoji; wzrost bezwzgl./wzgl. z CI, H5 | `results/robustness.json` |
| `morphology.py` | MorphScore (UD_Polish-PDB, implementacja przybliżona lub publiczny kod), spójność rdzenia 200 lematów | `results/morphology.json` |
| `superwords.py` | superwordy od środka słowa (słownik i użycie), boilerplate, rozbite częste słowa w kontekście, 100 dziwnych tokenów, H6/H7 | `results/superwords.json`, `results/dziwne_tokeny.md` |
| `vocab_usage.py` | martwe/rzadkie tokeny, Zipf, Rényi α=2,5 | `results/vocab_usage.json` |
| `hf_parity.py` | parytet HF po dziedzinach, różnica tokenów, klasy przyczyn, H8 | `results/hf_parity.json` |
| `speed.py` | tokeny/s i MB/s (Python vs HF), 1 wątek, 3 powtórzenia, mediana, CPU | `results/speed.json` |
| `stability.py` | tymczasowy retrening stage1+2 na innym shardzie HPLT, pokrycie słowników, Δfertility; inaczej UNKNOWN | `results/stability.json` |

Każdy skrypt zapisuje JSON z surowymi liczbami, ustawieniami i wersjami.
Tabele w raportach generujemy **z JSON-ów**, nie ręcznie.

## 9. Round 2 (niezależna powtórka) i round 3 (adwokat diabła)

Runda 2: recenzent dostaje tylko ten protokół, manifest i listę tokenizerów;
pisze własne minimalne skrypty w `audit/review/` dla 5 liczb (fertility na 3
dziedzinach urzędowych dla TOKENIZATOREX/HF/Slayer1B; koszt lat 2024 vs 2026;
NFD; superwordy od środka; parytet HF na `przetargi_ogloszenia`). Każda różnica
> 0,5% względnie musi być wyjaśniona. Wynik: `REVIEW_RESULT` w `REVIEW_R2.md`,
werdykt PASS/FAIL, maks. 2 pętle poprawek.

Runda 3: inny agent/sesja szuka przypadków, gdzie TOKENIZATOREX wypada źle:
inne definicje słowa, liczenie na bajtach, usuwanie 10% najdłuższych dokumentów,
leave-one-source-out, 50 najgorszych dokumentów, boilerplate, koszt w kontekście
2048. Wynik: `RED_TEAM_R3.md` z oceną „zmienia wniosek / nie zmienia”.

## 10. Ograniczenia z góry znane

* Fertility ≠ jakość modelu (modelu 150M jeszcze nie trenowano).
* APT3 jest stratny (NFKC, usuwanie znaków) — jego przewaga częściowo pochodzi
  z wyrzucania znaków; raportujemy z adnotacją.
* Modele światowe są wielojęzyczne; porównanie nie jest „na równych zasadach”.
* ELI 2026 publikuje głównie PDF; tekst z PDF (pypdf) może mieć artefakty
  łamania linii — dotyczy wszystkich tokenizerów identycznie.
* OCR z Polony ma błędy rozpoznawania — to celowo (dziedzina `ocr_prasa`).
* Próbkowanie „head” parquetów dynaword nie jest losowe w całym zbiorze; jest
  deterministyczne i identyczne dla wszystkich tokenizerów.
* `stability.py` może zakończyć się UNKNOWN, jeśli zabraknie czasu/danych;
  powód będzie zapisany.
* Nie mierzymy jakości modelu, tylko koszt i segmentację.

## 11. Zmiany po fakcie

(brak — protokół zamrożony przed pomiarami)
