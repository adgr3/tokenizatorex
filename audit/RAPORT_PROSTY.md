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
Dwie z nich dotyczą jednak decyzji o modelu, nie samego tokenizera.

## Co jest mocne

1. **Mało kawałków na polski tekst urzędowy.** 1,68 na słowo to najlepszy
   wynik w naszym zestawie. Na przetargach 1,56, na KIO 1,40.
2. **Tanie liczby i daty.** Kwota `1 234 567,89 zł` to 3,87 kawałka, podczas
   gdy Slayer potrzebuje 5,23. Data słowna: 3,76 vs 5,31. Przepis: 4,20 vs 5,78.
3. **Słownik nie ma „martwych” kawałków.** Tylko 1,8% kawałków nigdy nie
   wystąpiło (Slayer: 8,9%, Pollock: 9,4%). To znaczy, że słownik jest dobrze
   dopasowany do polskiego, a nie „napchany” nieużywanymi znakami.
   **Uwaga:** Rényi, którym wcześniej chwaliliśmy się jako „najmocniejszą
   przewagą”, jest tylko miarą opisową. APT3 ma go nieco wyżej (0,531 vs 0,527
   w formie Zouhara; 0,00768 vs 0,00742 w formie `exp(H)/|V|`), a literatura
   (Cognetta i in. 2024) pokazuje, że Rényi nie przewiduje jakości modelu.
4. **Jest szybki w wersji dla modelu (HF).** 575 tys. kawałków na sekundę,
   czyli około 3 MB tekstu na sekundę. Wersja „dokładna” w Pythonie jest
   3,3× wolniejsza, ale to i tak minuty, nie godziny, przy 300 MB danych.
5. **Jest stabilny wydajnościowo.** Gdy wytrenowaliśmy go od nowa na innym
   kawałku internetu, tnie tekst prawie tak samo (−0,1% do +2%), choć 10,7%
   kawałków jest innych.
6. **Na 4 nowych źródłach (Dolny Śląsk, TED, SAOS, NCN) przewaga nad Pollockiem
   się utrzymuje: −6,11%.**

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
   tekstach urzędowych 97,27% fragmentów ma te same **identyfikatory** co
   w wersji referencyjnej (na web 99,36%). Różnice do 0,5% kawałków. Ale
   **po zdekodowaniu 100% tekstu jest identyczne** — to różnica scalania,
   nie utrata znaków. Wniosek: **trening i ocena muszą używać tego samego
   pliku**, inaczej porównujemy jabłka z gruszkami.
5. **Wikipedii i nauki nie wygrywa.** W Wikipedii Pollock jest lepszy o 1,25%,
   w nauce APT3 o 2,95%, a angielski jest 1,68× droższy niż w GPT-4o. To znane
   i akceptowalne ograniczenie tokenizera „pod polski urzędowy”.
6. **Uchwały w teście to tylko pierwsza strona HTML.** Na pełnym PDF przewaga
   nad APT3 spada do **0,55%** (HF 0,82%) — poniżej progu 1%, który sami
   uznaliśmy za istotny. APT3 jest przy tym stratny: w 6 na 1010 dokumentów
   wraca do innego tekstu (dodaje znaki). To nie jest wygrana jakością.
7. **Morfologia (odmiana słów) jest słabsza niż w modelach bazowych.**
   MorphScore precision 0,023 vs Slayer 0,082 i Bielik 0,135. Ale literatura
   mówi, że to słabo przekłada się na jakość modelu (R² ≈ 0,02), więc nie
   panikujemy i nie optymalizujemy na ślepo.

## Nowy, ważny pomiar: ile kosztują pojedyncze cyfry

Jeśli naprawimy kalendarz przez rozbicie cyfr, dokumenty **wydłużą się**.
Szacunek na 7 dziedzinach urzędowych: **+6,7% (dolna granica) do +15,0%
(górna)**. Na pełnym ogłoszeniu przetargowym: mediana **3984 → 4646 tokenów
(+16,6%)**. To nie jest darmowe. Prawdziwy koszt zmierzymy po wytrenowaniu
nowego tokenizera w TKX-C; teraz mamy tylko widełki.
(`audit/results/digits_cost.json`)

## Kontekst modelu 150M

To decyzja o modelu, nie o tokenizerze:

* Pełne ogłoszenie przetargowe: mediana **3984** tokenów, p90 **7396**;
  w 2048 mieści się **1,7%**, w 4096 — **53%**.
* Pełna uchwała śląska (PDF): mediana **2403**; w 2048 mieści się **40%**,
  w 4096 — **72,5%**.
* Po rozbiciu cyfr mediana ogłoszenia rośnie do **4646** i wypada z 4096
  (w 4096 mieści się wtedy 33%).

Opcje: **2048 + dzielenie na kawałki** (taniej, ale gubi więź między kwotą
a warunkiem, jeśli wpadną do różnych okien) albo **4096** (mieści medianę
ogłoszenia, ale nie ogon i nie po rozbiciu cyfr). Ostateczna decyzja należy do
planu modelu.

## Co naprawić w pierwszej kolejności (decyzja właściciela 19.11)

**Baza, bez eksperymentów:**
1. **Pojedyncze cyfry** — ale kryterium sukcesu to **ten sam koszt 2024 i 2027**
   na zdaniu `w roku RRRR r. zadanie`, a nie spadek fertility (fertlity wręcz
   wzrośnie o 6–17%).
2. **NFC w potoku, nie w tokenizerze** — dla PDF-ów; z pomiarem NFD vs NFC
   i osobną ścieżką dla wersalików.
3. **Jeden kanoniczny enkoder** (HF) z testem `decode(encode(x)) == x` i
   zamrożonymi sekwencjami referencyjnymi.

**Potem:** warianty słownika **16k / 24k / 32k** oceniane na **małych modelach**
(BPB i sonda jakościowa), **nie przez fertility**. Przy `d_model` 768 słownik
32k to 24,6 mln parametrów embeddingu (16,4% modelu 150M), więc sam spadek
fertility nie rozstrzyga.

**Dopiero na końcu:** wielkie litery, filtr boilerplate'u, zakaz superwordów od
środka słowa, Picky BPE/BoundlessBPE, mieszanka danych.

## Czego nie robić

* Nie używać Rényiego do wyboru wariantu — to miara opisowa, a APT3 ma wyżej.
* Nie wybierać słownika przez samą fertility — rozbicie cyfr ją podniesie.
* Nie gonić „0 różnic ID HF” — ważny jest jeden enkoder i wierny round-trip,
  nie identyczne identyfikatory.
* Nie „naprawiać” angielskiego kosztem polskiego — ten tokenizer ma być polski.

## Samoocena vs rundy niezależne

`audit/REVIEW_R2.md` i `audit/RED_TEAM_R3.md` to **samoocena wykonawcy**.
Niezależne rundy zrobili osobno:
* **Codex** — gałąź `review/tkx-a-r2-codex` @ `47e9cb2`, raport
  `audit/independent/codex/REVIEW_CODEX_R2.md`, werdykt **PASS_Z_UWAGAMI**,
  12/12 liczb powtórzonych.
* **Grok** — gałąź `review/tkx-a-r3-grok` @ `686cbce`, raport
  `audit/independent/grok/RED_TEAM_GROK_R3.md`, werdykt: **zmienia 2, osłabia
  2, nie zmienia 3**.

Liczby z tych rund mają pierwszeństwo. To one wymusiły korektę Rényiego, dodanie
pomiaru cyfr, zastrzeżenie o pełnych PDF i sekcję o kontekście.

## Słowniczek

* **Token (kawałek)** — najmniejsza jednostka, na którą tokenizer dzieli tekst.
* **Fertility** — liczba tokenów na słowo; mniej = taniej i więcej tekstu
  w oknie kontekstu.
* **Superword** — token obejmujący kilka słów, np. ` w związku z`.
* **NDF/NFC** — dwa sposoby zapisu polskich liter w Unicode; NFD rozkłada
  `ą` na `a` + ogonek, NFC trzyma `ą` jako jeden znak.
* **CAPS** — tekst WIELKIMI LITERAMI.
* **Parytet HF** — czy eksport dla biblioteki Hugging Face tnie tekst tak samo
  jak nasz enkoder referencyjny (na poziomie identyfikatorów).
* **Round-trip** — czy `decode(encode(tekst))` daje z powrotem ten sam tekst.
* **Rényi** — miara wykorzystania słownika; wyżej = lepiej, ale **nie**
  przewiduje jakości modelu.
* **BPB** — bity na bajt; miara jakości modelu używana w TKX-C zamiast
  fertility.
* **CI (przedział ufności)** — widełki, w których z 95% pewnością jest
  prawdziwa liczba.
* **OCR** — automatyczne rozpoznawanie tekstu ze skanu; ma błędy, celowo
  uwzględnione w dziedzinie `ocr_prasa`.

## Jedno zdanie na koniec

TOKENIZATOREX jest **najlepszym tanim tokenizerem do polskiego urzędowego**,
ale przed treningiem modelu 150M trzeba naprawić **parytet/kanoniczny enkoder,
cyfry/lata i spójność zapisów**, a decyzję o oknie 2048 vs 4096 podjąć
świadomie — bo pełne ogłoszenie i tak nie mieści się w 2048.
