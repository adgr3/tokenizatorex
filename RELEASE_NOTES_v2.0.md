# RELEASE NOTES — TOKENIZATOREX v2.0 (draft)

Status: DRAFT (wydanie po scaleniu PR i zgodzie właściciela).

## Co to jest v2.0

v2.0 to stan po TKX-A + TKX-C + test domenowy na tekstach urzędowych (BZP, Dz.U. ELI, KIO, samorząd, granty, JSON narzędzi, kontrola ogólna).

## Wariant domyślny i kandydaci

Z danych (`results/tkx_v2_fertility.json`): **V0-32k ma najniższą fertility na wszystkich 8 źródłach** (punktowo). CI rozdzielają V0 od V3 wyraźnie tylko na części źródeł; Dz.U. i granty mają n=12, więc ranking jest niepewny.

**Domyślny wariant v2.0 = V0-32k.** Ma `§` jako 1 token i round-trip 0/700 na dokumentach.

**V3-32k = wariant eksperymentalny z cięciem cyfr.** Wygrywa na identyfikatorach, kodach pocztowych, numerach BZP, skrótach i sygnaturach w wzorcach; przegrywa na datach i kwotach; nie ma `§` jako jednego tokena; normalizuje NFD→NFC. O1 FAIL: 4/700 dokumentów (3 BZP + 1 KIO, wszystkie NFD; 4/500 BZP ma NFD); O2 PASS. Na źródłach testowych traci vs V0: BZP +8,54%, Dz.U. +5,43%, KIO +1,87%, samorząd +4,39%, granty +6,18%, JSON narzędzi +2,76%, JSON BZP tabele +8,35%, ogólny +1,68% (liczone z fertility w `results/tkx_v2_fertility.json`).

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
- Bielik-1.5B-v3 (APT4) jest obecny w wynikach fertility; testy downstream nie wykonane. Tokenizer Bielika jest przeliczony w `results/tkx_v2_special_chars.json` i `results/tkx_v2_patterns.json` po zalogowaniu HF.
- Efektywność Rényiego (TokEval) — zaplanowana, nie policzona.

## Eksperyment v2.1-JSON (kandydat warunkowy V0J2-32k)

Dane: `results/tkx_v21_*.json` (gałąź `feat/tkx-v2-1-json`, cherry-pick do `feat/tkx-v2-0`). Reguła z protokołu: bramka JSON + brak regresji polskiego > 1% na 7 źródłach, `§` 1 token.

### Wynik według reguły oryginalnej (na pierwszym miejscu)

Wynik: **brak kandydata** (`results/tkx_v21_selection.json`: `winner = null`). V0J2-32k nie przeszedł bramki polskiej na grantach przy n=12 (reguła oryginalna).

### Poprawka 2 (granty 149)

Na grantach n=149 (`results/tkx_v21_selection_r2.json`): V0R 1,408412, V0J2 1,411248, delta +0,20% (próg ≤ 1%). CI 95% V0R [1,379812, 1,438095], V0J2 [1,382802, 1,440124]. Status: **kandydat warunkowy do TKX-D** (nie awans automatyczny).

### Zysk JSON (V0R vs V0J2, test)

| Miara | V0R-32k | V0J2-32k | Zmiana |
|---|---:|---:|---:|
| JSON tc1 test | 3,7376 | 2,8699 | -23,22% |
| JSON tc1 (same wywołania) | 4,8415 | 2,6698 | -44,86% |
| JSON narzędzia niewidziane | 9,1819 | 6,1485 | -33,04% |
| 10 wzorców JSON (suma tokenów) | 321 | 135 | -57,94% |
| 8 wzorców bez >50% pokrycia | 234 | 111 | -52,56% |

Przeciek wzorców: **częściowe pokrycie szkieletem** (2/10 > 50%, max 54,4%); 0 exact. Zysk na 10 wzorcach jest częściowo memorization wspólnego szkieletu, dlatego podany osobno dla 8 bez >50%.

### Held-out — rozbicie na formy

| Forma | Dokumenty | Tokeny V0 | Tokeny V0J2 | Zmiana |
|---|---:|---:|---:|---:|
| compact | 49 | 4034 | 2269 | -43,75% |
| pretty | 32 | 3212 | 2294 | -28,58% |
| result | 19 | 1284 | 1149 | -10,51% |
| razem | 100 | 8530 | 5712 | -33,04% |

Duża część zysku to wspólny szkielet wywołania (`<tool_call>`, `"name"`, `"arguments"`); na samych wynikach narzędzi zysk jest znacznie mniejszy.

### Koszt dla polskiego (V0J2 vs V0R, dev, delta %)

| Źródło | Delta % | Próg ≤ 1% |
|---|---:|---:|
| BZP ogłoszenia | +0,22% | TAK |
| Dz.U. ELI | +0,29% | TAK |
| KIO | -0,08% | TAK |
| Samorząd | +0,37% | TAK |
| Granty (n=149) | +0,20% | TAK |
| JSON BZP tabele | -1,32% | TAK |
| Ogólny web | +0,49% | TAK |

Tokeny specjalne (V0J5S) nie poprawiły wyniku względem V0J5 i nie dały kandydata; w 10 wzorcach JSON suma tokenów V0J5S to 144 vs V0J2 135 (`results/tkx_v21_wzorce.json`).

### Formaty dat, kwot i „§” — skrót

Pełne tabele per zapis: `tkx_v21/RAPORT.md`, sekcja 8a. Źródło: `results/tkx_v21_formaty.json` (40 dat, po 40 kwot na zapis, 9 form z „§”).

| Miara | V0 | V0J2 | V3 | Slayer | GPT-4o |
|---|---:|---:|---:|---:|---:|
| Daty (średnia) | 4,18 | 4,06 | 5,90 | 5,77 | 7,03 |
| Kwoty (średnia) | 5,56 | 5,41 | 4,94 | 6,27 | 5,83 |
| `§` (tokeny) | 1 | 1 | 2 | 1 | 1 |

Wniosek: po dodaniu JSON `§` pozostaje 1 tokenem w V0 i V0J2; średnia na datach V0J2 ≤ V0 + 0,1; kwoty bez istotnej zmiany. Kwoty dla „mln” i „tys.” są losowane w realistycznych zakresach (1–500 mln, 1–999 tys.).

## Plan v2.1 i TKX-D

- v2.1: naprawa `§` (V3), skróty prawne, tokeny JSON; mieszanka 10–30% tekstów urzędowych.
- TKX-D: wybór wariantu i rozmiaru słownika (16k/24k/32k) na małych modelach; ≥ 3 seedy; BPB.

## Weryfikacja

`pytest -q` zielone. `python scripts/sprawdz_liczby_v2.py` exit 0 na wszystkich raportach. `python scripts/generuj_raporty_v2.py --check` nie zmienia plików. Liczby w raportach pochodzą z `results/tkx_v2_*.json` i `results/tkx_v21_*.json`. Weryfikacja przez człowieka wymagana.
