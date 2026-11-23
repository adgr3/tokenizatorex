# Raport prosty v2.0 (ok. 1 strona)

TOKENIZATOREX tnie polski tekst najlepiej z 20 tokenizerów (1,656 tokena na słowo).
W wersji v2.0 sprawdziliśmy, jak tną teksty urzędowe (przetargi, ustawy, orzeczenia,
samorząd, granty, JSON) i porównaliśmy 20 tokenizerów.

Wyniki: oryginalny wariant V0-32k nadal wygrywa kompresję na wszystkich źródłach.
Wariant V3-32k (z poprawionymi cyframi) traci 8-12% kompresji, ale ma lepsze cięcie dat i kwot.
Żaden wariant nie ma „§” w V3 jako jednego tokena — to wada do naprawy w v2.1.

Martwe tokeny: ~8% u nas, ~35% u Slayera.

Wybór kandydata do modelu 150M: V3-32k (hipoteza), do potwierdzenia na małych modelach (TKX-D).
Fertility to warunek konieczny, nie dowód jakości modelu.
PY