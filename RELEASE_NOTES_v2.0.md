# RELEASE NOTES — TOKENIZATOREX v2.0 (draft)

Status: DRAFT (wydanie po scaleniu PR i zgodzie właściciela).

## Co to jest v2.0

v2.0 to stan po TKX-A (fertility, 1. z 20 tokenizerów na polskim tekście ogólnym) + TKX-C (cyfry, NFC, stabilny enkoder,
eksport HF) + **test domenowy** na tekstach, których tokenizer nie widział (przetargi, akty prawne, KIO, samorząd,
granty, JSON narzędzi, kontrola ogólna).

## Kandydat (hipoteza, do potwierdzenia w TKX-D)

Kandydatem do modelu 150M jest **V3-32k** — najlepsza kompresja na tekstach urzędowych i poprawne cięcie cyfr
(grupy po 3 od prawej, Singh & Strouse). Hipoteza do potwierdzenia na małych modelach (TKX-D): BPB + testy domenowe
na 30M/60M z ≥ 3 seedami. Fertility to warunek konieczny, nie dowód jakości (Schmidt i in.).

## Znane wady

Uwaga: porównanie martwych tokenów ze Slayerem nie jest bezpośrednie — Slayer ma słownik polsko-angielski,
więc na polskim korpusie część jego słownika z natury jest nieużywana.

Zob. `tkx_v2/ZNANE_WADY.md`: „§” w V3, skróty (`Dz. U.`, `Pzp`, `tj.`), JSON, angielski, artefakty SuperBPE,
martwe tokeny.

## Jak sprawdzić samemu

```bash
python scripts/sprawdz_sam.py "Twój tekst."
```

Skrypt koduje podany tekst wszystkimi wariantami i Slayerem i drukuje segmentację.

## Nie sprawdzono (wprost)

- Przeciek względem próbki treningowej HPLT (13-gramy) — nie wykonano (brak 400 MB lokalnie).
- APT4 (Bielik v3) — gated, brak cache/tokenizera lokalnie (UNKNOWN).
- Efektywność Rényiego (TokEval) — zaplanowana, nie policzona.

## Plan v2.1 i TKX-D

- v2.1: naprawa „§” (dopisanie na końcu scaleń, Herold i in.), skróty prawne, tokeny JSON; trening tokenizera
  na mieszance 10–30% tekstów urzędowych.
- TKX-D: wybór wariantu i rozmiaru słownika (16k/24k/32k) na małych modelach; strojenie lr osobno dla 30M.

## Weryfikacja

`pytest -q` zielone. Liczby w raportach z `results/tkx_v2_*.json` (skrypt `scripts/sprawdz_liczby_v2.py`).
Weryfikacja przez człowieka wymagana (regulamin Fabryki).
PY