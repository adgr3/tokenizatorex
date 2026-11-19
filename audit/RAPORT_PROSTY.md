# TOKENIZATOREX — raport prosty (dla właściciela)

Data: 19.11.2026 · Wersja bez żargonu · Szczegóły: `audit/RAPORT_SLABOSCI.md`

## Najkrócej

TOKENIZATOREX jest **bardzo dobry w przeciętnym polskim tekście urzędowym**:
na 7 sprawdzonych dziedzinach (przetargi, KIO, uchwały, granty, prawo, OCR
prasy, tabele) potrzebuje **1,68 kawałka na słowo**. Pollock potrzebuje 1,79,
APT3 1,86, a Slayer 2,03. To znaczy: ten sam dokument zmieści się w mniejszej
liczbie „klocków”, więc model czyta go taniej.

Ale są **cztery rzeczy, które psują jakość** i które warto naprawić przed
treningiem modelu 150M. Nie są to katastrofy — to konkretne, mierzalne rzeczy.

## Co jest mocne

1. **Mało kawałków na polski tekst urzędowy.** 1,68 na słowo to najlepszy
   wynik w naszym zestawie. Na przetargach 1,56, na KIO 1,40.
2. **Tanie liczby i daty.** Kwota `1 234 567,89 zł` to 3,87 kawałka, podczas
   gdy Slayer potrzebuje 5,23. Data słowna: 3,76 vs 5,31. Przepis: 4,20 vs 5,78.
3. **Słownik nie ma „martwych” kawałków.** Tylko 1,8% kawałków nigdy nie
   wystąpiło (Slayer: 8,9%, Pollock: 9,4%). To znaczy, że słownik jest dobrze
   dopasowany do polskiego, a nie „napchany” nieużywanymi znakami.
4. **Jest szybki w wersji dla modelu (HF).** 575 tys. kawałków na sekundę,
   czyli około 3 MB tekstu na sekundę. Wersja „dokładna” w Pythonie jest
   3,3× wolniejsza, ale to i tak minuty, nie godziny, przy 300 MB danych.
5. **Jest stabilny wydajnościowo.** Gdy wytrenowaliśmy go od nowa na innym
   kawałku internetu, tnie tekst prawie tak samo (−0,1% do +2%), choć 10,7%
   kawałków jest innych.

## Co jest słabe

1. **Zamrożony kalendarz.** Lata 2015–2024 to **jeden** kawałek, a 2025 i 2026
   to **dwa**. Przykład: `2024 r.` → `202│4·r.`, ale `2026 r.` → `202│6·r.`.
   Model nie widzi wspólnego wzorca między starym i nowym rokiem. Każdy nowy
   rok będzie „nowy” i droższy. To najważniejsza słabość dla ogłoszeń z 2027+.
2. **Ten sam zapis tnie się różnie w różnym otoczeniu.** `Dz.U.` raz jest
   `Dz│.│U.`, a raz `│Dz.│U.` — zależnie od tego, co stoi obok. W 12–57%
   przypadków (w zależności od zapisu) podział jest inny niż najczęstszy.
   Slayer w wielu zapisach jest w 100% powtarzalny. Dla modelu to jakby ten
   sam numer raz był jednym słowem, a raz dwoma.
3. **Nie lubi PDF-ów i wielkich liter.** Tekst z PDF, który ma „rozłożone”
   polskie znaki (np. `ą` jako `a` + ogonek), jest **o 46% droższy**. Tekst
   pisany WIELKIMI LITERAMI jest **o 107% droższy**. Tytuły — o 31%.
4. **Eksport dla modelu (HF) nie jest w 100% tym samym tokenizerem.** Na
   tekstach urzędowych tylko 97,27% fragmentów tnie się identycznie jak
   w wersji referencyjnej (na web 99,36%). Różnice do 0,5% kawałków. To znaczy:
   **trening i ocena muszą używać tego samego pliku**, inaczej porównujemy
   jabłka z gruszkami.
5. **Wikipedii i nauki nie wygrywa.** W Wikipedii Pollock jest lepszy o 1,25%,
   w nauce APT3 o 2,95%, a angielski jest 1,68× droższy niż w GPT-4o. To znane
   i akceptowalne ograniczenie tokenizera „pod polski urzędowy”.
6. **Morfologia (odmiana słów) jest słabsza niż w modelach bazowych.**
   MorphScore precision 0,023 vs Slayer 0,082 i Bielik 0,135. Ale literatura
   mówi, że to słabo przekłada się na jakość modelu (R² ≈ 0,02), więc nie
   panikujemy i nie optymalizujemy na ślepo.

## Co naprawić w pierwszej kolejności (TKX-C)

1. **Ujednolicić eksport HF.** To nie „optymalizacja”, to poprawność. Bez tego
   model może się uczyć na jednym tokenizerze, a być oceniany na innym.
2. **Naprawić cyfry i lata.** Grupowanie cyfr od prawej albo pojedyncze cyfry
   plus `r.` jako osobny kawałek. Zysk: nowy rok przestaje być o 100% droższy,
   a dokumenty z datami/kwotami tanieją o 1–3%.
3. **Uporządkować zapisy urzędowe.** `Dz.U.`, `lit.`, `poz.`, CPV, znak sprawy
   powinny mieć jeden, powtarzalny podział niezależnie od kontekstu.
4. **NFC przed kodowaniem (w pipeline, nie w tokenizerze).** Dla PDF-ów to
   różnica 46% tokenów. Ale to zmienia tekst, więc decyzja należy do właściciela.
5. **Dopiero potem**: wielkie litery, mieszanka danych, filtr boilerplate'u,
   zakaz superwordów od środka słowa, Picky BPE/BoundlessBPE. To rzeczy
   o mniejszym zysku lub większym ryzyku.

## Czego nie robić

* Nie gonić „dziwnych tokenów” — jest ich mało (3,5% superwordów, 0,09% użyć)
  i nie psują średniego wyniku.
* Nie „naprawiać” angielskiego kosztem polskiego — ten tokenizer ma być polski.
* Nie zmieniać tokenizera bez ponownego pomiaru parytetu HF i testów.

## Słowniczek

* **Token (kawałek)** — najmniejsza jednostka, na którą tokenizer dzieli tekst.
* **Fertility** — liczba tokenów na słowo; mniej = taniej i więcej tekstu
  w oknie kontekstu.
* **Superword** — token obejmujący kilka słów, np. ` w związku z`.
* **NDF/NFC** — dwa sposoby zapisu polskich liter w Unicode; NFD rozkłada
  `ą` na `a` + ogonek, NFC trzyma `ą` jako jeden znak.
* **CAPS** — tekst WIELKIMI LITERAMI.
* **Parytet HF** — czy eksport dla biblioteki Hugging Face tnie tekst tak samo
  jak nasz enkoder referencyjny.
* **CI (przedział ufności)** — widełki, w których z 95% pewnością jest
  prawdziwa liczba; jeśli widełki różnicy nie zawierają zera, różnica jest
  „istotna”.
* **Bootstrap** — losowanie dokumentów ze zwracaniem, żeby oszacować
  niepewność bez zakładania rozkładu.
* **Rényi** — miara, jak dobrze wykorzystany jest cały słownik (wyżej = lepiej).
* **MorphScore** — miara, czy tokenizer tnie słowa na granicach morfemów.
* **OCR** — automatyczne rozpoznawanie tekstu ze skanu; ma błędy, celowo
  uwzględnione w dziedzinie `ocr_prasa`.

## Jedno zdanie na koniec

TOKENIZATOREX jest **najlepszym tanim tokenizerem do polskiego urzędowego**,
ale przed treningiem modelu 150M trzeba naprawić **parytet HF, cyfry/lata
i spójność zapisów** — reszta może poczekać.
