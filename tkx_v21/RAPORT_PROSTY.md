# TOKENIZATOREX v2.1-JSON — prostym językiem

**Pytanie:** czy dodanie JSON-a do treningu tokenizera zmniejszy liczbę tokenów na wywołaniach narzędzi, nie psując polskiego?

**Odpowiedź:** JSON jest dużo tańszy — **V0J2-32k** na teście tc1 oszczędza 23,2% tokenów, a na nowych narzędziach 33,0%. Ale **nie ma kandydata**, bo polski na jednym źródle (granty, 12 dokumentów) rośnie o 3,75% — powyżej progu 1%. Przedziały ufności tego źródła pokrywają się z V0, więc to wynik na granicy szumu, ale zgodnie z regułą: brak kandydata.

- Odtworzenie V0: merge'e identyczne, tokeny na BZP identyczne.
- JSON na teście dla najbliższego (V0J2-32k): tc1 -23,22%; nowe narzędzia -33,04%.
- „§”: 1 token w V0R i we wszystkich wariantach V0J.
- Tokeny specjalne: 6/6 atomowych w V0J5S, ale na JSON +0,22% tokenów względem V0J5 (nie zastępują słownika JSON).
- Przeciek: OK.
- Round-trip: 0 błędów na 700 przypadków.

Poprawka 2 (po fakcie): na 149 ogłoszeniach grantowych V0J2-32k rośnie tylko o 0,20% (CI V0R 1,3798–1,4381 vs V0J2-32k 1,3828–1,4401), więc jest kandydatem warunkowym do TKX-D, a nie wybranym według protokołu. Ta poprawka jest jawna i po fakcie; oryginalny wynik „brak kandydata” zostaje na pierwszym miejscu. Testy JSON są na naszych danych syntetycznych (tc1 i generator), więc potwierdzenie musi przyjść z TKX-D.

**Co dalej:** sprawdzić V0J2 (i ewentualnie V0J5) na małym modelu (TKX-D), z bramką opartą na CI, nie tylko na punkcie. Automaty nie zastępują decyzji właściciela.

