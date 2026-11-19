# Audyt TKX-A

Katalog zawiera **tylko pomiary**; nie zmienia `superbpe.py`, `tokenizers/`,
`hf/` ani `export_hf.py`. Poprawki to TKX-C.

## Odtworzenie

```bash
pip install -r audit/requirements-audit.txt
# 1) protokół i korpus (teksty zostają lokalnie, do repo idzie MANIFEST)
python audit/prepare_corpus.py          # może potrwać; używa cache w audit/data/cache
python audit/prepare_corpus.py --manifest --bench
python audit/make_tokenizers_manifest.py
# 2) pomiary
python audit/fertility.py
python audit/notations.py
python audit/consistency.py
python audit/robustness.py
python audit/morphology.py              # wymaga audit/tmp/morphscore + polish_data.csv
python audit/superwords.py
python audit/vocab_usage.py
python audit/hf_parity.py
python audit/speed.py
python audit/stability.py               # opcjonalny retrening; może dać UNKNOWN
python audit/official_aggregate.py
# 3) wykresy i testy
python audit/make_charts.py
python -m pytest -q
```

`audit/data/raw/`, `audit/data/cache/`, `audit/data/bench/`,
`audit/data/tokenizer_files/` i `audit/tmp/` są w `.gitignore` (teksty korpusu
nie trafiają do repo). W repo są: `PROTOKOL.md`, `data/MANIFEST.json`
(URL, data, dziedzina, podział, słowa, SHA-256), `results/*.json`, raporty,
wykresy, skrypty recenzji (`review/`) i red teamu (`redteam/`).

## Pliki

| plik | co |
|---|---|
| `PROTOKOL.md` | zamrożone definicje, progi, hipotezy, zmiany po fakcie |
| `prepare_corpus.py` | pobieranie i zamrażanie korpusu (7 nowych + 8 istniejących dziedzin) |
| `fertility.py` | tokeny/słowo, bajty/token, znaki/token, CI, pary |
| `notations.py` | zapisy urzędowe, H1 (lata), H2 (długość kodów) |
| `consistency.py` | ten sam zapis w 7 kontekstach, H3/H4 |
| `robustness.py` | NFD, CAPS, literówki, OCR, PL–EN, emoji, H5 |
| `morphology.py` | MorphScore (publiczny kod) + spójność rdzenia |
| `superwords.py` | superwordy, boilerplate, rozbite słowa, 100 dziwnych tokenów |
| `vocab_usage.py` | martwe/rzadkie tokeny, Zipf, Rényi |
| `hf_parity.py` | parytet eksportu HF, H8 |
| `speed.py` | tokeny/s i MB/s (Python vs HF) |
| `stability.py` | tymczasowy retrening na innym shardzie HPLT |
| `official_aggregate.py` | agregat 7 dziedzin urzędowych i całego korpusu z CI |
| `make_charts.py` | wykresy PNG do raportu |
| `RAPORT_R1.md` | wyniki rundy 1 |
| `REVIEW_R2.md` | niezależna recenzja (werdykt PASS po poprawce H6) |
| `RED_TEAM_R3.md` | adwokat diabła: odporność wniosków, najgorsze przypadki, 2048 |
| `RAPORT_SLABOSCI.md` | raport końcowy (profesjonalny) |
| `RAPORT_PROSTY.md` | raport końcowy (prosty język) |
| `tests/test_audit.py` | testy audytu (H9, załącznik A, manifest, parytet) |
