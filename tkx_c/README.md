# TKX-C — poprawki TOKENIZATOREX

Warianty: `tokenizers/variants/<nazwa>/superbpe.json`, kanoniczny HF:
`hf/variants/<nazwa>/tokenizer.json`. Raporty: `RAPORT_TKX_C.md`,
`RAPORT_PROSTY.md`; plan TKX-D: `TKX_D_PLAN.md`; protokół: `PROTOKOL_TKX_C.md`.

## Odtworzenie

```bash
pip install -r requirements.txt
# dane: HPLT p2 400 MB (fallback; patrz protokół §9)
# trening wariantów (przykłady)
python train.py baseline --data audit/tmp/stability_train.txt --vocab 32000   --stage1-mb 300 --digits single --normalize nfc --out tkx_c/tmp/V2-base-32k.json
python train.py superbpe --data audit/tmp/stability_train.txt   --from tkx_c/tmp/V2-base-32k.json --transition 20000 --vocab 32000   --stage2-mb 100 --out tkx_c/tmp/V2-32k.json
# finalizacja + HF
python tkx_c/finalize_variants.py
# golden
python tkx_c/make_golden_dataset.py
python tkx_c/generate_golden.py
# pomiary i wykresy
python tkx_c/measure.py --only core
python tkx_c/measure_consistency.py
python tkx_c/measure_nfd.py
python tkx_c/measure_roundtrip.py
python tkx_c/full_docs.py
python tkx_c/measure_context.py
python tkx_c/make_charts.py
python -m pytest -q
```

`tkx_c/tmp/` i `tkx_c/data/` są w `.gitignore`; w repo są warianty, HF,
golden, wyniki JSON, wykresy i raporty.
