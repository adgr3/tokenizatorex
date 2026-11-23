# PROTOKÓŁ TKX-V21-JSON (zapisany przed treningiem (commit 5d1e50d); aneksy: Poprawka 1 (po treningu, przed pomiarem), Poprawka 2 (po fakcie))

Data: 23.11.2026 · gałąź `feat/tkx-v2-1-json` · commit bazowy `688e0021`
Seed: **20261123**, `PYTHONHASHSEED=0`, bootstrap 1000× po dokumentach.

## 1. Pytanie

Czy domieszka JSON-a do danych treningowych tokenizera (2%, 5%, 10% bajtów)
zmniejsza liczbę tokenów na wywołaniach narzędzi, **nie pogarszając polszczyzny
o więcej niż 1%** na żadnym źródle z testu domenowego v2?

Wynik w każdą stronę jest wynikiem: „domieszka pomaga”, „domieszka kosztuje
polszczyznę o X%” albo „brak kandydata”.

## 2. Dane treningowe

* HPLT p2 (`european_hplt_v3_pl_bin8_5_p2.parquet`) → `stability_train.txt`,
  400 160 750 B, SHA-256 `b0e7447cf94f8e0fa03edfeb3f6f10a2e63c9e32037f086cf5a434709ae6e558`.
  To dokładnie ten sam plik, na którym powstał V0 (pierwsze 200 000 wierszy p2,
  `strip`, linia po linii; patrz `audit/stability.py`).
* V0: `train.py baseline --data stability_train.txt --vocab 32000 --stage1-mb 300
  --digits grouped --normalize none`, potem
  `train.py superbpe --from <baseline> --transition 20000 --vocab 32000
  --stage2-mb 100 --max-words 4`. To parametry z README i metadanych V0.
* JSON do treningu: wyłącznie `tc1/dane/train.jsonl` (800, tury asystenta/narzędzia)
  oraz **własny generator** `tkx_v21/generuj_json.py` (50 narzędzi: 40 treningowych,
  10 tylko held-out). Zakazane i nieużywane: `tc1/dane/test.jsonl`,
  `spec1/data/test.jsonl`, `tkx_v2/wzorce.json`.
* Mieszanki: 300 MB HPLT (ten sam prefiks co V0) + JSON wstawiony równomiernie
  w 120 miejscach, tak by JSON stanowił **2 / 5 / 10% bajtów całości**
  (`V0J2-32k`, `V0J5-32k`, `V0J10-32k`). Dokładne bajty i SHA w
  `tkx_v21/dane/MANIFEST_DANYCH.json`.
* `V0J5S-32k` = `V0J5-32k` + 6 atomowych tokenów specjalnych
  (`<|system|>`, `<|uzytkownik|>`, `<|asystent|>`, `<|narzedzie|>`,
  `<tool_call>`, `</tool_call>`). Słownik 32 006 zamiast 32 000 — raportowane
  osobno; **nie jest kandydatem w regule wyboru**, bo jego zysk pochodzi
  z tokenów specjalnych, a nie ze słownika JSON.
* Odtworzenie V0 (`V0R-32k`) jest udane, jeśli SHA-256 pliku `superbpe.json`
  jest identyczny z V0 (`7ba5543d…5e5e43`); jeśli nie — wszystkie porównania
  idą względem `V0R`, a różnica jest raportowana.

## 3. Zbiory oceny

* **Dev (wybór wariantu, liczony dla wszystkich wariantów):**
  `tc1/dane/dev.jsonl` (100) + `json_generic_heldout_dev` (100, narzędzia niewidziane).
* **Test (liczony raz, po wyborze):**
  `tc1/dane/test.jsonl` (200, narzędzia widziane w tc1 train) +
  `json_generic_heldout_test` (100, narzędzia niewidziane).
* **Polski (warunek, nie optymalizacja):** te same 7 źródeł co w v2
  (BZP 500 z `spec1/data/test.jsonl`, Dz.U. ELI, KIO, samorząd, granty,
  `json_bzp_tabele`, ogólny web) + kontrola. Każde źródło z 95% CI.
* **Round-trip:** po 100 dokumentów z każdego z 7 źródeł (700 łącznie).
* **Przeciek:** każda linia JSON z testu vs dane treningowe — dokładnie oraz
  13-gramy znaków; dokument z pokryciem > 50% to przeciek (raportowany).

## 4. Miary

* **Fertility** = suma tokenów / suma słów (`str.split()`), jak w v2.
  Dla JSON raportujemy też łączną liczbę tokenów i tokeny/przykład.
* **95% CI:** bootstrap po dokumentach, 1000 prób, seed 20261123.
* **Wzorce urzędowe:** 155 pozycji z `tkx_v2/wzorce.json` (12 kategorii,
  w tym 10 wzorców JSON); liczba tokenów na wzorzec, średnia per kategoria,
  segmentacja tekstowa dla 2 przykładów JSON.
* **„§”:** `len(encode("§")) == 1` (nie „jest w słowniku”).
* **Martwe tokeny:** tokeny słownika o zerowej częstości na korpusie oceny
  (7 źródeł + JSON test); tokeny specjalne wyłączone.
* **Tokeny specjalne:** osobna tabela dla V0J5S (`<tool_call>`, `</tool_call>`,
  role) — czy każdy jest 1 tokenem.

## 5. Reguła wyboru (z góry, bez podglądania testu)

1. Kandydaci: `V0J2-32k`, `V0J5-32k`, `V0J10-32k`.
2. Wygrywa kandydat z **najniższą fertility JSON na dev** (łącznie
   tc1 dev + generic dev; remis rozstrzyga niższa fertility na tc1 dev).
3. Warunek konieczny: na **każdym** polskim źródle fertility (punktowo)
   ≤ **1,01 × fertility V0R** oraz `len(encode("§")) == 1` w wybranym wariancie.
4. Jeśli żaden kandydat nie spełnia warunku 3 — **brak kandydata**;
   raportujemy koszt polszczyzny per źródło (najmniejszy koszt i jego wartość).
5. `V0J5S-32k` nie wchodzi do reguły; jest raportowany obok jako ablacja
   tokenów specjalnych.
6. Test JSON liczymy **raz**, dla wszystkich wariantów, po wybraniu kandydata.
   Nie zmieniamy reguły po zobaczeniu testu.

## 6. Poprawka 1 (po treningu, przed pomiarem dev/test (deklaracja))

Data: **23.11.2026, 15:23** — po zakończeniu treningu wariantów (V0J2 ok. 15:06,
V0J10 ok. 15:16), przed uruchomieniem pomiarów dev/test.

**Co zmieniono.** Generator `tkx_v21/generuj_json.py` dostał osobne słownictwo
dla zbioru held-out: `HELDOUT_CITIES`, `HELDOUT_PROPERTIES`, funkcje
`_heldout_value`, `_heldout_specs`, `_heldout_example`. Przykłady held-out są
teraz tylko wywołaniami compact/pretty i odpowiedziami narzędzia, z innymi
nazwami pól i wartościami niż w treningu; nie zawierają definicji schematów.
Nazwy 10 narzędzi held-out były rozdzielone już wcześniej.

**Dlaczego.** Pierwsza wersja held-out korzystała z tych samych szablonów co
trening: 98/100 dokumentów miało >50% pokrycia 13-gramów (maks. 90,3%).
To nie były kopie (0 exact), ale wspólny szkielet schema/JSON. Po zmianie:
maks. pokrycie **54,4%** na 10 wzorcach JSON (świadomie wspólny szkielet
wywołania) i **41,7%** na held-out; 0 dokumentów korpusu >50%.

**Co się nie zmieniło.** `json_train.txt` ma ten sam SHA-256
`427acf858...` przed i po (`tkx_v21/MANIFEST_DANYCH.json`); warianty
V0J2/V0J5/V0J10 nie były ponownie trenowane. Zmieniły się wyłącznie pliki
`json_generic_heldout_dev.jsonl` i `json_generic_heldout_test.jsonl`
(nowe wartości, ten sam podział 100/100 i te same 10 narzędzi).
To poprawka **przed** pomiarem, nie po zobaczeniu testu (deklaracja).

## 7. Poprawka 2 (po fakcie, jawnie)

Data: **23.11.2026, po pierwszym pomiarze i po regule wyboru**, przed
ostatecznym raportem.

**Powód.** Jedynym źródłem, które zablokowało V0J2, były granty: 12 dokumentów,
+3,75%, CI pokrywają się z V0R. Właściciel wskazał większy zbiór
`D:\VPS\fabryka\spec1\data\zbiorB.jsonl`: **149 ogłoszeń** z lipca–listopada
2026, 120 251 słów, dane osobowe zamaskowane. Tylko odczyt; do repo trafiają
wyłącznie liczby (`results/tkx_v21_granty149.json`).

**Metoda:** ta sama co w protokole — suma tokenów / suma słów (`str.split()`),
bootstrap 1000× po dokumentach, seed 20261123.

**Wynik granty 149 (fertility [95% CI]):**

| tokenizer | fertility [CI] | Δ vs V0R |
|---|---:|---:|
| V0R-32k | 1,4084 [1,3798–1,4381] | — |
| V0J2-32k | 1,4112 [1,3828–1,4401] | +0,20% |
| V0J5-32k | 1,4179 [1,3902–1,4469] | +0,67% |
| V0J10-32k | 1,4244 [1,3962–1,4534] | +1,13% |
| V0J5S-32k | 1,4179 [1,3902–1,4469] | +0,67% |
| Slayer1B-1.08 | 1,6770 [1,6501–1,7052] | +19,07% |
| GPT-4o-o200k | 2,3894 [2,3654–2,4151] | +69,65% |

**Reguła z grantami 149:** V0J2 przechodzi wszystkie 7 źródeł (granty +0,20%,
najgorsze pozostałe +0,49%); V0J5 nadal odpada na ogólnym webie (+1,01%);
V0J10 odpada na BZP, samorządzie, grantach i ogólnym webie. Wynik:
**kandydat warunkowy V0J2-32k**, do potwierdzenia w TKX-D.

**Ważne:** to jest wynik **obok** oryginalnego protokołu, nie zmiana reguły.
Pierwszy wynik pozostaje „brak kandydata” według grantów 12; kandydat
warunkowy **nie jest wybrany według protokołu** i nie wolno go tak przedstawiać.

## 8. Czego ten protokół nie rozstrzyga

* Nie mówi, czy kandydat jest lepszy **jakościowo** — to wymaga treningu
  małych modeli (TKX-D) na co najmniej 3 seedach i pomiaru BPB.
* Fertility nie jest jakością modelu; mierzy koszt tokenizacji.
* 10% JSON to górna granica eksperymentu, nie rekomendacja dla produkcji.
* Brak dostępu do któregoś źródła = UNKNOWN, nie 0 i nie FALSE.
