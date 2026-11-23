# Raport prosty v2.0

TOKENIZATOREX ma warianty o niskiej fertility na polskim tekście. W v2.0 porównano warianty na 8 źródłach testowych (przetargi, Dz.U., KIO, samorząd, granty, JSON narzędzi, JSON BZP, kontrola ogólna).

Wyniki z danych (`results/tkx_v2_fertility.json`): V0-32k ma najniższą fertility na wszystkich 8 źródłach (punktowo). V3-32k przegrywa z V0 na 7 z 8 źródeł; na 1 źródle (kontrola ogólna) też przegrywa punktowo. CI rozdzielają V0 od V3 wyraźnie tylko na części źródeł; Dz.U. i granty mają n=12, więc ranking jest niepewny.

Martwe tokeny: V0-32k 8,12%, V3-32k 7,83%, Slayer1B-1.08 35,03% (`results/tkx_v2_dead_tokens.json`). Uwaga: 35,03% Slayera dotyczy korpusu polskiego; w audycie szerszym 8,90%.

Znaki specjalne: V3-32k nie ma `§` jako jednego tokena (2 tokeny). V0-32k ma `§` jako 1 token. Dane: `results/tkx_v2_special_chars.json`.

Kandydat domyślny v2.0: **V0-32k**. V3-32k to wariant eksperymentalny z cięciem cyfr i wadami (NFD→NFC, brak `§` jako 1 token, gorsza fertility na większości źródeł). Ostateczny wybór po TKX-D (małe modele, BPB, ≥ 3 seedy). Fertility to warunek konieczny, nie dowód jakości modelu.
