# Korpus testu domenowego TOKENIZATOREX v2.0

Pełne teksty: `audit/data/raw/` (gitignore, poza gitem). W repo: ten plik + manifest (URL, data, domena, podział, słowa, SHA-256).

## Źródła

| # | Domena | Źródło | Status | Dokumenty | Słowa (test) |
|---|--------|--------|--------|-----------|--------------|
| 1 | przetargi (BZP) | spec1/data/test.jsonl (pole `text`), 500 ogłoszeń oczyszczonych | OK | 500 | 1 421 000 |
| 2 | akty prawne (Dz.U. 2026) | API ELI Sejmu, PDF | OK (limit 20) | 20 | 39 546 |
| 3 | orzeczenia KIO | UZP wyszukiwarka, 2026 | OK | 110 | 153 324 |
| 4 | samorząd (uchwały) | dziennik urzędowy woj. śląskiego (ELI) | OK | 400 | 116 864 |
| 5 | granty | NIW (strony + PDF) | OK (limit 20) | 20 | 37 969 |
| 6 | JSON narzędzi | tc1/dane/test.jsonl | OK | 200 | 25 645 |
| 7 | kontrola ogólna | korpus TKX-A `web` (HPLT, test split) | OK | 421 | 155 005 |

Uwaga: pełne teksty nie trafiają do gita (zasada nr 2). W repo tylko manifest i metryki.

## Przeciek

13-gramy znaków/słów korpusu domenowego vs próbka treningowa tokenizera (HPLT 400 MB) — do wykonania po zamrożeniu korpusu.
Wynik: do uzupełnienia w RAPORT_TEST_DOMENOWY.md. Próg stopu: > 20% dokumentów z trafieniem.

## Licencje / status prawny

Dokumenty urzędowe (Dz.U., Monitor Polski, BZP, dzienniki urzędowe województw) są publiczne.
Orzeczenia KIO są publiczne. Ogłoszenia konkursów z BIP/NIW są publiczne.
Teksty z HPLT/FineWeb-2 na licencji ODC-By; Wikipedia CC BY-SA.
Brak danych osobowych: spec1 już oczyszczony; pozostałe źródła przetwarzane własnym kodem (bez NERGAL).
PY