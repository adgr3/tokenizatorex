# TOKENIZATOREX ZOO — raport przed postem v2.0

Gałąź `feat/tkx-zoo` od `f12fc2c` · commit autora `adgr3` · seed 20261123, `PYTHONHASHSEED=0`, bootstrap 1000× po dokumentach · `encode(..., add_special_tokens=False)`.
Wszystkie liczby poniżej wygenerował `tkx_zoo/raport.py` z plików `results/tkx_zoo_*.json`. Wyniki V0, V0J2, Slayera, Bielika 1.5B, APT3 i GPT-4o zostały skopiowane z istniejących plików (pole `origin` w `tkx_zoo_fertility.json`) — bez przeliczania.

## Po ludzku (10 zdań)

1. Na 8 polskich źródłach najmniej tokenów na słowo daje **V0-32k** — na BZP ma 1,4304.
2. 6 z 10 tabel wygrywa V0-32k; na 3_kio, 6_json_narzedzia, json_bzp_tabele, json_generic_heldout_test lepszy jest V0J2-32k.
3. Na ośmiu polskich źródłach żaden PLLuM ani Bielik nie był tańszy niż V0 (0 przypadki); na JSON held-out takich przypadków jest 6 (np. PLLuM 8B 6,6921 vs V0 9,1819). Najbliżej V0 na BZP jest Aster-0.5B z 1,7313 przy słowniku 32 000.
4. PLLuM 4B ma dokładnie taką samą fertility jak Gemma 3, a PLLuM 12B jak Mistral Nemo — choć pliki `tokenizer.json` mają inne hashe (PLLuM dodał tokeny, na tych tekstach nie zmieniły liczby tokenów).
5. Bielik 4.5B v3 daje identyczną fertility jak Bielik 1.5B v3 (1,9556 na BZP) przy słowniku 32 000 — to inny plik, ten sam efekt.
6. Cyfry: PLLuM 4B/12B, Gemma 3 i Mistral Nemo tną je pojedynczo; PLLuM 8B i GPT-4o po trzy; V0, V0J2, Slayer i Aster w grupach 1–3.
7. Znak „§” jest jednym tokenem w 14 tokenizerach (m.in. PLLuM-4B, PLLuM-8B, PLLuM-12B, Bielik-11B-v3.1); nie jest w Bielik-4.5B-v3, Bielik-1.5B-v3, APT3-1B (3, 3, 2 tokeny).
8. Słownik to realny koszt: PLLuM 4B (262 147) przy d_model 768 zajmuje 201,33 M parametrów, czyli 134,2% modelu 150M; V0 (32 000) to 24,58 M (16,4%).
9. Martwe tokeny: od 8,1% (V0-32k) do 93,4% (PLLuM-4B) słownika nie użyt ani razu.
10. Round-trip na 700 dokumentach jest bezstratny dla 15 tokenizerów; wyjątki: Aster-0.5B (4 błędów), APT3-1B (654 błędów).

## Tabela fertility (8 źródeł v2 + 2 dodatkowe)

| źródło | PLLuM-4B | PLLuM-8B | PLLuM-12B | Bielik-11B-v3.1 | Bielik-4.5B-v3 | Aster-0.5B | EuroLLM-1.7B | Mistral-Nemo | Gemma-3-4B | DanielK-t1-pl-polish-32k | DanielK-t2-pl-cnc-32k | V0-32k | V0J2-32k | Slayer-v6 | Bielik-1.5B-v3 | APT3-1B | GPT-4o-o200k |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **słownik** | 262 147 | 128 259 | 131 072 | 32 128 | 32 000 | 32 000 | 128 000 | 131 072 | 262 145 | 32 768 | 32 768 | 32 000 | 32 000 | 32 768 | 32 000 | 31 980 | 200 019 |
| 1_bzp | 2,3988 | 2,9169 | 2,6591 | 3,3050 | 1,9556 | 1,7313 | 2,2408 | 2,6591 | 2,3988 | 1,7680 | 1,7687 | 1,4304 | 1,4335 | 1,8096 | 1,9556 | 1,6625 | 2,5586 |
| 2_du_eli | 2,3432 | 2,6773 | 2,4420 | 3,0437 | 1,9048 | 1,6245 | 2,1522 | 2,4420 | 2,3432 | 1,6835 | 1,6846 | 1,4635 | 1,4677 | 1,7710 | 1,9048 | 1,5325 | 2,3790 |
| 3_kio | 2,2117 | 2,7476 | 2,4355 | 3,1436 | 1,8141 | 1,6071 | 2,0783 | 2,4355 | 2,2117 | 1,6370 | 1,6374 | 1,3983 | 1,3972 | 1,7153 | 1,8141 | 1,5808 | 2,3899 |
| 4_samorzad | 2,5278 | 2,7260 | 2,6230 | 3,2611 | 2,3102 | 1,8479 | 2,4935 | 2,6230 | 2,5278 | 1,7638 | 1,7638 | 1,5502 | 1,5560 | 1,9798 | 2,3102 | 1,7707 | 2,4442 |
| 5_granty | 2,4710 | 2,8370 | 2,6117 | 3,2948 | 2,1853 | 1,8632 | 2,3013 | 2,6117 | 2,4710 | 1,9133 | 1,9095 | 1,7455 | 1,8110 | 2,0288 | 2,1853 | 2,0401 | 2,5107 |
| 6_json_narzedzia | 4,0964 | 4,0016 | 4,2437 | 4,6790 | 4,3242 | 4,0152 | 4,3770 | 4,2437 | 4,0964 | 4,4286 | 4,4274 | 3,7376 | 2,8699 | 3,9848 | 4,3242 | 3,8109 | 3,7541 |
| 7_ogolny | 2,0738 | 2,5295 | 2,2505 | 2,8790 | 1,6611 | 1,5963 | 1,8625 | 2,2505 | 2,0738 | 1,6754 | 1,6764 | 1,4117 | 1,4186 | 1,6724 | 1,6611 | 1,5568 | 2,1886 |
| json_bzp_tabele | 3,8511 | 3,9723 | 3,9208 | 4,7747 | 3,4276 | 3,0800 | 3,6738 | 3,9208 | 3,8511 | 3,0972 | 3,1996 | 2,7357 | 2,6996 | 3,1794 | 3,4276 | 2,9216 | 3,6116 |
| granty_149 | 2,2725 | 2,7459 | 2,4704 | 3,1484 | 1,7834 | 1,5941 | 2,0519 | 2,4704 | 2,2725 | 1,6480 | 1,6487 | 1,4084 | 1,4112 | 1,6770 | 1,7834 | 1,5679 | 2,3894 |
| json_generic_heldout_test | 7,7890 | 6,6921 | 7,1948 | 7,8956 | 8,7772 | 8,7072 | 8,5113 | 7,1948 | 7,7890 | 9,5565 | 9,5565 | 9,1819 | 6,1485 | 7,7051 | 8,7772 | 9,0000 | 6,4586 |

Zwycięzcy per źródło: 1_bzp=V0-32k (1,4304); 2_du_eli=V0-32k (1,4635); 3_kio=V0J2-32k (1,3972); 4_samorzad=V0-32k (1,5502); 5_granty=V0-32k (1,7455); 6_json_narzedzia=V0J2-32k (2,8699); 7_ogolny=V0-32k (1,4117); json_bzp_tabele=V0J2-32k (2,6996); granty_149=V0-32k (1,4084); json_generic_heldout_test=V0J2-32k (6,1485).
Dla V0J2 na KIO i `json_bzp_tabele` różnica jest mniejsza niż szerokość CI — liczby są w `results/tkx_zoo_fertility.json`.

## V0-32k vs Aster-0.5B (32k vs 32k)

| źródło | V0-32k [95% CI] | Aster-0.5B [95% CI] | przedziały rozłączne? |
|---|---:|---:|:---:|
| 1_bzp | 1,4304 [1,4224–1,4391] | 1,7313 [1,7214–1,7427] | tak |
| 2_du_eli | 1,4635 [1,3640–1,5807] | 1,6245 [1,5387–1,7374] | nie |
| 3_kio | 1,3983 [1,3739–1,4250] | 1,6071 [1,5772–1,6400] | tak |
| 4_samorzad | 1,5502 [1,5381–1,5609] | 1,8479 [1,8346–1,8596] | tak |
| 5_granty | 1,7455 [1,6744–1,8124] | 1,8632 [1,8096–1,9298] | nie |
| 6_json_narzedzia | 3,7376 [3,6239–3,8240] | 4,0152 [3,9058–4,1025] | tak |
| 7_ogolny | 1,4117 [1,3942–1,4297] | 1,5963 [1,5803–1,6131] | tak |
| json_bzp_tabele | 2,7357 [2,5610–2,9050] | 3,0800 [2,8859–3,2717] | nie |
| granty_149 | 1,4084 [1,3798–1,4381] | 1,5941 [1,5666–1,6219] | tak |
| json_generic_heldout_test | 9,1819 [7,9131–10,6830] | 8,7072 [7,4510–10,1776] | nie |

## V0-32k vs V0J2-32k

| źródło | V0-32k [95% CI] | V0J2-32k [95% CI] | przedziały rozłączne? |
|---|---:|---:|:---:|
| 1_bzp | 1,4304 [1,4224–1,4391] | 1,4335 [1,4258–1,4427] | nie |
| 2_du_eli | 1,4635 [1,3640–1,5807] | 1,4677 [1,3680–1,5867] | nie |
| 3_kio | 1,3983 [1,3739–1,4250] | 1,3972 [1,3731–1,4221] | nie |
| 4_samorzad | 1,5502 [1,5381–1,5609] | 1,5560 [1,5438–1,5664] | nie |
| 5_granty | 1,7455 [1,6744–1,8124] | 1,8110 [1,7117–1,9075] | nie |
| 6_json_narzedzia | 3,7376 [3,6239–3,8240] | 2,8699 [2,8140–2,9151] | tak |
| 7_ogolny | 1,4117 [1,3942–1,4297] | 1,4186 [1,4008–1,4363] | nie |
| json_bzp_tabele | 2,7357 [2,5610–2,9050] | 2,6996 [2,5286–2,8633] | nie |
| granty_149 | 1,4084 [1,3798–1,4381] | 1,4112 [1,3828–1,4401] | nie |
| json_generic_heldout_test | 9,1819 [7,9131–10,6830] | 6,1485 [5,4772–6,9772] | tak |

### Uczciwe wyjątki

- Na `json_generic_heldout_test` Aster-0.5B 8,7072 [7,4510–10,1776] jest tańszy niż V0-32k 9,1819 [7,9131–10,6830]; CI się nakładają (przedziały rozłączne? nie).
- Na `2_du_eli` V0-32k 1,4635 [1,3640–1,5807] jest tańszy niż Aster-0.5B 1,6245 [1,5387–1,7374], ale przewaga jest w granicach CI (przedziały rozłączne? nie).
- Na `5_granty` V0-32k 1,7455 [1,6744–1,8124] jest tańszy niż Aster-0.5B 1,8632 [1,8096–1,9298], ale przewaga jest w granicach CI (przedziały rozłączne? nie).
- Na polskich tekstach (6 v2 + granty 149, bez JSON-ów) V0–Aster ma 5 rozłącznych przedziałów na 7, a V0–V0J2 0 na 7 — czyli V0 z V0J2 to remis w granicach CI.

## Test formatów (średnia liczba tokenów na zapis)

| format | PLLuM-4B | PLLuM-8B | PLLuM-12B | Bielik-11B-v3.1 | Bielik-4.5B-v3 | Aster-0.5B | EuroLLM-1.7B | Mistral-Nemo | Gemma-3-4B | DanielK-t1-pl-polish-32k | DanielK-t2-pl-cnc-32k | V0-32k | V0J2-32k | Slayer-v6 | Bielik-1.5B-v3 | APT3-1B | GPT-4o-o200k |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| RRRR.MM.DD | 10,00 | 6,00 | 10,00 | 11,00 | 11,00 | 5,38 | 11,00 | 10,00 | 10,00 | 4,30 | 4,30 | 4,00 | 4,00 | 5,47 | 11,00 | 3,88 | 6,00 |
| RRRR-MM-DD | 10,00 | 6,00 | 10,00 | 11,00 | 11,00 | 5,38 | 11,00 | 10,00 | 10,00 | 5,97 | 5,97 | 3,50 | 3,23 | 5,47 | 11,00 | 3,33 | 6,00 |
| DD.MM.RRRR | 10,00 | 6,00 | 10,00 | 11,00 | 11,00 | 5,38 | 11,00 | 10,00 | 10,00 | 4,08 | 4,08 | 3,60 | 3,38 | 5,47 | 11,00 | 4,00 | 6,00 |
| D.MM.RRRR | 9,68 | 6,00 | 9,68 | 10,68 | 10,68 | 5,38 | 10,68 | 9,68 | 9,68 | 3,98 | 3,98 | 3,60 | 3,38 | 5,47 | 10,68 | 4,00 | 6,00 |
| DD.MM.RRRR r. | 12,00 | 8,00 | 12,00 | 13,00 | 13,00 | 7,38 | 13,00 | 12,00 | 12,00 | 6,08 | 6,08 | 4,12 | 4,05 | 7,47 | 13,00 | 6,00 | 8,00 |
| D.MM.RRRRr. | 11,68 | 8,00 | 11,68 | 12,68 | 12,68 | 7,38 | 12,68 | 11,68 | 11,68 | 5,97 | 5,97 | 4,60 | 4,38 | 7,47 | 12,68 | 6,00 | 8,00 |
| DD/MM/RRRR | 10,00 | 6,00 | 10,00 | 11,00 | 11,00 | 5,38 | 11,00 | 10,00 | 10,00 | 5,97 | 5,97 | 5,47 | 5,33 | 5,47 | 11,00 | 4,92 | 6,00 |
| D miesiąca RRRR r. | 9,68 | 8,72 | 9,68 | 12,10 | 10,68 | 5,12 | 10,68 | 9,68 | 9,68 | 5,47 | 5,67 | 3,52 | 3,52 | 5,28 | 10,68 | 5,28 | 8,20 |
| D miesiąca RRRRr. | 9,68 | 8,72 | 9,68 | 12,10 | 10,68 | 5,12 | 10,68 | 9,68 | 9,68 | 5,47 | 5,67 | 4,40 | 4,40 | 5,28 | 10,68 | 5,28 | 8,20 |
| z dnia D miesiąca RRRR r. | 12,68 | 12,72 | 12,68 | 15,10 | 12,68 | 7,12 | 12,68 | 12,68 | 12,68 | 7,47 | 7,47 | 5,53 | 5,53 | 7,28 | 12,68 | 7,28 | 11,20 |
| D RZYM RRRR | 7,67 | 5,00 | 7,67 | 8,68 | 8,68 | 3,12 | 8,68 | 7,67 | 7,67 | 3,48 | 3,48 | 3,45 | 3,45 | 3,27 | 8,68 | 3,27 | 5,00 |
| D.RZYM.RRRR | 8,68 | 5,78 | 8,45 | 10,07 | 10,18 | 5,38 | 9,68 | 8,45 | 8,68 | 6,33 | 6,33 | 4,38 | 4,08 | 5,88 | 10,18 | 5,33 | 5,78 |
| 1 234,56 zł | 10,22 | 6,15 | 10,22 | 12,22 | 11,22 | 6,38 | 11,22 | 10,22 | 10,22 | 6,10 | 6,12 | 6,00 | 5,97 | 6,45 | 11,22 | 5,53 | 6,15 |
| 1234,56 zł | 9,15 | 5,08 | 9,15 | 11,15 | 10,15 | 6,00 | 10,15 | 9,15 | 9,15 | 5,60 | 5,62 | 5,75 | 5,67 | 6,08 | 10,15 | 5,47 | 5,08 |
| 1.234,56 zł | 10,22 | 6,15 | 10,22 | 12,22 | 11,22 | 7,47 | 11,22 | 10,22 | 10,22 | 6,55 | 6,58 | 6,38 | 6,30 | 7,53 | 11,22 | 6,15 | 6,15 |
| 1234.56 PLN | 9,15 | 6,08 | 10,15 | 11,15 | 10,15 | 6,00 | 10,15 | 10,15 | 9,15 | 6,50 | 6,50 | 5,53 | 5,47 | 6,08 | 10,15 | 5,85 | 5,08 |
| 1 234,56 PLN | 10,22 | 7,15 | 11,22 | 12,22 | 11,22 | 6,38 | 11,22 | 11,22 | 10,22 | 7,10 | 7,12 | 6,00 | 5,97 | 6,45 | 11,22 | 5,53 | 6,15 |
| 1 234 zł | 7,22 | 4,15 | 7,22 | 9,22 | 8,22 | 4,38 | 8,22 | 7,22 | 7,22 | 4,30 | 4,30 | 4,42 | 4,45 | 4,45 | 8,22 | 4,38 | 4,15 |
| kwota brutto: 1 234,56 zł | 16,23 | 12,15 | 16,23 | 17,23 | 14,22 | 10,38 | 16,23 | 16,23 | 16,23 | 11,18 | 11,20 | 10,03 | 9,00 | 10,45 | 14,22 | 8,53 | 12,15 |
| 1,2 mln zł | 5,00 | 6,00 | 5,00 | 8,00 | 6,00 | 5,00 | 6,00 | 5,00 | 5,00 | 3,23 | 4,20 | 3,00 | 3,00 | 5,00 | 6,00 | 3,27 | 5,00 |
| 123 tys. zł | 5,45 | 4,38 | 5,45 | 8,45 | 6,45 | 4,45 | 6,45 | 5,45 | 5,45 | 3,40 | 3,40 | 3,50 | 3,50 | 4,47 | 6,45 | 4,50 | 4,38 |
| § | 1 | 1 | 1 | 1 | 3 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 3 | 2 | 1 |
| § 5 | 3 | 3 | 3 | 3 | 5 | 2 | 3 | 3 | 3 | 2 | 2 | 2 | 2 | 2 | 5 | 3 | 3 |
| § 12 ust. 3 | 8 | 7 | 8 | 9 | 10 | 5 | 8 | 8 | 8 | 4 | 4 | 4 | 4 | 5 | 10 | 6 | 7 |
| § 12 ust. 3 pkt 4 lit. a | 14 | 13 | 14 | 15 | 16 | 10 | 14 | 14 | 14 | 9 | 9 | 8 | 8 | 10 | 16 | 12 | 13 |
| §5 | 2 | 2 | 2 | 2 | 4 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 4 | 3 | 2 |
| §§ 3–5 | 6 | 6 | 6 | 6 | 11 | 5 | 6 | 6 | 6 | 5 | 5 | 5 | 5 | 5 | 11 | 6 | 6 |
| w § 2 | 4 | 4 | 4 | 4 | 6 | 3 | 4 | 4 | 4 | 3 | 3 | 3 | 3 | 3 | 6 | 4 | 4 |
| zgodnie z § 14 ust. 1 | 12 | 11 | 12 | 13 | 12 | 7 | 10 | 12 | 12 | 6 | 6 | 7 | 7 | 8 | 12 | 8 | 11 |
| art. 5 § 2 | 7 | 7 | 7 | 7 | 9 | 5 | 7 | 7 | 7 | 4 | 4 | 4 | 4 | 5 | 9 | 6 | 7 |

Jak tną cyfry (`1234567890`):

- **PLLuM-4B** — pojedynczo: 1 2 3 4 5 6 7 8 9 0.
- **PLLuM-8B** — grupy 1–3 (zwykle po 3): 123 456 789 0.
- **PLLuM-12B** — pojedynczo: 1 2 3 4 5 6 7 8 9 0.
- **Bielik-11B-v3.1** — pojedynczo: ▁ 1 2 3 4 5 6 7 8 9 0.
- **Bielik-4.5B-v3** — pojedynczo: ▁ 1 2 3 4 5 6 7 8 9 0.
- **Aster-0.5B** — grupy 1–3 (zwykle po 3): 123 45 6 78 90.
- **EuroLLM-1.7B** — pojedynczo: ▁ 1 2 3 4 5 6 7 8 9 0.
- **Mistral-Nemo** — pojedynczo: 1 2 3 4 5 6 7 8 9 0.
- **Gemma-3-4B** — pojedynczo: 1 2 3 4 5 6 7 8 9 0.
- **DanielK-t1-pl-polish-32k** — grupy 1–3 (zwykle po 3): 123 45 6 78 90.
- **DanielK-t2-pl-cnc-32k** — grupy 1–3 (zwykle po 3): 123 45 6 78 90.
- **V0-32k** — grupy 1–3 (zwykle po 3): 123 45 67 8 90.
- **V0J2-32k** — grupy 1–3 (zwykle po 3): 123 45 67 8 90.
- **Slayer-v6** — grupy 1–3 (zwykle po 3): 123 45 67 8 90.
- **Bielik-1.5B-v3** — pojedynczo: ▁ 1 2 3 4 5 6 7 8 9 0.
- **APT3-1B** — grupy 1–3 (zwykle po 3): ▁123 45 67 8 90.
- **GPT-4o-o200k** — grupy 1–3 (zwykle po 3): 123 456 789 0.

Segmentacja 3 przykładów (liczba tokenów):

| tokenizer | 2 stycznia 2026 r. | 1 234 567,89 zł | § 12 ust. 3 pkt 4 lit. a |
|---|---:|---:|---:|
| PLLuM-4B | 9 | 13 | 14 |
| PLLuM-8B | 10 | 8 | 13 |
| PLLuM-12B | 9 | 13 | 14 |
| Bielik-11B-v3.1 | 12 | 15 | 15 |
| Bielik-4.5B-v3 | 10 | 14 | 16 |
| Aster-0.5B | 5 | 8 | 10 |
| EuroLLM-1.7B | 10 | 14 | 14 |
| Mistral-Nemo | 9 | 13 | 14 |
| Gemma-3-4B | 9 | 13 | 14 |
| DanielK-t1-pl-polish-32k | 6 | 8 | 9 |
| DanielK-t2-pl-cnc-32k | 6 | 8 | 9 |
| V0-32k | 4 | 7 | 8 |
| V0J2-32k | 4 | 8 | 8 |
| Slayer-v6 | 6 | 8 | 10 |
| Bielik-1.5B-v3 | 10 | 14 | 16 |
| APT3-1B | 6 | 7 | 12 |
| GPT-4o-o200k | 9 | 8 | 13 |

## Koszt słownika w modelu 150M

| tokenizer | słownik | 768: parametry | 768: % z 150M | 1024: parametry | 1024: % z 150M |
|---|---:|---:|---:|---:|---:|
| PLLuM-4B | 262 147 | 201,33 M | 134,2% | 268,44 M | 179,0% |
| PLLuM-8B | 128 259 | 98,50 M | 65,7% | 131,34 M | 87,6% |
| PLLuM-12B | 131 072 | 100,66 M | 67,1% | 134,22 M | 89,5% |
| Bielik-11B-v3.1 | 32 128 | 24,67 M | 16,4% | 32,90 M | 21,9% |
| Bielik-4.5B-v3 | 32 000 | 24,58 M | 16,4% | 32,77 M | 21,8% |
| Aster-0.5B | 32 000 | 24,58 M | 16,4% | 32,77 M | 21,8% |
| EuroLLM-1.7B | 128 000 | 98,30 M | 65,5% | 131,07 M | 87,4% |
| Mistral-Nemo | 131 072 | 100,66 M | 67,1% | 134,22 M | 89,5% |
| Gemma-3-4B | 262 145 | 201,33 M | 134,2% | 268,44 M | 179,0% |
| DanielK-t1-pl-polish-32k | 32 768 | 25,17 M | 16,8% | 33,55 M | 22,4% |
| DanielK-t2-pl-cnc-32k | 32 768 | 25,17 M | 16,8% | 33,55 M | 22,4% |
| V0-32k | 32 000 | 24,58 M | 16,4% | 32,77 M | 21,8% |
| V0J2-32k | 32 000 | 24,58 M | 16,4% | 32,77 M | 21,8% |
| Slayer-v6 | 32 768 | 25,17 M | 16,8% | 33,55 M | 22,4% |
| Bielik-1.5B-v3 | 32 000 | 24,58 M | 16,4% | 32,77 M | 21,8% |
| APT3-1B | 31 980 | 24,56 M | 16,4% | 32,75 M | 21,8% |
| GPT-4o-o200k | 200 019 | 153,61 M | 102,4% | 204,82 M | 136,5% |

Przy braku współdzielenia embedingu wejściowego z wyjściem liczby parametrów i procenty należy podwoić (pole `pct_150m_untied` w JSON).

## Dodatkowe miary

| tokenizer | „§” tokeny | martwe % | round-trip błędy | JSON tc1 | JSON held-out |
|---|---:|---:|---:|---:|---:|
| PLLuM-4B | 1 | 93,4% | 0 | 4,0964 | 7,7890 |
| PLLuM-8B | 1 | 88,8% | 0 | 4,0016 | 6,6921 |
| PLLuM-12B | 1 | 89,2% | 0 | 4,2437 | 7,1948 |
| Bielik-11B-v3.1 | 1 | 74,3% | 0 | 4,6790 | 7,8956 |
| Bielik-4.5B-v3 | 3 | 15,0% | 0 | 4,3242 | 8,7772 |
| Aster-0.5B | 1 | 14,6% | 4 | 4,0152 | 8,7072 |
| EuroLLM-1.7B | 1 | 85,5% | 0 | 4,3770 | 8,5113 |
| Mistral-Nemo | 1 | 89,2% | 0 | 4,2437 | 7,1948 |
| Gemma-3-4B | 1 | 93,4% | 0 | 4,0964 | 7,7890 |
| DanielK-t1-pl-polish-32k | 1 | 24,9% | 0 | 4,4286 | 9,5565 |
| DanielK-t2-pl-cnc-32k | 1 | 24,9% | 0 | 4,4274 | 9,5565 |
| V0-32k | 1 | 8,1% | 0 | 3,7376 | 9,1819 |
| V0J2-32k | 1 | 9,6% | 0 | 2,8699 | 6,1485 |
| Slayer-v6 | 1 | 35,0% | 0 | 3,9848 | 7,7051 |
| Bielik-1.5B-v3 | 3 | 15,0% | 0 | 4,3242 | 8,7772 |
| APT3-1B | 2 | 13,9% | 654 | 3,8109 | 9,0000 |
| GPT-4o-o200k | 1 | n/d | 0 | 3,7541 | 6,4586 |

## Test regresji podziału (4 frazy, wszystkie tokenizery)

| tokenizer | 15 maja | 100 mln zł | 3 miesiące | 5 min |
|---|---|---|---|---|
| PLLuM-4B | 1 / 5 / ▁maja (3) | 1 / 0 / 0 / ▁mln / ▁zł (5) | 3 / ▁miesią / ce (3) | 5 / ▁min (2) |
| PLLuM-8B | 15 / Ġm / aja (3) | 100 / Ġm / ln / ĠzÅĤ (4) | 3 / Ġmies / iÄħ / ce (4) | 5 / Ġmin (2) |
| PLLuM-12B | 1 / 5 / Ġmaja (3) | 1 / 0 / 0 / Ġmln / ĠzÅĤ (5) | 3 / Ġmies / iÄħ / ce (4) | 5 / Ġmin (2) |
| Bielik-11B-v3.1 | ▁ / 1 / 5 / ▁maj / a (5) | ▁ / 1 / 0 / 0 / ▁m / ln / ▁z / ł (8) | ▁ / 3 / ▁m / ies / ią / ce (6) | ▁ / 5 / ▁min (3) |
| Bielik-4.5B-v3 | ▁ / 1 / 5 / ▁maja (4) | ▁ / 1 / 0 / 0 / ▁mln / ▁zł (6) | ▁ / 3 / ▁miesiące (3) | ▁ / 5 / ▁min (3) |
| Aster-0.5B | 15 / Ġmaja (2) | 100 / Ġmln / ĠzÅĤ (3) | 3 / ĠmiesiÄħce (2) | 5 / Ġmin (2) |
| EuroLLM-1.7B | ▁ / 1 / 5 / ▁maja (4) | ▁ / 1 / 0 / 0 / ▁mln / ▁zł (6) | ▁ / 3 / ▁miesiące (3) | ▁ / 5 / ▁min (3) |
| Mistral-Nemo | 1 / 5 / Ġmaja (3) | 1 / 0 / 0 / Ġmln / ĠzÅĤ (5) | 3 / Ġmies / iÄħ / ce (4) | 5 / Ġmin (2) |
| Gemma-3-4B | 1 / 5 / ▁maja (3) | 1 / 0 / 0 / ▁mln / ▁zł (5) | 3 / ▁miesią / ce (3) | 5 / ▁min (2) |
| DanielK-t1-pl-polish-32k | 15 / Ġmaja (2) | 100 / Ġmln / ĠzÅĤ (3) | 3 / ĠmiesiÄħce (2) | 5 / Ġmin (2) |
| DanielK-t2-pl-cnc-32k | 15 / Ġm / aja (3) | 100 / Ġm / ln / ĠzÅĤ (4) | 3 / Ġm / iesiÄħ / ce (4) | 5 / Ġm / in (3) |
| V0-32k | 15 / Ġmaja (2) | 100 / ĠmlnĠzÅĤ (2) | 3 / ĠmiesiÄħce (2) | 5 / Ġmin (2) |
| V0J2-32k | 15 / Ġmaja (2) | 100 / ĠmlnĠzÅĤ (2) | 3 / ĠmiesiÄħce (2) | 5 / Ġmin (2) |
| Slayer-v6 | 15 / Ġmaja (2) | 100 / Ġmln / ĠzÅĤ (3) | 3 / ĠmiesiÄħce (2) | 5 / Ġmin (2) |
| Bielik-1.5B-v3 | ▁ / 1 / 5 / ▁maja (4) | ▁ / 1 / 0 / 0 / ▁mln / ▁zł (6) | ▁ / 3 / ▁miesiące (3) | ▁ / 5 / ▁min (3) |
| APT3-1B | ▁15 / ▁maja (2) | ▁100 / ▁mln / ▁zł (3) | ▁3 / ▁miesiące (2) | ▁5 / ▁min (2) |
| GPT-4o-o200k | 15 /  maja (2) | 100 /  mln /  zł (3) | 3 /  miesią / ce (3) | 5 /  min (2) |

W nawiasie liczba tokenów; `same_as_v0` w `results/tkx_zoo_regression_split.json` mówi, czy podział jest identyczny jak V0-32k.

## Propozycja zdań do posta

1. Sprawdziliśmy 17 tokenizery — także PLLuM 4B/8B/12B, Bielika 11B v3.1 i 4.5B v3, Aster-0.5B i dwa DanielK 32k z PR #29 — na tych samych ośmiu polskich źródłach urzędowych.
2. V0-32k vs V0J2-32k na polskim to remis w granicach CI: 0 rozłącznych przedziałów na 7 tabel (6 tekstowych v2 + granty 149). V0J2 jest wyraźnie lepszy tylko na JSON narzędzi: tc1 2,8699 vs 3,7376 i held-out 6,1485 vs 9,1819, przedziały rozłączne.
3. Najbliższy rywal przy tym samym słowniku 32k: Aster-0.5B — 1,7313 na BZP vs V0 1,4304 przy 32 000 słów; DanielK t1/t2 mają 1,7680/1,7687, a PLLuM 4B 2,3988 przy 262 147.
4. Cyfry uczą nas, że grupowanie po 3 (PLLuM 8B, V0) jest tańsze niż cięcie pojedynczo (PLLuM 4B/12B): 7,25 vs 10,14 tokenów na datę.
5. Koszt słownika w modelu 150M to od 16,4% (32k) do 134,2% (PLLuM 4B) samych embeddingów — bez współdzielenia z wyjściem dwukrotnie.

## Czego nie udało się pobrać

- **Llama-3.1-8B** — baza niedostępna (gated, czeka na zatwierdzenie Meta) (repo `meta-llama/Llama-3.1-8B`, rewizja `d04e592bb4f6aa9cfee91e2e20afa771667e1d4b`). Nie podstawiono innego repo.

Bielik-4.5B-v3 i Gemma 3 po akceptacji regulaminu pobrały się poprawnie; porównanie hashu PLLuM 8B z bazą pozostaje do uzupełnienia (po zatwierdzeniu Meta).

