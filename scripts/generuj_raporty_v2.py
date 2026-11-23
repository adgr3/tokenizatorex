import json, os
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
RES = REPO / 'results'

fert = json.load(open(RES/'tkx_v2_fertility.json', encoding='utf-8'))
dead = json.load(open(RES/'tkx_v2_dead_tokens.json', encoding='utf-8'))
spec = json.load(open(RES/'tkx_v2_special_chars.json', encoding='utf-8'))
pat = json.load(open(RES/'tkx_v2_patterns.json', encoding='utf-8'))
wz = json.load(open(REPO/'tkx_v2/wzorce.json', encoding='utf-8'))

SOURCES = [
    ('1_bzp','BZP (ogłoszenia)'),
    ('2_du_eli','Dz.U. 2026 ELI'),
    ('3_kio','KIO'),
    ('4_samorzad','Samorząd (uchwały)'),
    ('5_granty','Granty'),
    ('6_json_narzedzia','JSON narzędzi (tc1)'),
    ('7_ogolny','Kontrola ogólna (HPLT web)'),
    ('json_bzp_tabele','JSON BZP (tabele, extra)'),
]
TOKS = ['TKX/V0-32k','TKX/V3-32k','Slayer1B-1.08']

def f3(x):
    return f"{x:.3f}".replace('.',',')

def f2(x):
    return f"{x:.2f}".replace('.',',')

def pct(x):
    return f"{x:.2f}%".replace('.',',')

def get_f(src, tok):
    return fert['sources'][src]['tokenizers'][tok]

# report: test domenowy
lines = []
lines.append('# RAPORT TEST DOMENOWY — TOKENIZATOREX v2.0')
lines.append('')
lines.append('Data: 23.11.2026. Liczby z `results/tkx_v2_*.json` (generowane skryptem).')
lines.append('')
lines.append('## 1. Korpus')
lines.append('')
lines.append('Źródła i rozmiary z `results/tkx_v2_fertility.json`:')
lines.append('')
lines.append('| Źródło | Dokumenty | Słowa | Bajty |')
lines.append('|---|---:|---:|---:|')
for sid, name in SOURCES:
    s = fert['sources'][sid]
    lines.append(f"| {name} | {s['docs']} | {s['words']} | {s['bytes']} |")
lines.append('')
lines.append('Uwaga: Dz.U. i granty mają po 12 dokumentów — ranking fertility na tych źródłach jest niepewny (mała próba).')
lines.append('')
lines.append('## 2. Fertility (tokeny/słowo) z 95% CI')
lines.append('')
for sid, name in SOURCES:
    s = fert['sources'][sid]
    lines.append(f'### {name} (n={s["docs"]} dok.)')
    lines.append('')
    lines.append('| Tokenizer | Fertility | 95% CI | Bajty/token |')
    lines.append('|---|---:|---:|---:|')
    for tok in TOKS:
        r = s['tokenizers'][tok]
        lines.append(f"| {tok} | {f3(r['fertility'])} | [{f3(r['fertility_ci_lo'])}, {f3(r['fertility_ci_hi'])}] | {f3(r['bytes_per_token'])} |")
    lines.append('')
lines.append('Wniosek z danych: V0-32k ma najniższą fertility na wszystkich 8 źródłach (punktowo). CI rozdzielają V0 od V3 wyraźnie tylko na części źródeł; na Dz.U. i grantach (n=12) ranking jest niepewny.')
lines.append('')
lines.append('## 3. Znaki specjalne')
lines.append('')
chars = spec['chars']
lines.append(f'Lista znaków (n={len(chars)}), z pliku `results/tkx_v2_special_chars.json`: ' + ', '.join(f'`{c}`' for c in chars))
lines.append('')
lines.append('| Tokenizer | Liczba znaków jako 1 token | `§` jako 1 token |')
lines.append('|---|---:|---:|')
for tok in TOKS:
    row = spec['tokenizers'][tok]
    cnt = sum(1 for c in chars if row.get(c) is False or row.get(c) is True and row[c])
    # recompute properly
    cnt = sum(1 for c in chars if row.get(c) is True)
    lines.append(f"| {tok} | {cnt} | {'TAK' if row.get('§') else 'NIE'} |")
lines.append('')
lines.append('V3-32k nie ma `§` jako jednego tokena (encode daje 2 tokeny). V0-32k i Slayer mają `§` jako 1 token.')
lines.append('')
lines.append('## 4. Martwe tokeny')
lines.append('')
lines.append('| Tokenizer | Vocab | Martwe | % |')
lines.append('|---|---:|---:|---:|')
for tok in TOKS:
    r = dead['tokenizers'][tok]
    lines.append(f"| {tok} | {r['vocab']} | {r['dead']} | {pct(r['dead_pct'])} |")
lines.append('')
lines.append('Uwaga: porównanie ze Slayerem nie jest bezpośrednie — Slayer ma słownik polsko-angielski; na polskim korpusie część słownika z natury jest nieużywana. W audycie szerszym martwe tokeny Slayera to 8,90%.')
lines.append('')
lines.append('## 5. Wzorce i segmentacja')
lines.append('')
lines.append(f'Wzorce: {wz["count"]} w {len(set(i["category"] for i in wz["items"]))} kategoriach (`tkx_v2/wzorce.json`).')
lines.append('Segmentacja mierzona przez `encoding.offsets` (liczba kontekstów z identyczną segmentacją, sklejenia z poprzedzającym znakiem, segmentacja tekstowa) — zapis w `results/tkx_v2_patterns.json`.')
lines.append('')
# small summary for V0,V3,Slayer
for tok in TOKS:
    items = pat['tokenizers'][tok]['per_item']
    ident = sum(1 for i in items if i.get('contexts_identical'))
    merged = sum(1 for i in items if i.get('merged_with_prev_count',0)>0)
    lines.append(f'- {tok}: identyczna segmentacja w 5/5 kontekstach dla {ident}/{len(items)} wzorców; wzorce ze sklejeniem z poprzedzającym znakiem: {merged}/{len(items)}.')
lines.append('')
lines.append('## 6. Kandydat')
lines.append('')
lines.append('Domyślny wariant v2.0: **V0-32k** (najniższa fertility na wszystkich 8 źródłach, `§` jako 1 token, round-trip NFC/NFD bez zmian w próbce syntetycznej).')
lines.append('V3-32k: wariant eksperymentalny z cięciem cyfr; wygrywa na identyfikatorach/kodach/sygnaturach, przegrywa na datach i kwotach; nie ma `§` jako jednego tokena; normalizuje NFD→NFC (4 błędy round-trip w próbie).')
lines.append('Ostateczny wybór dopiero po TKX-D (małe modele, BPB, ≥ 3 seedy). Fertility to warunek konieczny, nie dowód jakości.')
lines.append('')
(REPO/'tkx_v2/RAPORT_TEST_DOMENOWY.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
print('dom')

# RAPORT_PROSTY_V2
rp = []
rp.append('# Raport prosty v2.0')
rp.append('')
rp.append('TOKENIZATOREX ma warianty o niskiej fertility na polskim tekście. W v2.0 porównano warianty na 8 źródłach testowych (przetargi, Dz.U., KIO, samorząd, granty, JSON narzędzi, JSON BZP, kontrola ogólna).')
rp.append('')
rp.append('Wyniki z danych (`results/tkx_v2_fertility.json`): V0-32k ma najniższą fertility na wszystkich 8 źródłach (punktowo). V3-32k przegrywa z V0 na 7 z 8 źródeł; na 1 źródle (kontrola ogólna) też przegrywa punktowo. CI rozdzielają V0 od V3 wyraźnie tylko na części źródeł; Dz.U. i granty mają n=12, więc ranking jest niepewny.')
rp.append('')
rp.append(f"Martwe tokeny: V0-32k {pct(dead['tokenizers']['TKX/V0-32k']['dead_pct'])}, V3-32k {pct(dead['tokenizers']['TKX/V3-32k']['dead_pct'])}, Slayer1B-1.08 {pct(dead['tokenizers']['Slayer1B-1.08']['dead_pct'])} (`results/tkx_v2_dead_tokens.json`). Uwaga: 35,03% Slayera dotyczy korpusu polskiego; w audycie szerszym 8,90%.")
rp.append('')
rp.append('Znaki specjalne: V3-32k nie ma `§` jako jednego tokena (2 tokeny). V0-32k ma `§` jako 1 token. Dane: `results/tkx_v2_special_chars.json`.')
rp.append('')
rp.append('Kandydat domyślny v2.0: **V0-32k**. V3-32k to wariant eksperymentalny z cięciem cyfr i wadami (NFD→NFC, brak `§` jako 1 token, gorsza fertility na większości źródeł). Ostateczny wybór po TKX-D (małe modele, BPB, ≥ 3 seedy). Fertility to warunek konieczny, nie dowód jakości modelu.')
(REPO/'tkx_v2/RAPORT_PROSTY_V2.md').write_text('\n'.join(rp)+'\n', encoding='utf-8')
print('prosty')

# ZNANE_WADY
zw = []
zw.append('# Znane wady TOKENIZATOREX (v2.0)')
zw.append('')
zw.append('Każda wada z dowodem i propozycją naprawy (v2.1). Liczby z `results/tkx_v2_*.json`.')
zw.append('')
zw.append('## W1. Znak `§` rozbity w wariancie V3-32k')
zw.append('')
zw.append('- **Dowód:** `results/tkx_v2_special_chars.json` — V3-32k nie ma `§` jako pojedynczego tokena (`encode` daje 2 tokeny); V0-32k ma 1 token.')
zw.append('- **Przyczyna (hipoteza):** wymuszone tokeny cyfr i ograniczony budżet słownika mogły wypchnąć rzadkie znaki; do potwierdzenia na danych treningowych V3.')
zw.append('- **Naprawa (v2.1):** dopisać `§` na końcu scaleń albo zarezerwować slot specjalny.')
zw.append('')
zw.append('## W2. Skróty prawne (Dz. U., Pzp, tj.)')
zw.append('')
zw.append('- **Dowód:** `results/tkx_v2_patterns.json` — segmentacja tekstowa pokazuje rozbicia (np. `Dz. U.` jest rozbijane; `Pzp` rozbijane w części wariantów).')
zw.append('- **Naprawa:** dopisać skróty na końcu scaleń; rozważyć trening na mieszance 10–30% tekstów urzędowych.')
zw.append('')
zw.append('## W3. JSON wywołań narzędzi')
zw.append('')
v0_json = get_f('6_json_narzedzia','TKX/V0-32k')
sl_json = get_f('6_json_narzedzia','Slayer1B-1.08')
v0_toks = round(v0_json['fertility'] * fert['sources']['6_json_narzedzia']['words'])
sl_toks = round(sl_json['fertility'] * fert['sources']['6_json_narzedzia']['words'])
zw.append(f"- **Dowód:** na `tc1_json_tools` (200 dok., {fert['sources']['6_json_narzedzia']['words']} słów) V0-32k ma fertility {f3(v0_json['fertility'])} vs Slayer {f3(sl_json['fertility'])} (`results/tkx_v2_fertility.json`), czyli V0 tańszy na tym korpusie; łącznie {v0_toks} vs {sl_toks} tokenów. Osobno 10 wzorców JSON z `tkx_v2/wzorce.json`: suma tokenów standalone Slayer 298 vs V0 321 (`results/tkx_v2_patterns.json` po kategoriach). To różne miary — nie mieszać.")
zw.append('- **Naprawa:** tokeny dla `<tool_call>` i kluczy JSON; ocena na BPB w TKX-D.')
zw.append('')
zw.append('## W4. Angielski')
zw.append('')
zw.append('- **Dowód:** TKX-A — fertility 1,97 vs Slayer 1,30 na angielskim (znany kompromis).')
zw.append('- **Status:** akceptowany kompromis; bezpiecznik: brak regresji > 5%.')
zw.append('')
zw.append('## W5. Artefakty SuperBPE')
zw.append('- Niektóre superwordy mogą zaczynać się w środku słowa; częste słowa mogą stracić własny token.')
zw.append('- **Naprawa:** audyt słownika, filtrowanie merge w v2.1.')
zw.append('')
zw.append('## W6. Martwe tokeny')
zw.append('')
zw.append('Uwaga: porównanie ze Slayerem nie jest bezpośrednie (słownik polsko-angielski). Na polskim korpusie 35,03% martwych; w audycie szerszym 8,90%.')
zw.append(f"- **Dowód:** V0-32k {pct(dead['tokenizers']['TKX/V0-32k']['dead_pct'])}, V3-32k {pct(dead['tokenizers']['TKX/V3-32k']['dead_pct'])}, Slayer {pct(dead['tokenizers']['Slayer1B-1.08']['dead_pct'])} (`results/tkx_v2_dead_tokens.json`).")
zw.append('')
zw.append('## Czego nie sprawdzają testy')
zw.append('- Jakość modelu downstream (wymaga TKX-D).')
zw.append('- Morfologia (otwarte pytanie).')
zw.append('- APT4/Bielik-1.5B-v3: tokenizer jest w wynikach fertility; nie wykonano testów downstream.')
(REPO/'tkx_v2/ZNANE_WADY.md').write_text('\n'.join(zw)+'\n', encoding='utf-8')
print('zw')

# RELEASE_NOTES
rn = []
rn.append('# RELEASE NOTES — TOKENIZATOREX v2.0 (draft)')
rn.append('')
rn.append('Status: DRAFT (wydanie po scaleniu PR i zgodzie właściciela).')
rn.append('')
rn.append('## Co to jest v2.0')
rn.append('')
rn.append('v2.0 to stan po TKX-A + TKX-C + test domenowy na tekstach urzędowych (BZP, Dz.U. ELI, KIO, samorząd, granty, JSON narzędzi, kontrola ogólna).')
rn.append('')
rn.append('## Wariant domyślny i kandydaci')
rn.append('')
rn.append('Z danych (`results/tkx_v2_fertility.json`): **V0-32k ma najniższą fertility na wszystkich 8 źródłach** (punktowo). CI rozdzielają V0 od V3 wyraźnie tylko na części źródeł; Dz.U. i granty mają n=12, więc ranking jest niepewny.')
rn.append('')
rn.append('**Domyślny wariant v2.0 = V0-32k.** Ma `§` jako 1 token i zachowuje round-trip NFC/NFD w próbce syntetycznej.')
rn.append('')
rn.append('**V3-32k = wariant eksperymentalny z cięciem cyfr.** Wygrywa na identyfikatorach, kodach pocztowych, numerach BZP, skrótach i sygnaturach w wzorcach; przegrywa na datach i kwotach; nie ma `§` jako jednego tokena; normalizuje NFD→NFC (4 błędy round-trip w próbie syntetycznej). Na źródłach testowych traci vs V0: BZP +8,54%, Dz.U. +5,43%, KIO +1,87%, samorząd +4,39%, granty +6,18%, JSON narzędzi +2,76%, JSON BZP tabele +8,35%, ogólny +1,68% (liczone z fertility w `results/tkx_v2_fertility.json`).')
rn.append('')
rn.append('Ostateczny wybór dopiero po TKX-D (małe modele, BPB, ≥ 3 seedy). Fertility to warunek konieczny, nie dowód jakości (Schmidt i in.).')
rn.append('')
rn.append('## Znane wady')
rn.append('')
rn.append('Zob. `tkx_v2/ZNANE_WADY.md`. Uwaga: porównanie martwych tokenów ze Slayerem nie jest bezpośrednie (słownik polsko-angielski).')
rn.append('')
rn.append('## Jak sprawdzić samemu')
rn.append('')
rn.append('```bash')
rn.append('python scripts/sprawdz_sam.py "Twój tekst."')
rn.append('python scripts/sprawdz_sam.py --wszystkie "Twój tekst."')
rn.append('```')
rn.append('')
rn.append('Domyślnie lokalne tokenizery TOKENIZATOREX + Slayer; `--wszystkie` dodaje zewnętrzne (wymaga cache/logowania).')
rn.append('')
rn.append('## Nie sprawdzono (wprost)')
rn.append('')
rn.append('- Przeciek względem próbki treningowej HPLT (13-gramy) — nie wykonano.')
rn.append('- Bielik-1.5B-v3 (APT4) jest obecny w wynikach fertility; testy downstream nie wykonane. W tym środowisku tokenizer Bielika jest gated/brak cache dla recompute znaków specjalnych — oznaczono jako UNKNOWN w `results/tkx_v2_special_chars.json`.')
rn.append('- Efektywność Rényiego (TokEval) — zaplanowana, nie policzona.')
rn.append('')
rn.append('## Plan v2.1 i TKX-D')
rn.append('')
rn.append('- v2.1: naprawa `§` (V3), skróty prawne, tokeny JSON; mieszanka 10–30% tekstów urzędowych.')
rn.append('- TKX-D: wybór wariantu i rozmiaru słownika (16k/24k/32k) na małych modelach; ≥ 3 seedy; BPB.')
rn.append('')
rn.append('## Weryfikacja')
rn.append('')
rn.append('`pytest -q` zielone. `python scripts/sprawdz_liczby_v2.py` exit 0. Liczby w raportach pochodzą z `results/tkx_v2_*.json`. Weryfikacja przez człowieka wymagana.')
(REPO/'RELEASE_NOTES_v2.0.md').write_text('\n'.join(rn)+'\n', encoding='utf-8')
print('rn')

# KARTA_WYMAGAN
ka = []
ka.append('# Karta wymagań TOKENIZATOREX v2.0 — tokenizer pod polski model ≤ 150M (polszczyzna urzędowa)')
ka.append('')
ka.append('Wersja: 23.11.2026. Powiązane: project-hub #566 (model 150M), #576 (dziennik), TKX-A, TKX-C.')
ka.append('')
ka.append('Zasada: nie ma najlepszego tokenizera — jest najlepszy do zadania i rozmiaru modelu. Fertility to warunek konieczny, nie dowód jakości. Ostateczny wybór w TKX-D.')
ka.append('')
ka.append('## Macierz zgodności O1–O9 (z danych)')
ka.append('')
ka.append('Wartości z `results/*.json` i pomiarów opisanych w raportach. PASS/FAIL nie są zgadywane.')
ka.append('')
ka.append('| Wymaganie | V0-32k | V3-32k | Slayer1B-1.08 | Dowód |')
ka.append('|---|---:|---:|---:|---|')
ka.append('| O1 Round-trip (NFC/NFD próbka syntetyczna) | PASS (NFC+NFD) | FAIL (4 błędy NFD→NFC w próbie) | PASS (NFC+NFD) | test `tests/test_tkx_v2_r2.py` |')
ka.append('| O2 NFC (brak NFD na wyjściu / normalizacja) | PASS (zachowuje NFD) | FAIL (normalizuje NFD→NFC) | PASS (zachowuje NFD) | test `tests/test_tkx_v2_r2.py` |')
ka.append('| O3 Znak `§` jako pojedynczy token | PASS (1 token) | FAIL (2 tokeny) | PASS (1 token) | `results/tkx_v2_special_chars.json` |')
ka.append('| O4 Lata 2015–2035 (≤ 2 tokeny/rok w formatach) | UNKNOWN | UNKNOWN | UNKNOWN | nie zmierzono w tym raporcie |')
ka.append('| O5 Kwoty (≤ 6 tokenów/kwota, spójnie) | FAIL | FAIL | FAIL | `results/tkx_v2_patterns.json` (kategoria kwoty, średnie > 6 nie spełniają progu) |')
ka.append('| O6 Daty (≤ 5 tokenów/data) | FAIL | FAIL | FAIL | `results/tkx_v2_patterns.json` (kategoria daty_iso) |')
ka.append('| O7 CPV (≤ 3 tokeny/kod) | FAIL | FAIL | FAIL | `results/tkx_v2_patterns.json` (kategoria cpv) |')
ka.append('| O8 Martwe tokeny ≤ 5% | FAIL (8,12%) | FAIL (7,83%) | FAIL (35,03%) | `results/tkx_v2_dead_tokens.json` |')
ka.append('| O9 Przeciek 13-gram ≤ 20% | UNKNOWN | UNKNOWN | UNKNOWN | nie wykonano |')
ka.append('')
ka.append('Uwaga: żaden z ocenianych wariantów (V0, V3, Slayer) nie spełnia O5–O8. Progi O5–O8 okazały się nierealne dla wszystkich tokenizerów (także Slayera) → do rewizji w v2.1 z uzasadnieniem, a nie po cichu.')
ka.append('')
ka.append('## Wymagania (skrót)')
ka.append('')
ka.append('- O1: round-trip `decode(encode(x)) == x` 100%.')
ka.append('- O2: brak NFD w słowniku i na wyjściu; 100% dokumentów.')
ka.append('- O3: znak `§` jako pojedynczy token w słowniku i kodowaniu (nie cały wzorzec `§ 362(a)`).')
ka.append('- O4: lata 2015–2035 ≤ 2 tokeny/rok.')
ka.append('- O5–O7: progi tokenów dla kwot/daty/CPV — do rewizji w v2.1.')
ka.append('- O8: martwe tokeny ≤ 5% słownika.')
ka.append('- O9: przeciek 13-gram ≤ 20% dokumentów.')
ka.append('')
ka.append('## Bezpieczniki')
ka.append('- Angielski: brak regresji > 5% względem V0-32k (procentowy próg; wartość bazowa do pomiaru w TKX-D).')
ka.append('- JSON narzędzi: nie gorszy niż Slayer (metryka do doprecyzowania: fertility na korpusie vs suma wzorców).')
ka.append('')
ka.append('## Definicja gotowe')
ka.append('- `pytest -q` zielone.')
ka.append('- `python scripts/sprawdz_liczby_v2.py` exit 0.')
ka.append('- Liczby w raportach z `results/tkx_v2_*.json`.')
(REPO/'tkx_v2/KARTA_WYMAGAN.md').write_text('\n'.join(ka)+'\n', encoding='utf-8')
print('ka')

# KORPUS_DOMENOWY
kd = []
kd.append('# Korpus testu domenowego TOKENIZATOREX v2.0')
kd.append('')
kd.append('Pełne teksty poza repo (zasada: bez surowych tekstów w git). W repo: manifest, metryki, ten opis.')
kd.append('')
kd.append('## Źródła (zgodne z `results/tkx_v2_fertility.json`)')
kd.append('')
kd.append('| # | Domena | Źródło | Dokumenty | Słowa | Bajty |')
kd.append('|---:|---|---|---:|---:|---:|')
for sid, name in SOURCES:
    s = fert['sources'][sid]
    kd.append(f"| {sid} | {name} | patrz manifest/metryki | {s['docs']} | {s['words']} | {s['bytes']} |")
kd.append('')
kd.append('## Zestawy dodatkowe opisane w tkx_v2/MANIFEST.json')
kd.append('- BZP 500 (spec1): `D:\VPS\fabryka\spec1\data\test.jsonl` (poza repo).')
kd.append('- JSON narzędzi 200 (tc1): `D:\VPS\fabryka\tc1\dane\test.jsonl` (poza repo).')
kd.append('')
kd.append('## Przeciek')
kd.append('13-gramy vs próbka treningowa HPLT 400 MB — nie wykonano. Próg stopu: > 20% dokumentów z trafieniem.')
kd.append('')
kd.append('## Licencje / status')
kd.append('Dokumenty urzędowe są publiczne. HPLT/FineWeb-2: ODC-By; Wikipedia: CC BY-SA.')
(REPO/'tkx_v2/KORPUS_DOMENOWY.md').write_text('\n'.join(kd)+'\n', encoding='utf-8')
print('kd')
