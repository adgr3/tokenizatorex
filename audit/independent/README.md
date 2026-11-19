# Niezależne rundy 2 (Codex) i 3 (Grok)

Te pliki są **kopiami 1:1** raportów i artefaktów z gałęzi niezależnych
recenzentów. Nie są samooceną wykonawcy; liczby z tych plików mają
pierwszeństwo przed `audit/REVIEW_R2.md` i `audit/RED_TEAM_R3.md`.

## Codex — runda 2

* Gałąź: `review/tkx-a-r2-codex`
* Commit: `47e9cb2522ee16b88591c43cdc7e826681ba4735`
* Pliki: `REVIEW_CODEX_R2.md`, `results_codex.json`, `compute_codex.py`
* Werdykt: **PASS_Z_UWAGAMI**, 12/12 liczb powtórzonych.
* Uwagi: brak pomiaru cyfr (dodany jako `audit/digits_cost.py`), Rényi tylko
  `exp(H)/|V|` (dodano `H/ln|V|`), ranking HF #1/TKX #2 wynika ze scalania
  (potwierdzone: ciągi 100%), bootstrap RNG (ujednolicony), parytet HF przez ID
  (dodano porównanie ciągów).

## Grok — runda 3

* Gałąź: `review/tkx-a-r3-grok`
* Commit: `686cbceeb69eecb9faa8c62af97f2f1c9b3507`
* Pliki: `RED_TEAM_GROK_R3.md`, `measure_r3.py`, `collect_extra.py`,
  `slask_pdf_sample.py`, `uchwala_context.py`, `r3_*.json`
* Werdykt: **zmienia 2, osłabia 2, nie zmienia 3**.
* Zmienia: Rényi (APT3 wygrywa obie formy) i kryterium sukcesu modelu 150M.
* Osłabia: pełne PDF uchwał (0,55% vs APT3) i „tokeny albo bajty” jako osobną
  oś odporności (to tożsamość).
* Nie zmienia: 4 nowe źródła (przewaga nad Pollockiem −6,11%), round-trip HF
  (1010/1010), kontekst 2048 (1,7%), H1.

Kopie cytowane w raportach (żeby każda liczba miała plik w `audit/results/`):
`results/full_pdf_uchwaly.json`, `results/new_sources_four.json`,
`results/context_full.json`, `results/context_truncated.json`,
`results/doc_lengths_extra.json`, `results/roundtrip_independent.json`,
`results/codex_results.json`.

Surowe teksty z `raw_extra/` **nie** są kopiowane do repo (zostają lokalnie u
recenzenta); w repo są URL-e, SHA-256 i liczby, zgodnie z zasadą „do repo nie
trafiają treści korpusów”.
