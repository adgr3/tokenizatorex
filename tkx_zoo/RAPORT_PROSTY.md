# ZOO tokenizatorów — po prostu

Wzięliśmy 17 tokenizatorów i daliśmy im te same polskie teksty: ogłoszenia, Dz.U., KIO, samorząd, granty i JSON-y. Fertility to liczba części słów (tokenów) na jedno słowo. Im mniej, tym taniej.

Wygrywa **V0-32k**: na BZP 1,4304, na 149 grantach 1,4084. Najbliższy rywal przy tym samym słowniku 32k to Aster-0.5B (1,7313) — na części źródeł przewaga V0 mieści się w marginesie błędu, a na JSON held-out Aster jest nawet tańszy. V0 i V0J2 na polskim to remis w granicach CI; V0J2 wygrywa wyraźnie na JSON.

Rodzina PLLuM tnie polski drożej: 4B 2,3988, 8B 2,9169, 12B 2,6591. PLLuM 4B zachowuje się jak Gemma 3, 12B jak Mistral Nemo. Bielik 4.5B daje tyle samo tokenów co Bielik 1.5B.

Liczby uczą, że cięcie cyfr po trzy jest tańsze niż pojedynczo. Bielik 4.5B i 1.5B nie mają „§” jako jednego tokenu (3 tokeny).

Duży słownik kosztuje: 262 147 tokenów w PLLuM 4B to 201,33 M parametrów (134,2%) w modelu 150M. V0 ma 32 000 tokenów i 16,4%.

Dodaliśmy też dwa tokenizery DanielK 32k z publicznego PR (po 32 768 tokenów w słowniku). Na BZP dają 1,7680 i 1,7687 — nadal więcej niż V0.

Jedna rzecz została otwarta: baza Llama 3.1 dla PLLuM 8B (gated, czeka na zatwierdzenie Meta). Nie podstawiliśmy żadnym innym repozytorium.

