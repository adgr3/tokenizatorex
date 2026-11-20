# REVIEW TKX-C, RUNDA 2 — niezależna powtórka (Codex)

Repo: `adgr3/tokenizatorex` · head recenzji: `d3a004e` (zweryfikowane `git rev-parse HEAD`)
· gałąź: `review/tkx-c-r2-codex` · data: 20.11.2026
· własne wyniki: `tkx_c/review_codex/results_codex.json` (commit `d58b93e`, uzupełnienie `ebb99a9`)

Metoda: własne skrypty w `tkx_c/review_codex/`, kanoniczny eksport HF
(`hf/variants/*/tokenizer.json`), HF `tokenizers` 0.23.3 importowany przed
dołączeniem ścieżek repo, test/dev wg `audit/data/MANIFEST.json`,
bootstrap 1000× seed 20261119 na jednym generatorze NumPy, tekst po NFC
wyłącznie dla V2+ (V0/V1 surowy). Nie zmieniano kodu wykonawcy.

---

## Tabela A — moje liczby

| # | Pomiar | Wynik |
|---|---|---|
| A1 | Rozmiary słownika (14 wariantów) | 16 000 / 24 000 / 32 000 dokładnie (15999/23999/31999 + 1 token specjalny) we wszystkich wariantach |
| A1 | V3 — wymuszone grupy w słowniku | `00`–`99`: 100/100, `000`–`999`: 1000/1000, wersje ze spacją: 100 + 1000, `Ġ0`–`Ġ9`: 10 → **2210**; mieszczą się w limicie 32k/24k/16k |
| A2 | V1/V2/V2b — tokeny z ≥2 cyframi (ASCII `Nd`) | **0** w każdym |
| A2 | V1/V2/V2b — tokeny cyfra+litara | **0** w każdym (`Ġ` to symbol spacji ByteLevel, nie litera) |
| A2 | V2b — tokeny `Ġ0`…`Ġ9` | **10/10** obecne |
| A2 | V2b — superword z końcową spacją przed cyfrą w `test` | **0** |
| A2 | `ĠrokuĠ` w słowniku / wystąpienia w `test` | V2: **tak** (obecny w słowniku); V2b: **nie / 0 wystąpień**; V0,V3: nieobecny |
| A3 | Prawdziwy koszt vs V0, 7 dziedzin urzędowych¹ | V2 **+13,9927%** [12,978; 15,088] · V2b **+11,0778%** [10,260; 11,955] · V3 **+5,2638%** [4,803; 5,734] |
| A3 | Per dziedzina (V2) | przetargi_ogl. +16,76%, KIO +8,89%, uchwały +22,50%, granty +15,31%, prawo_eli +13,94%, OCR +4,02%, tabele +18,93% |
| A4 | Kalendarz 2015–2035 (wszystkie 32k) | V0 4/5/6 (niepłaski); V1/V2/V2-base/V2b **8**; V3 **6** — płaski dla każdego roku |
| A5 | Spójność (własna reimplementacja metryki „pary string×kontekst”) | data 17,14→0,00%; CPV 23,86→0,00%; przepis 28,00→14,86%; kwota 35,57→27,14%; znak sprawy 24,71→13,00% (V0→V2). V2b znak sprawy 12,14% |
| A6 | NFD (test, 7 dziedzin) | V0 +45,42% [43,25; 47,24]; V1 +39,94%; V2/V2b/V3 **0,00%** [0,00; 0,00] |
| A7 | Round-trip `decode(encode(x)) == x` | **2752/2752** dla każdego z 14 wariantów; suma długości kawalków = długość UTF-8 tekstu: **2752/2752** dla 14/14 |
| A8 | Martwe tokeny (test / dev) | V0 1,95% / 3,02%; V1 2,01% / 3,08%; V2 2,01% / 3,08%; V2b 2,01% / 3,12%; **V3 4,875% / 5,88%**; V3-24k 5,16%, V3-16k 7,03%. Z 2210 wymuszonych grup V3 na `test` nieużytych: **1016** |
| A9 | Pełne dokumenty (32k), mediana / p90 / ≤2048 / ≤4096 | ogłoszenia 3883/6722/10%/55% (V0) → 4536/7766/5%/30% (V2); KIO 1350/2478/80%/90% → 1485/2699/65%/90%; granty 10776/41891/25%/35% → 11471/44055/20%/35%; uchwały 2602/12114/40%/70% → 2858/21942/40%/60% |
| A10 | Te same dane treningowe | `audit/tmp/stability_train.txt`, 400 160 750 B, SHA-256 `b0e7447cf94f8e0fa03edfeb3f6f10a2e63c9e32037f086cf5a434709ae6e558`; protokoół §9.1/§9.7 i manifest wariantów wskazują tę samą próbkę p2 i seed dla wszystkich 14; SHA-256 eksportów HF z manifestu zgodne (0 rozbieżności) |

¹ Zbiór 7 dziedzin odtworzony niezależnie (przetargi_ogloszenia, przetargi_kio,
samorzad_uchwaly, granty_ogloszenia, prawo_eli, ocr_prasa, tabele_json); jako
jedyny z podzbiorów 15 dziedzin reprodukuje wszystkie trzy liczby wykonawcy
i pokrywa się z `measure_lib.OFFICIAL`.

### Tabela kawałków (A2, kanoniczny HF)

| Tekst | V0 | V2 | V2b | V3 |
|---|---|---|---|---|
| `2024` | `202│4` (2) | `2│0│2│4` (4) | `2│0│2│4` (4) | `2│024` (2) |
| `2027` | `202│7` (2) | `2│0│2│7` (4) | `2│0│2│7` (4) | `2│027` (2) |
| `45233140-2` | `45│23│3│140│-2` (5) | 10 pojedynczych (10) | 10 pojedynczych (10) | `45│233│140│-│2` (5) |
| `1 234 567,89` | `1│Ġ23│4│Ġ56│7,│89` (6) | 12 (12) | 10 (10) | `1│Ġ234│Ġ567│,│89` (5) |
| `0,125` | `0,│125` (2) | 5 (5) | 5 (5) | `0│,│125` (3) |
| `00-950` | `00│-9│50` (3) | 6 (6) | 6 (6) | `00│-│9│50` (4) ⚠ |
| `ZP.271.12.2026` | 7 | 13 | 13 | `Z│P.│271│.│12│.│2│026` (8) |
| `20.11.2026` | 4 | 10 | 10 | `20│.│11│.│2│026` (6) |
| `Dz.U. z 2024 r. poz. 1320` | 9 | 15 | 14 | 10 ⚠ |
| `art. 275 pkt 1` | 5 | 7 | 6 | `art.│Ġ275│Ġpkt│Ġ1` (4) |
| `0012` | `00│12` (2) | 4 (4) | 4 (4) | `00│12` (2) ⚠ |
| `123456789012345` | 7 | 15 | 15 | `12│34│56│789│01│23│45` (7) ⚠ |
| `COVID-19` | 3 | 5 | 5 | 4 |
| `A4` | 2 | 2 | 2 | 2 |
| `H2O` | 3 | 3 | 3 | 3 |
| `1 234 567,89 zł` | **7** | **13** | **11** | **6** |
| `w roku 2024 r. zadanie` | 5 | 8 | 8 | 6 |

⚠ — przypadki łamiące regułę „grupy po 3 cyfry od prawej” (szczegóły w znalezisku WAŻNE-1).

---

## Tabela B — porównanie z wykonawcą

| Liczba / twierdzenie | Wykonawca | Moja | Różnica wzgl. | Wyjaśnienie |
|---|---|---|---|---|
| Rozmiary 14 słowników | 16/24/32k | dokładnie 16/24/32k | 0% | zgodne |
| Wymuszone grupy V3 | 2210 merges | 2210 tokenów w słowniku | 0% | zgodne |
| Tokeny ≥2 cyfry / cyfra+litara w V1/V2/V2b | 0 / 0 | 0 / 0 | 0% | zgodne |
| `·0`…`·9` w V2b; superword przed cyfrą | tak; 0 | 10/10; 0 | 0% | zgodne |
| `·roku·` V2 → V2b | znika | obecny → nieobecny, 0 wystąpień | 0% | zgodne |
| Koszt V2 (7 urz.) | +13,99% [13,08; 15,07] | +13,9927% [12,98; 15,088] | <0,03% | punkt identyczny; CI różni się o 0,05–0,1 p.p. przez inną realizację RNG bootstrapu |
| Koszt V2b | +11,08% [10,32; 11,96] | +11,0778% [10,26; 11,955] | <0,03% | jw. |
| Koszt V3 | +5,26% [4,85; 5,72] | +5,2638% [4,80; 5,734] | <0,08% | jw. |
| Koszt per dziedzina (V2) | 16,76 / 8,89 / 22,49 / 15,31 / 13,94 / 4,02 / 18,93 | 16,76 / 8,89 / 22,50 / 15,31 / 13,94 / 4,02 / 18,93 | <0,05% | zgodne |
| Kalendarz V2b / V3 | 8 / 6 | 8 / 6 | 0% | zgodne |
| NFD V2/V2b/V3 | +0,0% | +0,0% [0,0; 0,0] | 0% | zgodne |
| Round-trip | 2752/2752 × 14 | 2752/2752 × 14 (+ suma długości kawalków) | 0% | zgodne |
| Martwe tokeny V3 / V0 / V2 | 4,88% / 1,95% / 2,01% | 4,875% / 1,95% / 2,0125% | <0,2% | zgodne po zaokrągleniu |
| Spójność data/CPV/przepis/kwota/znak (V0→V2) | 17,1→0 / 23,9→0 / 28,0→14,9 / 35,6→27,1 / 24,7→13,0 | 17,14→0 / 23,86→0 / 28,0→14,86 / 35,57→27,14 / 24,71→13,0 | <0,3% | własna reimplementacja metryki (max \|Δ\|=0,0024 tylko dla `rok` V0 przez limit ekstrakcji) |
| Kontekst — mediana ogłoszenia V0/V2/V2-16k | 3883 / 4536 / 5306 | 3883 / 4535,5 / 5305,5 | <0,03% | zgodne (zaokrąglenie) |
| Kwota `1 234 567,89 zł` | 7 → 13 → 11 → 6 | 7 → 13 → 11 → 6 | 0% | ten sam napis; `examples.json` zgodny |
| `w roku 2024 r.` — liczba kawałków V2/V2b | 6 / 6 | **7 / 7** | **+16,7%** | **błąd w raportach**: w tabeli i w `examples.json` lista ma 7 pozycji, podano 6. V0=4 i V3=5 są poprawne |
| „V3 tnie liczby na trójki od prawej” | zawsze | **4/15 przykładów łamie regułę** | — | zob. WAŻNE-1 |
| `pytest -q` | 59 passed | 59 passed (również w czystym venv z `requirements.txt`) | 0% | zgodne |
| Golden | 1240 zdań × 14 | 1240 × 14; mutacja 1 ID → test failuje, przywrócone | 0% | zgodne |
| Te same dane treningowe | p2, seed wspólny | ten sam plik, SHA-256 z manifestów zgodne | 0% | zgodne |

**`liczby_powtorzone: 27/29`** (27 pozycji odtworzonych w granicach zaokrąglenia /
z wyjaśnioną różnicą CI; 2 nieodtworzone: liczba kawałków V2/V2b w tabelach
raportów oraz twierdzenie o zawsze poprawnym grupowaniu V3).

### Wyjaśnienie „9 → 14” vs „7 → 13” (zadanie B)

W decyzjach właściciela (`tkxc_decyzje.md:5,20`) liczono tę samą kwotę
`1 234 567,89 zł` na tokenizatorze **v1** sprzed p2: 9 → 14 kawałków, a fragment
`1 234 567` pokazano jako `1|·|2|3|4|·|5|6|7` (9 kawałków). Wykonawca liczy ten
sam napis na nowej bazie p2: 7 → 13 (`tkx_c/results/examples.json`). Różnica
wynika z innej próbki treningowej i jest **jawnie zaznaczona** w obu raportach
(„kierunek ten sam”). Raporty są więc spójne z własnymi plikami `results/*.json`
z wyjątkiem błędu 6 zamiast 7 kawałków w kolumnie `w roku 2024 r.`.

---

## Znaleziska

### WAŻNE-1 — reguła „grupy po 3 cyfry od prawej” nie jest egzekwowana w kanonicznym enkoderze

- **Plik/linia:** `superbpe.py:60-70` (`split_groups3`) używana jest tylko w
  `pretokens()` (`superbpe.py:99-101`) podczas treningu etapu 1. W ścieżce
  kodowania `_encode_chunk_stage1` (`superbpe.py` ok. 380–390) i w eksporcie HF
  (`hf/variants/V3-32k/tokenizer.json` → `pre_tokenizer` = tylko `Split` +
  `ByteLevel`) funkcja ta **nie jest wywoływana**. Podział wynika wyłącznie
  z rang wymuszonych merges BPE na całym ciągu cyfr.
- **Poprawna reguła (protokół §9.7, decyzja `tkxc_decyzje.md:8`):** ciąg cyfr
  dzielimy od prawej na grupy po 3, z lewym ogonkiem 1–2 cyfry
  (`45233140 → 45|233|140`, `2024 → 2|024`).
- **Naruszenia na zestawie z zadania A2 (4/15):** `00-950` → `00│9│50`
  (oczekiwano `00│950`); `…poz. 1320` → `…│Ġ13│20` (oczekiwano `Ġ1│320`);
  `0012` → `00│12` (oczekiwano `0│012`); `123456789012345` →
  `12│34│56│789│01│23│45` (oczekiwano `123│456│789│012│345`).
- W słowniku jest wszystkie 1100 gołych grup, ale jako pojedynczy token wychodzi
  tylko 505/1000 trójek (pozostałe 495 wychodzą jako `spacja + grupa`, co jest
  poprawne). Błąd dotyczy głównie ciągów ≥4 cyfr.
- Skutek: twierdzenie raportu („żaden rok ani kod nie jest obcy”, „trójki od
  prawej”) jest prawdziwe dla lat i CPV, ale nie dla dowolnego dłuższego ciągu.
  Nie łamie zamrożonych progów akceptacji §7 (kalendarz płaski, 0 tokenów
  ≥4 cyfr, spójność lepsza niż V0), dlatego nie klasyfikuję tego jako BLOKER.

### WAŻNE-2 — V2b/V3 zaprojektowano na podstawie wyników `test`, nie `dev`

- Protokół §3: „Reguły (np. lista skrótów, próg cyfr) projektujemy na `dev`;
  `test` dotykamy tylko w pomiarach końcowych.”
- Historia commitów: `9bd1aa5` (19.11) — pomiary i raporty V0/V1/V2 na `test`;
  `ce72c3f` i `b44fee7` (20.11) — implementacja i pomiary V2b/V3; `d3a004e` —
  raporty. Uzasadnienie w raportach („Skąd część kosztu…”: duplikat `·roku·`,
  spacje w kwotach) wyprowadzone z obserwacji na `test`.
- Protokół §9.7 i raport §9 oznaczają to jako **post hoc** — jest to ujawnione,
  ale oznacza, że te same dokumenty `test` posłużyły zarówno do zaprojektowania
  reguł, jak i do końcowego pomiaru kosztu V2b/V3. Wnioski o V2b/V3 mają więc
  słabszą wartość dowodową niż V2.

### DROBNE-1 — błędna liczba kawałków w tabelach raportów

- `tkx_c/RAPORT_TKX_C.md:77-78` oraz `tkx_c/RAPORT_PROSTY.md:45-46`: w kolumnie
  `w roku 2024 r.` podano 6 kawałków dla V2 i V2b, podczas gdy wypisana lista
  (`w│·roku·│2│0│2│4│·r.` oraz `w│·roku│·2│0│2│4│·r.`) ma **7** pozycji.
  `tkx_c/results/examples.json` i mój pomiar dają 7. W tabeli podsumowawczej
  raportu (`RAPORT_TKX_C.md:282`) poprawnie podano 7/13 dla kwoty — niespójność
  dotyczy tylko tej jednej kolumny.

### DROBNE-2 — przedziały ufności bootstrapu różnią się nieznacznie

- Punkty estimate są identyczne co do 4 miejsc, ale moje CI są szersze
  o 0,05–0,1 p.p. (np. V2 [12,98; 15,09] vs [13,08; 15,07]). Wynika to z
  innej realizacji jednego generatora NumPy przy 1000 prób. Różnica <1%
  względem granic, nie wpływa na wnioski.

### DROBNE-3 — plan TKX-D: BPB na `dev`

- Decyzja właściciela mówi „BPB na `dev` + sonda”. Plan (`TKX_D_PLAN.md:19-23,129`)
  przewiduje BPB na walidacji `pack-07`, sondę na `dev`, a test TKX-A tylko
  jednokrotnie po decyzji. Duch reguły (nie wybierać na `test`) jest zachowany,
  ale literalnie BPB nie jest liczony na `dev` TKX-A. Pozostałe punkty listy
  (kandydaci, ta sama liczba bajtów, embeddingi w budżecie, sonda, Slayer
  z checkpointami, ≤5 USD / stop przy 4 / Destroy właściciel / brak klucza
  vast.ai) są obecne.

### Pozytywne potwierdzenia (C)

- Golden w CI **naprawdę łapie zmianę**: lokalna mutacja 1 ID w
  `tkx_c/golden/V2-32k.json` → `FAILED test_golden_sequences[V2-32k]`;
  stan przywrócony `git checkout --`, `git status` czysty.
- Wszystkie skrypty pomiarowe używają kanonicznego HF (`measure_lib.load_hf`);
  enkoder Python występuje wyłącznie w informacyjnym `python_parity.json`.
- `tokenizers==0.23.3` przypięte w `requirements.txt`; w nowym venv
  (`python -m venv` + `pip install -r requirements.txt numpy`) `pytest -q`
  → **59 passed**.
- `tkx_c/data/` i `audit/data/raw/` są w `.gitignore`; zero surowych plików
  w `git ls-files`.

---

```
REVIEW_RESULT
werdykt: PASS_Z_UWAGAMI
blokery: []
wazne: [WAŻNE-1: reguła grup po 3 od prawej nie jest egzekwowana w kodowaniu V3 (superbpe.py:60-70,99-101; hf/variants/V3-32k/tokenizer.json), 4/15 przykładów łamie regułę; WAŻNE-2: V2b/V3 projektowane na test, nie dev — ujawnione jako post hoc w protokole §9.7]
drobne: [DROBNE-1: RAPORT_TKX_C.md:77-78 i RAPORT_PROSTY.md:45-46 — 6 zamiast 7 kawałków dla V2/V2b w kolumnie „w roku 2024 r.”; DROBNE-2: CI bootstrapu różni się o 0,05-0,1 p.p. przez realizację RNG; DROBNE-3: TKX_D_PLAN.md — BPB na walidacji pack-07, nie na dev TKX-A]
liczby_powtorzone: 27/29
```

STATUS=REVIEW_GOTOWE werdykt=PASS_Z_UWAGAMI
