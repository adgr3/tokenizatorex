# PROTOKÓŁ TKX-V21-JSON (zapisany przed treningiem i przed commitem)

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

## 6. Czego ten protokół nie rozstrzyga

* Nie mówi, czy kandydat jest lepszy **jakościowo** — to wymaga treningu
  małych modeli (TKX-D) na co najmniej 3 seedach i pomiaru BPB.
* Fertility nie jest jakością modelu; mierzy koszt tokenizacji.
* 10% JSON to górna granica eksperymentu, nie rekomendacja dla produkcji.
* Brak dostępu do któregoś źródła = UNKNOWN, nie 0 i nie FALSE.
