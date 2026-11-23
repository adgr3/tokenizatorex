# Karta wymagań TOKENIZATOREX v2.0 — tokenizer pod polski model ≤ 150M (polszczyzna urzędowa)

Wersja: 23.11.2026 · Autor: Codex (z kontekstem PLAN_150M_v2.md, RESEARCH_TKX_V2.md)
Powiązane: project-hub #566 (model 150M), #576 (dziennik), TKX-A (fertility), TKX-C (cyfry/NFC/HF)

Zasada naczelna (z RESEARCH_TKX_V2 §1 i §8.1): **nie ma najlepszego tokenizera — jest najlepszy do zadania i do rozmiaru modelu**.
Niska liczba tokenów to warunek konieczny (Ali i in.), dla małych modeli ważniejszy niż dla dużych (Goldman i in.),
ale nie dowód jakości (Schmidt i in.). Dlatego TOKENIZATOREX v2.0 mierzy się testem domenowym i ostateczny wybór
robi TKX-D na małych modelach.

## 1. Kontekst zadania modelu

- Architektura: dekoder w stylu Llama (RMSNorm, RoPE, SwiGLU), **powiązane embeddingi**, kontekst 2048, format HF.
- Rozmiar: 130–150 mln parametrów łącznie z embeddingami; modele próbne ~30 mln i ~60 mln.
- Korpus: FineWeb-2 PL + Wikipedia PL + **10–30% tekstów urzędowych** (przetargi, samorządy, granty NGO, prawo).
- Zadania downstream: wyciąganie pól z ogłoszeń, klasyfikacja CPV, uchwały, granty, **tool calling w JSON**.
- Porównanie strat: bity na bajt (BPB) — uczciwe między różnymi tokenizerami.

## 2. Wymagania OBOWIĄZKOWE (bloker, jeśli nie spełnione)

| # | Wymaganie | Kryterium mierzalne | Próg | Jak mierzymy |
|---|-----------|---------------------|------|--------------|
| O1 | Odwracalność (round-trip) | `decode(encode(x)) == x` dla każdego dokumentu testowego i wzorca | 100% | `measure_roundtrip` + testy pytest |
| O2 | NFC (kanoniczna normalizacja) | brak NFD w słowniku i w wyjściu; `is_nfd(tok)==False` | 100% dokumentów | `measure_nfd` |
| O3 | Znak „§” | pojedynczy token w słowniku (id) i w kodowaniu wzorca „§ 362(a)” | 1 token | `wzorce.json` + vocab check |
| O4 | Stały podział lat 2015–2035 | rok jako jeden token w formatach `2026`, `2026 r.`, `r. 2026` | ≤ 2 tokeny/rok | `wzorce.json` kategoria „lata” |
| O5 | Kwoty w kilku formatach | `1 234 567,89 zł`, `1.234.567,89 PLN`, `1234567.89` | ≤ 6 tokenów/kwota, spójnie | `wzorce.json` kategoria „kwoty” |
| O6 | Daty w 5 formatach | `2026-01-02`, `02.01.2026`, `2 stycznia 2026`, `2 stycznia 2026 r.`, `02/01/2026` | ≤ 5 tokenów/data | `wzorce.json` kategoria „daty” |
| O7 | Kody CPV w jednym kształcie | `45000000-7`, `45233120-6` | ≤ 3 tokeny/kod | `wzorce.json` kategoria „CPV” |
| O8 | Brak „martwych” tokenów powyżej progu | tokeny o zerowej częstości na korpusie domenowym | ≤ 5% słownika | `vocab_usage` (Rényi) |
| O9 | Brak przecieku korpusu testowego | n-gramy domenowe vs HPLT 400 MB | ≤ 20% dokumentów z trafieniem 13-gramu | `przeciek` (poniżej) |

## 3. Wymagania WAŻNE (koszt skrótów i odwołań)

Każdy z poniższych wzorców ma być zmierzony (liczba tokenów + segmentacja tekstowa) w `wzorce.json` (≥ 150 przykładów, 12 kategorii). Progi: **nie gorzej niż Slayer v6** na tekstach urzędowych (fertility) i **spójność 100%** w 5 kontekstach (H3).

Skróty prawne: `art.`, `ust.`, `pkt`, `lit.`, `poz.`, `Dz. U.`, `Dz.U.`, `M.P.`, `t.j.`/`tj.`, `ze zm.`,
`Pzp`, `KPA`, `k.c.`

Sygnatury: `KIO 1234/26`, `II SA/Wa 123/26`

Identyfikatory: NIP (10 cyfr), REGON (9/14), KRS (10), kody pocztowe (`00-001`), numery ogłoszeń BZP (`2026/BZP 00514538`)

Daty słowne: „25 września 2026 r.”

Kwoty: „1 234 567,89 zł” i „1.234.567,89 PLN”

## 4. Bezpieczniki (nie optymalizujemy, pilnujemy)

- angielski: fertility **nie gorzej niż +X% od Slayera v6** (Slayer ma 1,30 na angielskim; nasz obecny 1,97 — to znany koszt; próg: brak regresji względem wariantu bazowego V0-32k).
- JSON wywołań narzędzi: koszt **≤ Slayer v6** (obecnie u nas 31 vs 29 tokenów — do naprawy w v2.1).
- adresy www/e-mail, nazwy firm i produktów: brak regresji > 5% względem V0-32k.

## 5. Rozmiar słownika vs 150M — OTWARTE PYTANIE do TKX-D

Przy powiązanych embeddingach (vocab × d_model parametrów w macierzy embeddingów; przy tied weights liczone raz):

| Słownik | d_model 384 (30M) | d_model 512 (60M) | d_model 768 (150M) |
|---|---:|---:|---:|
| 16k | 6,1 M (≈ 20% modelu 30M) | 8,2 M (≈ 14% modelu 60M) | 12,3 M (≈ 8% modelu 150M) |
| 24k | 9,2 M (≈ 31%) | 12,3 M (≈ 21%) | 18,4 M (≈ 12%) |
| 32k | 12,3 M (≈ 41%) | 16,4 M (≈ 27%) | 24,6 M (≈ 16%) |
| 48k | 18,4 M (≈ 61%) | 24,6 M (≈ 41%) | 36,9 M (≈ 25%) |

Uwagi:
- Szacunki PM z RESEARCH_TKX_V2 §2 (Tao i in.; Romanyukov i in.): dla małych modeli duży słownik dominuje embeddingi.
- Dla modelu 30M ze słownikiem 32k embeddingi to ~41% parametrów — wyniki modeli próbnych mogą słabo przenosić się na 150M.
- **Nie rozstrzygamy tutaj**: TKX-D mierzy rozmiar słownika 16k/24k/32k jako osobną oś (BPB + testy domenowe, ≥ 3 seedy), zgodnie z zasadą ablacji planu 150M.
- TKX-C odrzucił V3-16k/24k z powodu wymuszonych tokenów cyfr — to osobne pytanie, nie przesądza o 16k/24k dla innych wariantów.

## 6. Wymagania dla testu domenowego (metodologia)

- Tekst spoza treningu tokenizera (podział w czasie: trening do końca 2025, test 2026).
- Kontrola przecieku: 13-gramy znaków/słów vs HPLT 400 MB; próg ≤ 20% dokumentów z trafieniem.
- Fertility i bajty/token per źródło 1–7, z 95% CI (bootstrap po dokumentach, 1000×, seed 20261123).
- Ranking per źródło.
- Znaki specjalne: tabela wariant × znak (≥ 30 znaków).
- Diagnoza „§” w V3: hipoteza o wymuszonych tokenach 000–999/00–99 (bez trenowania nowych wariantów).
- Martwe tokeny per wariant na korpusie domenowym.
- Metryki z RESEARCH_TKX_V2 §8.2: **Rényi efficiency**, **metryki cyfr TokEval** (zgodność z wartością pozycyjną, F1 granic), kategorie testowe wzorowane na KL3M (cytowania, skróty, „§”).

## 7. Tokenizery do pomiaru

Wszystkie 14 wariantów `hf/variants/*` + Slayer v6 (`SlayerLab/Slayer1B-1.08`, SHA-256 0640d3bd…815dd) +
Bielik-1.5B-v3 (APT4), APT3 (`Azurro/APT3-1B-Base`), Qwen3.5 (`Qwen/Qwen3.5-4B`), GPT-4o (tiktoken o200k),
PLLuM-12B (`CYFRAGOVPL/PLLuM-12B-base-2412`).

Uwaga: Bielik-1.5B-v3 jest gated — używamy istniejącego logowania HF właściciela; brak dostępu = UNKNOWN.
APT4 z Bielika v3 (jeśli tokenizer publicznie dostępny) dodajemy jako najsilniejszy polski konkurent (RESEARCH §3).

## 8. Definicja „gotowe”

- `pytest -q` zielone.
- Wszystkie liczby w raportach z `results/tkx_v2_*.json` (skrypt `scripts/sprawdz_liczby_v2.py`).
- Draft PR z gałęzi `feat/tkx-v2-0` (po zgodzie na push).
- `STATUS=GOTOWE` albo `STATUS=BLOKER: <opis>`.
