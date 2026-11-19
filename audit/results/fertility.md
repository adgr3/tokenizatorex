# Fertility na `test` (tokeny/słowo; mniej = lepiej)

Wartości z 95% CI bootstrapu po dokumentach (1000 powtórzeń, seed 20261119).

| tokenizer | przetargi_ogloszenia | przetargi_kio | samorzad_uchwaly | granty_ogloszenia | prawo_eli | ocr_prasa | tabele_json | web | wikipedia | literatura | prawo | sejm | nauka | dyskusje | angielski |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| TOKENIZATOREX | 1.555 [1.528; 1.583] | 1.403 [1.383; 1.420] | 1.528 [1.517; 1.540] | 1.791 [1.712; 1.866] | 1.487 [1.421; 1.563] | 1.916 [1.717; 2.148] | 2.629 [2.504; 2.755] | 1.416 [1.399; 1.433] | 1.785 [1.736; 1.855] | 1.622 [1.590; 1.659] | 1.511 [1.482; 1.546] | 1.292 [1.283; 1.300] | 1.976 [1.904; 2.052] | 1.650 [1.615; 1.690] | 1.976 [1.956; 1.998] |
| TOKENIZATOREX-HF | 1.552 [1.525; 1.579] | 1.403 [1.384; 1.421] | 1.523 [1.512; 1.535] | 1.784 [1.708; 1.856] | 1.483 [1.418; 1.559] | 1.915 [1.717; 2.147] | 2.616 [2.492; 2.740] | 1.415 [1.399; 1.433] | 1.783 [1.734; 1.852] | 1.621 [1.590; 1.659] | 1.506 [1.477; 1.540] | 1.292 [1.283; 1.300] | 1.975 [1.903; 2.051] | 1.649 [1.615; 1.689] | 1.975 [1.955; 1.997] |
| TOKENIZATOREX-base | 1.871 [1.838; 1.906] | 1.649 [1.626; 1.671] | 1.949 [1.934; 1.964] | 1.996 [1.920; 2.073] | 1.798 [1.738; 1.867] | 2.076 [1.878; 2.305] | 2.997 [2.865; 3.133] | 1.582 [1.567; 1.598] | 1.941 [1.893; 2.006] | 1.752 [1.726; 1.783] | 1.830 [1.800; 1.861] | 1.515 [1.507; 1.524] | 2.115 [2.052; 2.178] | 1.864 [1.830; 1.903] | 1.981 [1.961; 2.001] |
| Slayer1B | 2.017 [1.981; 2.055] | 1.720 [1.693; 1.744] | 1.983 [1.970; 1.999] | 2.084 [2.014; 2.153] | 1.804 [1.735; 1.888] | 2.078 [1.924; 2.261] | 3.048 [2.910; 3.187] | 1.672 [1.657; 1.691] | 1.997 [1.956; 2.061] | 1.902 [1.874; 1.937] | 1.847 [1.817; 1.885] | 1.588 [1.579; 1.596] | 2.096 [2.038; 2.160] | 1.904 [1.871; 1.939] | 1.294 [1.280; 1.310] |
| APT3-1B | 1.796 [1.770; 1.823] | 1.584 [1.561; 1.604] | 1.772 [1.760; 1.786] | 2.051 [1.945; 2.152] | 1.587 [1.524; 1.660] | 1.976 [1.788; 2.197] | 2.805 [2.685; 2.928] | 1.557 [1.541; 1.573] | 1.831 [1.790; 1.883] | 1.689 [1.661; 1.721] | 1.572 [1.547; 1.603] | 1.418 [1.411; 1.425] | 1.917 [1.866; 1.970] | 1.759 [1.728; 1.794] | 1.815 [1.796; 1.838] |
| Pollock-2.0 | 1.812 [1.779; 1.845] | 1.497 [1.476; 1.515] | 1.753 [1.741; 1.766] | 1.781 [1.726; 1.834] | 1.555 [1.496; 1.629] | 1.942 [1.769; 2.144] | 2.711 [2.590; 2.832] | 1.577 [1.561; 1.594] | 1.763 [1.721; 1.819] | 1.778 [1.752; 1.814] | 1.592 [1.568; 1.621] | 1.392 [1.387; 1.398] | 1.973 [1.906; 2.043] | 1.719 [1.691; 1.750] | 1.762 [1.743; 1.781] |
| Bielik-v3 | 3.466 [3.428; 3.505] | 3.144 [3.118; 3.170] | 3.261 [3.246; 3.276] | 3.500 [3.401; 3.598] | 3.094 [3.040; 3.154] | 2.905 [2.838; 2.991] | 4.616 [4.474; 4.758] | 2.879 [2.857; 2.901] | 3.113 [3.064; 3.170] | 2.902 [2.874; 2.931] | 3.117 [3.078; 3.160] | 2.893 [2.878; 2.909] | 3.183 [3.121; 3.236] | 3.002 [2.970; 3.036] | 1.337 [1.319; 1.356] |
| PLLuM-12B | 2.720 [2.685; 2.759] | 2.433 [2.409; 2.457] | 2.627 [2.612; 2.642] | 2.828 [2.704; 2.955] | 2.475 [2.421; 2.535] | 2.430 [2.339; 2.552] | 3.786 [3.660; 3.913] | 2.251 [2.235; 2.270] | 2.424 [2.382; 2.483] | 2.319 [2.298; 2.342] | 2.454 [2.424; 2.492] | 2.252 [2.240; 2.264] | 2.537 [2.490; 2.584] | 2.422 [2.391; 2.455] | 1.227 [1.211; 1.243] |
| GPT-4o | 2.610 [2.580; 2.643] | 2.388 [2.363; 2.411] | 2.436 [2.423; 2.449] | 2.580 [2.526; 2.631] | 2.379 [2.333; 2.430] | 2.371 [2.302; 2.458] | 3.494 [3.385; 3.604] | 2.189 [2.172; 2.208] | 2.444 [2.407; 2.485] | 2.275 [2.252; 2.299] | 2.356 [2.320; 2.397] | 2.169 [2.155; 2.183] | 2.451 [2.408; 2.490] | 2.321 [2.295; 2.350] | 1.179 [1.166; 1.194] |

## Rankingi (test)

* **przetargi_ogloszenia**: 1. TOKENIZATOREX-HF 1.552, 2. TOKENIZATOREX 1.555, 3. APT3-1B 1.796, 4. Pollock-2.0 1.812, 5. TOKENIZATOREX-base 1.871, 6. Slayer1B 2.017, 7. GPT-4o 2.610, 8. PLLuM-12B 2.720, 9. Bielik-v3 3.466
* **przetargi_kio**: 1. TOKENIZATOREX 1.403, 2. TOKENIZATOREX-HF 1.403, 3. Pollock-2.0 1.497, 4. APT3-1B 1.584, 5. TOKENIZATOREX-base 1.649, 6. Slayer1B 1.720, 7. GPT-4o 2.388, 8. PLLuM-12B 2.433, 9. Bielik-v3 3.144
* **samorzad_uchwaly**: 1. TOKENIZATOREX-HF 1.523, 2. TOKENIZATOREX 1.528, 3. Pollock-2.0 1.753, 4. APT3-1B 1.772, 5. TOKENIZATOREX-base 1.949, 6. Slayer1B 1.983, 7. GPT-4o 2.436, 8. PLLuM-12B 2.627, 9. Bielik-v3 3.261
* **granty_ogloszenia**: 1. Pollock-2.0 1.781, 2. TOKENIZATOREX-HF 1.784, 3. TOKENIZATOREX 1.791, 4. TOKENIZATOREX-base 1.996, 5. APT3-1B 2.051, 6. Slayer1B 2.084, 7. GPT-4o 2.580, 8. PLLuM-12B 2.828, 9. Bielik-v3 3.500
* **prawo_eli**: 1. TOKENIZATOREX-HF 1.483, 2. TOKENIZATOREX 1.487, 3. Pollock-2.0 1.555, 4. APT3-1B 1.587, 5. TOKENIZATOREX-base 1.798, 6. Slayer1B 1.804, 7. GPT-4o 2.379, 8. PLLuM-12B 2.475, 9. Bielik-v3 3.094
* **ocr_prasa**: 1. TOKENIZATOREX-HF 1.915, 2. TOKENIZATOREX 1.916, 3. Pollock-2.0 1.942, 4. APT3-1B 1.976, 5. TOKENIZATOREX-base 2.076, 6. Slayer1B 2.078, 7. GPT-4o 2.371, 8. PLLuM-12B 2.430, 9. Bielik-v3 2.905
* **tabele_json**: 1. TOKENIZATOREX-HF 2.616, 2. TOKENIZATOREX 2.629, 3. Pollock-2.0 2.711, 4. APT3-1B 2.805, 5. TOKENIZATOREX-base 2.997, 6. Slayer1B 3.048, 7. GPT-4o 3.494, 8. PLLuM-12B 3.786, 9. Bielik-v3 4.616
* **web**: 1. TOKENIZATOREX-HF 1.415, 2. TOKENIZATOREX 1.416, 3. APT3-1B 1.557, 4. Pollock-2.0 1.577, 5. TOKENIZATOREX-base 1.582, 6. Slayer1B 1.672, 7. GPT-4o 2.189, 8. PLLuM-12B 2.251, 9. Bielik-v3 2.879
* **wikipedia**: 1. Pollock-2.0 1.763, 2. TOKENIZATOREX-HF 1.783, 3. TOKENIZATOREX 1.785, 4. APT3-1B 1.831, 5. TOKENIZATOREX-base 1.941, 6. Slayer1B 1.997, 7. PLLuM-12B 2.424, 8. GPT-4o 2.444, 9. Bielik-v3 3.113
* **literatura**: 1. TOKENIZATOREX-HF 1.621, 2. TOKENIZATOREX 1.622, 3. APT3-1B 1.689, 4. TOKENIZATOREX-base 1.752, 5. Pollock-2.0 1.778, 6. Slayer1B 1.902, 7. GPT-4o 2.275, 8. PLLuM-12B 2.319, 9. Bielik-v3 2.902
* **prawo**: 1. TOKENIZATOREX-HF 1.506, 2. TOKENIZATOREX 1.511, 3. APT3-1B 1.572, 4. Pollock-2.0 1.592, 5. TOKENIZATOREX-base 1.830, 6. Slayer1B 1.847, 7. GPT-4o 2.356, 8. PLLuM-12B 2.454, 9. Bielik-v3 3.117
* **sejm**: 1. TOKENIZATOREX-HF 1.292, 2. TOKENIZATOREX 1.292, 3. Pollock-2.0 1.392, 4. APT3-1B 1.418, 5. TOKENIZATOREX-base 1.515, 6. Slayer1B 1.588, 7. GPT-4o 2.169, 8. PLLuM-12B 2.252, 9. Bielik-v3 2.893
* **nauka**: 1. APT3-1B 1.917, 2. Pollock-2.0 1.973, 3. TOKENIZATOREX-HF 1.975, 4. TOKENIZATOREX 1.976, 5. Slayer1B 2.096, 6. TOKENIZATOREX-base 2.115, 7. GPT-4o 2.451, 8. PLLuM-12B 2.537, 9. Bielik-v3 3.183
* **dyskusje**: 1. TOKENIZATOREX-HF 1.649, 2. TOKENIZATOREX 1.650, 3. Pollock-2.0 1.719, 4. APT3-1B 1.759, 5. TOKENIZATOREX-base 1.864, 6. Slayer1B 1.904, 7. GPT-4o 2.321, 8. PLLuM-12B 2.422, 9. Bielik-v3 3.002
* **angielski**: 1. GPT-4o 1.179, 2. PLLuM-12B 1.227, 3. Slayer1B 1.294, 4. Bielik-v3 1.337, 5. Pollock-2.0 1.762, 6. APT3-1B 1.815, 7. TOKENIZATOREX-HF 1.975, 8. TOKENIZATOREX 1.976, 9. TOKENIZATOREX-base 1.981

## Różnice względem TOKENIZATOREX (test)

| dziedzina | tokenizer | różnica tok./słowo [95% CI] | stosunek | werdykt |
|---|---|---:|---:|---|
| przetargi_ogloszenia | TOKENIZATOREX-HF | -0.0028 [-0.0034; -0.0023] | 0.998 | nieistotna |
| przetargi_ogloszenia | TOKENIZATOREX-base | +0.3154 [+0.3069; +0.3239] | 1.203 | istotna |
| przetargi_ogloszenia | Slayer1B | +0.4619 [+0.4519; +0.4723] | 1.297 | istotna |
| przetargi_ogloszenia | APT3-1B | +0.2411 [+0.2354; +0.2464] | 1.155 | istotna |
| przetargi_ogloszenia | Pollock-2.0 | +0.2564 [+0.2495; +0.2636] | 1.165 | istotna |
| przetargi_ogloszenia | Bielik-v3 | +1.9103 [+1.8938; +1.9271] | 2.228 | istotna |
| przetargi_ogloszenia | PLLuM-12B | +1.1652 [+1.1521; +1.1791] | 1.749 | istotna |
| przetargi_ogloszenia | GPT-4o | +1.0549 [+1.0438; +1.0651] | 1.678 | istotna |
| przetargi_kio | TOKENIZATOREX-HF | +0.0006 [+0.0001; +0.0011] | 1.000 | nieistotna |
| przetargi_kio | TOKENIZATOREX-base | +0.2465 [+0.2366; +0.2569] | 1.176 | istotna |
| przetargi_kio | Slayer1B | +0.3172 [+0.3057; +0.3292] | 1.226 | istotna |
| przetargi_kio | APT3-1B | +0.1817 [+0.1730; +0.1911] | 1.130 | istotna |
| przetargi_kio | Pollock-2.0 | +0.0946 [+0.0851; +0.1038] | 1.067 | istotna |
| przetargi_kio | Bielik-v3 | +1.7418 [+1.7236; +1.7620] | 2.242 | istotna |
| przetargi_kio | PLLuM-12B | +1.0305 [+1.0176; +1.0453] | 1.735 | istotna |
| przetargi_kio | GPT-4o | +0.9855 [+0.9703; +1.0020] | 1.703 | istotna |
| samorzad_uchwaly | TOKENIZATOREX-HF | -0.0047 [-0.0054; -0.0041] | 0.997 | nieistotna |
| samorzad_uchwaly | TOKENIZATOREX-base | +0.4209 [+0.4106; +0.4311] | 1.275 | istotna |
| samorzad_uchwaly | Slayer1B | +0.4556 [+0.4498; +0.4616] | 1.298 | istotna |
| samorzad_uchwaly | APT3-1B | +0.2444 [+0.2374; +0.2510] | 1.160 | istotna |
| samorzad_uchwaly | Pollock-2.0 | +0.2250 [+0.2185; +0.2313] | 1.147 | istotna |
| samorzad_uchwaly | Bielik-v3 | +1.7327 [+1.7212; +1.7441] | 2.134 | istotna |
| samorzad_uchwaly | PLLuM-12B | +1.0990 [+1.0877; +1.1095] | 1.719 | istotna |
| samorzad_uchwaly | GPT-4o | +0.9078 [+0.8988; +0.9177] | 1.594 | istotna |
| granty_ogloszenia | TOKENIZATOREX-HF | -0.0072 [-0.0108; -0.0039] | 0.996 | nieistotna |
| granty_ogloszenia | TOKENIZATOREX-base | +0.2054 [+0.1789; +0.2344] | 1.115 | istotna |
| granty_ogloszenia | Slayer1B | +0.2927 [+0.2735; +0.3106] | 1.163 | istotna |
| granty_ogloszenia | APT3-1B | +0.2606 [+0.1884; +0.3415] | 1.146 | istotna |
| granty_ogloszenia | Pollock-2.0 | -0.0103 [-0.0401; +0.0228] | 0.994 | nieistotna |
| granty_ogloszenia | Bielik-v3 | +1.7095 [+1.6599; +1.7595] | 1.955 | istotna |
| granty_ogloszenia | PLLuM-12B | +1.0372 [+0.9671; +1.1084] | 1.579 | istotna |
| granty_ogloszenia | GPT-4o | +0.7887 [+0.7552; +0.8249] | 1.440 | istotna |
| prawo_eli | TOKENIZATOREX-HF | -0.0035 [-0.0045; -0.0027] | 0.998 | nieistotna |
| prawo_eli | TOKENIZATOREX-base | +0.3110 [+0.2903; +0.3326] | 1.209 | istotna |
| prawo_eli | Slayer1B | +0.3172 [+0.3035; +0.3329] | 1.213 | istotna |
| prawo_eli | APT3-1B | +0.1006 [+0.0843; +0.1233] | 1.068 | istotna |
| prawo_eli | Pollock-2.0 | +0.0687 [+0.0500; +0.0866] | 1.046 | istotna |
| prawo_eli | Bielik-v3 | +1.6077 [+1.5773; +1.6328] | 2.081 | istotna |
| prawo_eli | PLLuM-12B | +0.9879 [+0.9582; +1.0147] | 1.664 | istotna |
| prawo_eli | GPT-4o | +0.8919 [+0.8510; +0.9241] | 1.600 | istotna |
| ocr_prasa | TOKENIZATOREX-HF | -0.0007 [-0.0019; +0.0004] | 1.000 | nieistotna |
| ocr_prasa | TOKENIZATOREX-base | +0.1600 [+0.1461; +0.1755] | 1.084 | istotna |
| ocr_prasa | Slayer1B | +0.1625 [+0.1076; +0.2120] | 1.085 | istotna |
| ocr_prasa | APT3-1B | +0.0603 [+0.0402; +0.0770] | 1.032 | istotna |
| ocr_prasa | Pollock-2.0 | +0.0258 [-0.0104; +0.0569] | 1.013 | nieistotna |
| ocr_prasa | Bielik-v3 | +0.9890 [+0.8077; +1.1514] | 1.516 | istotna |
| ocr_prasa | PLLuM-12B | +0.5142 [+0.3674; +0.6423] | 1.268 | istotna |
| ocr_prasa | GPT-4o | +0.4548 [+0.2915; +0.6007] | 1.237 | istotna |
| tabele_json | TOKENIZATOREX-HF | -0.0137 [-0.0156; -0.0119] | 0.995 | nieistotna |
| tabele_json | TOKENIZATOREX-base | +0.3677 [+0.3493; +0.3862] | 1.140 | istotna |
| tabele_json | Slayer1B | +0.4184 [+0.4031; +0.4344] | 1.159 | istotna |
| tabele_json | APT3-1B | +0.1761 [+0.1663; +0.1846] | 1.067 | istotna |
| tabele_json | Pollock-2.0 | +0.0815 [+0.0711; +0.0911] | 1.031 | istotna |
| tabele_json | Bielik-v3 | +1.9868 [+1.9619; +2.0136] | 1.756 | istotna |
| tabele_json | PLLuM-12B | +1.1568 [+1.1386; +1.1741] | 1.440 | istotna |
| tabele_json | GPT-4o | +0.8650 [+0.8444; +0.8862] | 1.329 | istotna |
| web | TOKENIZATOREX-HF | -0.0002 [-0.0004; -0.0000] | 1.000 | nieistotna |
| web | TOKENIZATOREX-base | +0.1663 [+0.1591; +0.1732] | 1.117 | istotna |
| web | Slayer1B | +0.2568 [+0.2488; +0.2640] | 1.181 | istotna |
| web | APT3-1B | +0.1412 [+0.1355; +0.1472] | 1.100 | istotna |
| web | Pollock-2.0 | +0.1611 [+0.1531; +0.1696] | 1.114 | istotna |
| web | Bielik-v3 | +1.4634 [+1.4419; +1.4855] | 2.034 | istotna |
| web | PLLuM-12B | +0.8349 [+0.8192; +0.8511] | 1.590 | istotna |
| web | GPT-4o | +0.7730 [+0.7552; +0.7907] | 1.546 | istotna |
| wikipedia | TOKENIZATOREX-HF | -0.0026 [-0.0049; -0.0002] | 0.999 | nieistotna |
| wikipedia | TOKENIZATOREX-base | +0.1559 [+0.1467; +0.1645] | 1.087 | istotna |
| wikipedia | Slayer1B | +0.2119 [+0.1944; +0.2266] | 1.119 | istotna |
| wikipedia | APT3-1B | +0.0459 [+0.0249; +0.0629] | 1.026 | istotna |
| wikipedia | Pollock-2.0 | -0.0224 [-0.0420; -0.0047] | 0.987 | istotna |
| wikipedia | Bielik-v3 | +1.3275 [+1.2734; +1.3696] | 1.744 | istotna |
| wikipedia | PLLuM-12B | +0.6392 [+0.5981; +0.6723] | 1.358 | istotna |
| wikipedia | GPT-4o | +0.6585 [+0.6050; +0.6997] | 1.369 | istotna |
| literatura | TOKENIZATOREX-HF | -0.0003 [-0.0005; -0.0002] | 1.000 | nieistotna |
| literatura | TOKENIZATOREX-base | +0.1302 [+0.1233; +0.1370] | 1.080 | istotna |
| literatura | Slayer1B | +0.2799 [+0.2734; +0.2857] | 1.173 | istotna |
| literatura | APT3-1B | +0.0671 [+0.0603; +0.0729] | 1.041 | istotna |
| literatura | Pollock-2.0 | +0.1567 [+0.1461; +0.1662] | 1.097 | istotna |
| literatura | Bielik-v3 | +1.2798 [+1.2553; +1.2999] | 1.789 | istotna |
| literatura | PLLuM-12B | +0.6975 [+0.6760; +0.7159] | 1.430 | istotna |
| literatura | GPT-4o | +0.6529 [+0.6284; +0.6725] | 1.403 | istotna |
| prawo | TOKENIZATOREX-HF | -0.0051 [-0.0067; -0.0036] | 0.997 | nieistotna |
| prawo | TOKENIZATOREX-base | +0.3188 [+0.2951; +0.3448] | 1.211 | istotna |
| prawo | Slayer1B | +0.3364 [+0.3264; +0.3469] | 1.223 | istotna |
| prawo | APT3-1B | +0.0608 [+0.0455; +0.0759] | 1.040 | istotna |
| prawo | Pollock-2.0 | +0.0810 [+0.0651; +0.0969] | 1.054 | istotna |
| prawo | Bielik-v3 | +1.6063 [+1.5837; +1.6290] | 2.063 | istotna |
| prawo | PLLuM-12B | +0.9433 [+0.9232; +0.9634] | 1.624 | istotna |
| prawo | GPT-4o | +0.8456 [+0.8262; +0.8649] | 1.560 | istotna |
| sejm | TOKENIZATOREX-HF | -0.0004 [-0.0007; -0.0002] | 1.000 | nieistotna |
| sejm | TOKENIZATOREX-base | +0.2234 [+0.2176; +0.2291] | 1.173 | istotna |
| sejm | Slayer1B | +0.2960 [+0.2932; +0.2990] | 1.229 | istotna |
| sejm | APT3-1B | +0.1261 [+0.1224; +0.1298] | 1.098 | istotna |
| sejm | Pollock-2.0 | +0.1002 [+0.0927; +0.1071] | 1.078 | istotna |
| sejm | Bielik-v3 | +1.6014 [+1.5890; +1.6133] | 2.240 | istotna |
| sejm | PLLuM-12B | +0.9600 [+0.9515; +0.9687] | 1.743 | istotna |
| sejm | GPT-4o | +0.8766 [+0.8682; +0.8852] | 1.679 | istotna |
| nauka | TOKENIZATOREX-HF | -0.0009 [-0.0017; -0.0003] | 1.000 | nieistotna |
| nauka | TOKENIZATOREX-base | +0.1391 [+0.1035; +0.1623] | 1.070 | istotna |
| nauka | Slayer1B | +0.1196 [+0.0776; +0.1525] | 1.061 | istotna |
| nauka | APT3-1B | -0.0584 [-0.0962; -0.0244] | 0.970 | istotna |
| nauka | Pollock-2.0 | -0.0024 [-0.0162; +0.0110] | 0.999 | nieistotna |
| nauka | Bielik-v3 | +1.2069 [+1.1143; +1.2917] | 1.611 | istotna |
| nauka | PLLuM-12B | +0.5616 [+0.4818; +0.6319] | 1.284 | istotna |
| nauka | GPT-4o | +0.4750 [+0.3918; +0.5498] | 1.240 | istotna |
| dyskusje | TOKENIZATOREX-HF | -0.0005 [-0.0017; +0.0003] | 1.000 | nieistotna |
| dyskusje | TOKENIZATOREX-base | +0.2145 [+0.2050; +0.2228] | 1.130 | istotna |
| dyskusje | Slayer1B | +0.2542 [+0.2429; +0.2624] | 1.154 | istotna |
| dyskusje | APT3-1B | +0.1089 [+0.0961; +0.1199] | 1.066 | istotna |
| dyskusje | Pollock-2.0 | +0.0688 [+0.0565; +0.0809] | 1.042 | istotna |
| dyskusje | Bielik-v3 | +1.3521 [+1.3241; +1.3749] | 1.820 | istotna |
| dyskusje | PLLuM-12B | +0.7720 [+0.7480; +0.7924] | 1.468 | istotna |
| dyskusje | GPT-4o | +0.6712 [+0.6486; +0.6922] | 1.407 | istotna |
| angielski | TOKENIZATOREX-HF | -0.0009 [-0.0015; -0.0004] | 1.000 | nieistotna |
| angielski | TOKENIZATOREX-base | +0.0043 [-0.0025; +0.0114] | 1.002 | nieistotna |
| angielski | Slayer1B | -0.6823 [-0.6976; -0.6688] | 0.655 | istotna |
| angielski | APT3-1B | -0.1610 [-0.1674; -0.1542] | 0.919 | istotna |
| angielski | Pollock-2.0 | -0.2143 [-0.2224; -0.2062] | 0.892 | istotna |
| angielski | Bielik-v3 | -0.6393 [-0.6591; -0.6191] | 0.677 | istotna |
| angielski | PLLuM-12B | -0.7494 [-0.7721; -0.7281] | 0.621 | istotna |
| angielski | GPT-4o | -0.7972 [-0.8160; -0.7804] | 0.597 | istotna |
