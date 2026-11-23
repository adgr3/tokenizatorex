# RELEASE NOTES — TOKENIZATOREX v2.0 (draft)

Status: DRAFT (wydanie po scaleniu PR i zgodzie właściciela).

## Co to jest v2.0

v2.0 to stan po TKX-A + TKX-C + test domenowy na tekstach urzędowych (BZP, Dz.U. ELI, KIO, samorząd, granty, JSON narzędzi, kontrola ogólna).

## Wariant domyślny i kandydaci

Z danych (`results/tkx_v2_fertility.json`): **V0-32k ma najniższą fertility na wszystkich 8 źródłach** (punktowo). CI rozdzielają V0 od V3 wyraźnie tylko na części źródeł; Dz.U. i granty mają n=12, więc ranking jest niepewny.

**Domyślny wariant v2.0 = V0-32k.** Ma `§` jako 1 token i zachowuje round-trip NFC/NFD w próbce syntetycznej.

**V3-32k = wariant eksperymentalny z cięciem cyfr.** Wygrywa na identyfikatorach, kodach pocztowych, numerach BZP, skrótach i sygnaturach w wzorcach; przegrywa na datach i kwotach; nie ma `§` jako jednego tokena; normalizuje NFD→NFC (4 błędy round-trip w próbie syntetycznej). Na źródłach testowych traci vs V0: BZP +8,54%, Dz.U. +5,43%, KIO +1,87%, samorząd +4,39%, granty +6,18%, JSON narzędzi +2,76%, JSON BZP tabele +8,35%, ogólny +1,68% (liczone z fertility w `results/tkx_v2_fertility.json`).

Ostateczny wybór dopiero po TKX-D (małe modele, BPB, ≥ 3 seedy). Fertility to warunek konieczny, nie dowód jakości (Schmidt i in.).

## Znane wady

Zob. `tkx_v2/ZNANE_WADY.md`. Uwaga: porównanie martwych tokenów ze Slayerem nie jest bezpośrednie (słownik polsko-angielski).

## Jak sprawdzić samemu

```bash
python scripts/sprawdz_sam.py "Twój tekst."
python scripts/sprawdz_sam.py --wszystkie "Twój tekst."
```

Domyślnie lokalne tokenizery TOKENIZATOREX + Slayer; `--wszystkie` dodaje zewnętrzne (wymaga cache/logowania).

## Nie sprawdzono (wprost)

- Przeciek względem próbki treningowej HPLT (13-gramy) — nie wykonano.
- Bielik-1.5B-v3 (APT4) jest obecny w wynikach fertility; testy downstream nie wykonane. W tym środowisku tokenizer Bielika jest gated/brak cache dla recompute znaków specjalnych — oznaczono jako UNKNOWN w `results/tkx_v2_special_chars.json`.
- Efektywność Rényiego (TokEval) — zaplanowana, nie policzona.

## Plan v2.1 i TKX-D

- v2.1: naprawa `§` (V3), skróty prawne, tokeny JSON; mieszanka 10–30% tekstów urzędowych.
- TKX-D: wybór wariantu i rozmiaru słownika (16k/24k/32k) na małych modelach; ≥ 3 seedy; BPB.

## Weryfikacja

`pytest -q` zielone. `python scripts/sprawdz_liczby_v2.py` exit 0. Liczby w raportach pochodzą z `results/tkx_v2_*.json`. Weryfikacja przez człowieka wymagana.
