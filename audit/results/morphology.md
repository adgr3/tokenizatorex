# Morfologia (UD_Polish-PDB)

Kod MorphScore: `821fabf4692b`; pozycji po filtrze: 10916.

## MorphScore (paper default: freq_scale=True, bez słów 1-tokenowych)

| tokenizer | precision | recall | micro F1 | mean token/char |
|---|---:|---:|---:|---:|
| TOKENIZATOREX | 0.023 | 0.063 | 0.031 | 0.344 |
| TOKENIZATOREX-HF | 0.023 | 0.063 | 0.031 | 0.344 |
| TOKENIZATOREX-base | 0.023 | 0.060 | 0.030 | 0.334 |
| Slayer1B | 0.082 | 0.225 | 0.094 | 0.362 |
| APT3-1B | 0.030 | 0.070 | 0.049 | 0.282 |
| Pollock-2.0 | 0.026 | 0.065 | 0.033 | 0.320 |
| Bielik-v3 | 0.135 | 0.395 | 0.147 | 0.431 |
| PLLuM-12B | 0.105 | 0.298 | 0.129 | 0.390 |
| GPT-4o | 0.098 | 0.268 | 0.123 | 0.385 |

## Spójność rdzenia (pierwszy token wspólny z formą podstawową)

| tokenizer | rzeczowniki | czasowniki | przymiotniki | razem |
|---|---:|---:|---:|---:|
| TOKENIZATOREX | 0.910 | 1.000 | 0.969 | 0.933 |
| TOKENIZATOREX-HF | 0.910 | 1.000 | 0.969 | 0.933 |
| TOKENIZATOREX-base | 0.896 | 1.000 | 0.952 | 0.918 |
| Slayer1B | 0.898 | 1.000 | 0.967 | 0.926 |
| APT3-1B | 0.322 | 1.000 | 0.493 | 0.391 |
| Pollock-2.0 | 0.809 | 1.000 | 0.928 | 0.857 |
| Bielik-v3 | 0.957 | 1.000 | 0.985 | 0.968 |
| PLLuM-12B | 0.917 | 1.000 | 0.982 | 0.943 |
| GPT-4o | 0.873 | 1.000 | 0.981 | 0.916 |

Zgodność z morfologią słabo przewiduje jakość modelu (R² ≈ 0,02); raportujemy, ale nie optymalizujemy na ślepo.
