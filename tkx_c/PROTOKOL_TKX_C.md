# PROTOKÓŁ TKX-C — poprawki TOKENIZATOREX i warianty słownika

Wersja: 1.0 (zamrożona przed treningiem i pomiarami) · Data: 19.11.2026
Repo: `adgr3/tokenizatorex`, gałąź `feat/tkx-c-19-11`, baza `main` =
`86d45eeddbd6fa5140ba3164503f66259f2bd0fc` (po scaleniu TKX-A, PR #2).
Wykonawca: agent TKX-C. Niezależne rundy 2/3: Codex i Grok (osobne zadania).

Ten dokument jest zamrożony **przed** treningiem wariantów. Każda zmiana po
rozpoczęciu treningu/pomiarów trafia do sekcji „Zmiany po fakcie”, a wyniki nią
dotknięte są oznaczone jako **post hoc**.

## 1. Cel

Naprawić fundament przed treningiem modelu 150M:
1. **A1 — pojedyncze cyfry:** każda cyfra osobnym pretokenem, tokeny
   wielocyfrowe nie powstają, superwordy nie zawierają cyfr; lata 2015–2035
   mają **stały** koszt.
2. **A2 — NFC w potoku:** normalizacja przed kodowaniem i w danych treningowych,
   w jednej funkcji; NFD nie zwiększa liczby tokenów.
3. **A3 — jeden kanoniczny enkoder:** eksport HF (`tokenizer.json`) jest
   tokenizerem modelu; jakość = `decode(encode(x)) == x` + zamrożone sekwencje
   referencyjne. Zgodność z enkoderem Pythona jest tylko informacyjna.

Dodatkowo: warianty słownika 16k/24k/32k (SuperBPE i base), bez wyboru po
fertility; wybór w TKX-D na małych modelach (BPB + sonda).

## 2. Warianty (jedna zmiana naraz)

| Wariant | Zmiana | Słownik | Etap 2 |
|---|---|---:|---:|
| V0 | odtworzenie v1 (te same dane/seed/ustawienia) | 32k | 20k |
| V1 | V0 + pojedyncze cyfry | 32k | 20k |
| V2 | V1 + NFC w potoku | 32k | 20k |
| V2-24k | V2, słownik 24k, t = 15k | 24k | 15k |
| V2-16k | V2, słownik 16k, t = 10k | 16k | 10k |
| V2-base-32k | V2 bez etapu 2 | 32k | — |
| V2-base-24k | V2-base-32k obcięty do 24k | 24k | — |
| V2-base-16k | V2-base-32k obcięty do 16k | 16k | — |

V0: jeśli nie da się odtworzyć v1 bit w bit, zapisujemy dlaczego, a **wszystkie
warianty, łącznie z nowym V0, trenujemy na tej samej nowej próbce** (ten sam
plik, seed, podział). V0 jest wtedy nową bazą odniesienia, nie kopią v1.

## 3. Dane treningowe

Te same co v1: HPLT v3 PL (`SlayerLab/hplt-v3-pl-cleaned`), shard
`european_hplt_v3_pl_bin8_5_p0.parquet`; `prepare_data.py` z seed 42, 300 MB
etapu 1; etap 2 = pierwsze 100 MB tego samego `train.txt` (`read_blocks`).
Jeśli shard niedostępny lub odtworzenie niemożliwe: jedna nowa próbka 300 MB +
100 MB z tego samego shardu, używana przez **wszystkie** warianty; powód w
raporcie i w `tkx_c/results/data_source.json`.

Podział na `dev`/`test` pochodzi wyłącznie z `audit/data/MANIFEST.json`
(TKX-A). Reguły (np. lista skrótów, próg cyfr) projektujemy na `dev`;
`test` dotykamy tylko w pomiarach końcowych.

## 4. Implementacja (opcje wyłączane, domyślnie v1)

* `SuperBPETokenizer(digits="single")`: `WORD_PATTERN_SINGLE_DIGITS`
  (`\p{N}{1,3}` → `\p{Nd}`), a w etapie 2 `allowed()` odrzuca każdy merge,
  którego wynik zawiera cyfrę (`\p{Nd}`).
* `SuperBPETokenizer(normalize="nfc")`: `normalize_text()` wywoływane w
  `encode_ordinary()`, `encode()` i w liczeniu pretokenów/fragmentów treningu.
* Domyślne `digits="grouped"`, `normalize="none"` = zachowanie v1; pliki v1
  muszą się ładować bez zmian.
* Eksport HF: `normalizers.NFC()` dla V2; `pre_tokenizers.Digits(
  individual_digits=True)` albo równoważny regex dla V1+; kanoniczny enkoder to
  eksport HF.

## 5. Zamrożone sekwencje referencyjne (A3)

`tkx_c/golden/`:
* ≥ 1000 zdań z `dev` (7 dziedzin urzędowych + `web`), deterministycznie
  (seed 20261119, sortowanie po `id`);
* zapisy z załącznika A audytu (kwoty, daty, przepisy, CPV, znaki sprawy,
  uchwały, NIP syntetyczny, adres, e-mail syntetyczny);
* lata 2015–2035 w szablonie `w roku RRRR r. zadanie`;
* `\n\n`, tabulatory, emoji, mieszany PL–EN.
Dla każdego wariantu: sekwencje ID z **kanonicznego eksportu HF** + SHA-256
pliku `tokenizer.json`. Test CI (`tkx_c/test_golden.py`) failuje przy każdej
zmianie, która zmienia którąkolwiek sekwencję, dopóki pliki referencyjne nie
zostaną świadomie zaktualizowane.

## 6. Pomiary (split `test`)

Bootstrap po dokumentach 1000×, seed 20261119, jeden generator NumPy
(`common.bootstrap_indices`). Wszystkie liczby do `tkx_c/results/*.json`.

1. **Fertility i bajty/token** na 15 dziedzinach, 95% CI. Raportowane, **nie**
   służą do wyboru wariantu.
2. **Prawdziwy koszt cyfr:** V1 vs V0, % tokenów na dziedzinę, z CI; porównanie
   z przedziałem audytu (dolna Codex, górna Grok) i wyjaśnienie różnic.
3. **Kalendarz:** `w roku RRRR r. zadanie` dla 2015–2035; oczekiwane stałe
   koszty w V1+; wykres V0 vs V1.
4. **Spójność zapisów (H3/H4):** odsetek innych podziałów niż najczęstszy dla
   kwot, dat, przepisów, `Dz.U.`, CPV, znaków spraw; V0 vs V1+.
5. **NFD:** wzrost tokenów po NFD, V1 vs V2; oczekiwane ~0% w V2.
6. **Kanoniczny HF:** round-trip na tekście po NFC na **wszystkich** `test`;
   zgodność z Pythonem informacyjnie (% pretokenów z identyczną listą kawałków).
7. **Słownik:** martwe/rzadkie tokeny; udział tokenów z cyframi (V0) vs
   zwolnione miejsca (V1+); 50 najczęstszych nowych tokenów.
8. **Długość dokumentów a kontekst:** kanoniczny HF, pełne dokumenty bez cięcia
   20k (jeśli pełne teksty są dostępne; inaczej UNKNOWN z powodem), mediana,
   p90, % w 2048/4096 dla przetargów, uchwał, grantów, KIO.
9. **Embeddingi 150M:** 16k/24k/32k, d=768, powiązane i niepowiązane.

## 7. Progi akceptacji (zamrożone)

* **A1:** koszt lat **stały** dla 2015–2035 (ten sam token count w szablonie);
  0 tokenów wielocyfrowych w słowniku i w kodowaniu; spójność zapisów z cyframi
  lepsza niż V0 (H3/H4).
* **A2:** wzrost tokenów po NFD ≤ **1%** w V2 (na 7 dziedzinach urzędowych).
* **A3:** round-trip 100% na `test`; golden sequences przechodzą w CI.
* **Koszt cyfr** (V1 vs V0) podany z CI dla każdej dziedziny. **Nie ma progu
  „za drogo”** — decyzja właściciela po raporcie, koszt i zysk obok siebie.
* **Wybór słownika:** brak wyboru w TKX-C; 16k/24k/32k tylko zbudowane i
  opisane. Wybór w TKX-D (BPB + sonda, budżet z embeddingami).

## 8. Ograniczenia z góry znane

* Fertility ≠ jakość modelu; wybór słownika wyłącznie w TKX-D.
* V0 może nie odtworzyć v1 bit w bit (inna wersja polars/HF, inny shard);
  wtedy nowa baza i jawny powód.
* Pełne dokumenty bez cięcia 20k mogą być niedostępne dla części dziedzin;
  wtedy UNKNOWN z powodem, bez zgadywania.
* NFD dotyczy głównie PDF; w korpusie TKX-A tylko 2 dokumenty NFD.
* Golden sequences są regresją, nie dowodem jakości modelu.
* Nie trenujemy modeli 150M; tylko przygotowujemy warianty i plan TKX-D.

## 9. Zmiany po fakcie

(brak — protokół zamrożony przed treningiem i pomiarami)
