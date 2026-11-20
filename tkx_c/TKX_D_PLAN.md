# TKX-D — plan małych modeli i pomiaru BPB (bez trenowania tutaj)

Data: 19.11.2026 · Aktualizacja: 20.11.2026 (decyzja właściciela: **TKX-D
realizujemy**, obliczenia na wynajętej RTX 5090) · Wejście: warianty TKX-C
(`tokenizers/variants/`, `hf/variants/`) · Cel: wybrać tokenizer i sposób cięcia
liczb **na podstawie jakości modelu**, nie fertility.

## 1. Protokół eksperymentu

* **Architektura:** mały model ~30M parametrów, ta sama architektura i ten sam
  seed dla każdego tokenizera; **ta sama liczba bajtów treningu** (nie tokenów).
  Wzór: `SlayerLab/TokenizerTest-32m-A/B` (patrz §3) — 38,9M, d_model 384,
  15 warstw, 6 głów, kontekst 1024, tied embeddings, Muon, seed 1337.
* **Budżet parametrów:** liczba parametrów **z embeddingami**; przy 16k/24k/32k
  i d_model 384 trzeba podać udział embeddingów i wyrównać liczbę parametrów
  nie-embeddingowych, żeby porównanie nie było „większy słownik = większy
  model”. Dla docelowego 150M (d_model 768) udział jest w
  `results/embeddings.json`: 8,2% / 12,3% / 16,4% (tied).
* **Dane:** to samo 12,4 GB? Dla TKX-D wystarczy kontrolowany podzbiór, np.
  2–4 mld bajtów z `SlayerLab/slayer-pl-8x3b` (pack-00/01 + shared/core,
  core_sa, legal, legal_sa), walidacja `pack-07` po decontaminacji 13-gramów.
  **Nie używać testu TKX-A do treningu**; dev TKX-A może być sondą, test tylko
  do finalnego BPB.
* **Zamrożenie kandydatów (przed wglądem w test TKX-A).** Zestaw kandydatów
  i rozmiary słownika zamrażamy przed jakimkolwiek wglądem w test TKX-A.
  Kolejność V3-32k < V2b-32k < V2-32k z `digits_cost_new.json` to **koszt
  tokenów na teście, nie ranking modelu**. Rozmiaru słownika **nie wybieramy**
  z `digits_cost_new.json` ani z żadnego kosztu tokenów na teście.
* **Metryki:**
  * **BPB** = `sum(NLL)/ln(2)/bajty UTF-8`, na tych samych bajtach: główny
    pomiar na **`dev` TKX-A** (dziedziny urzędowe i ogólne — osobno i łącznie),
    drugi pomiar na walidacji korpusu modelu (`pack-07`);
  * **sonda** na `dev`, **exact match napisu** (nie liczba tokenów!), trzy
    zadania: (1) rok poza oknem — kontrola 2018–2024, trzymane 2028–2035,
    pary `2024`/`2027` i `1999`/`2000` w zdaniu `w roku {Y} r.`; (2) ta sama
    kwota w dwóch zapisach (`1234567,89 zł` / `1 234 567,89 zł` oraz
    `1999` / `1 999`) → ta sama wartość; (3) grupa i klasa CPV — 50 kodów
    z `dev`, oczekiwane `452` i `4523` dla `45233140`;
  * opcjonalnie: czas kroku, VRAM, przepustowość.
* **Kandydaci — runda 1 (tylko 32k, ta sama liczba bajtów treningu):**
  V0-32k (kontrola „przed poprawkami”), V2-32k, V2b-32k, **V3-32k po naprawie**
  (jako „folia kompresji”, nie faworyt), tokenizer Slayera v6 (SHA-256
  `0640d3bd3674d7a6e59c540d945a2ad275a12e1bcaeb6007c37a90751f9815dd`).
* **Runda 2 (16k/24k)** tylko dla zwycięzcy rundy 1, jeśli BPB przy 32k
  nie rozstrzygnie — i nigdy na podstawie fertility ani kosztu z testu.
* **Odrzucone przed treningiem:** V3-16k (13,81% słownika to wymuszone grupy,
  7,03% martwych, 500/1000 gołych trójek bez użyć, 2210/16000 = 13,81%) i
  V3-24k (9,21% wymuszonych, te same 1016 martwych grup). Obie wersje zostały
  w repo z dopiskiem „odrzucony przed TKX-D”.
* **Post hoc:** V2b i V3 zaprojektowano po obejrzeniu V2 na teście; ich wynik
  na teście nie jest pomiarem z góry. Próbka treningu tokenizera to HPLT p2
  400 MB, **nie korpus modelu**. **Liczby V2b/V3 z testu nie służą do wyboru
  wariantu.**
* **Kryterium wyboru:** najniższy BPB na `dev` TKX-A (osobno i łącznie) + BPB
  na `pack-07` jako drugi pomiar + **nie gorsza sonda**; różnica musi być
  większa niż szum — co najmniej 2 seedy albo bootstrap po dokumentach `dev`.
  **Fertility, Rényi i koszt tokenów NIE są kryterium.** Test TKX-A idzie
  **raz, po wyborze**, i nie wraca do listy kandydatów.
* **Zastrzeżenie o skali:** wynik na modelach ~30M to **przesiew**, nie
  werdykt dla 150M — luka między schematami cyfr maleje ze skalą (Singh i
  Strouse 2024).
* **Budżet i precision:** **bf16 na RTX 5090**. Jeden przebieg ≤ 2 h, łącznie
  ≤ 10 h GPU, ale **twardy limit kosztu 5 USD** (stop i pytanie przy 4 USD).
  Zapisać kartę, wersje torch/CUDA i sumy SHA-256 wyników.

## 2. Co już wiadomo z TKX-C

* V1/V2 mają **stały** koszt lat (8 tokenów w szablonie 2015–2035) i 0
  tokenów wielocyfrowych; V0 ma schodki 4/5/6.
* Prawdziwy koszt cyfr: **+14,0%** na 7 dziedzinach urzędowych (V1 vs V0);
  na pełnym ogłoszeniu mediana 3883 → 4536 tokenów.
* NFC: V2 +0,0% przy NFD (V1 +39,9%, V0 +45,4%).
* Kanoniczny HF: round-trip 100% na 2752 dokumentach testu; zgodność z Pythonem
  99,975% dla V1/V2 (V0 97,08%).
* 16k/24k/32k: fertility rośnie w dół (V2-16k 2,168 vs V2-32k 1,920), ale to
  **nie** rozstrzyga; potrzebny BPB i budżet embeddingów.
* **V2b/V3 (post hoc, 20.11; V3 po naprawie):** koszt vs V0 na 7 dziedzinach
  urzędowych to +11,08% [10,32; 11,96] dla V2b i **+4,58% [4,15; 5,05]** dla
  V3 (przed naprawą +5,26%; V2: +13,99%); kalendarz płaski (V2b 8, V3 6
  tokenów); NFD 0%; round-trip 2752/2752. V3 ma **1,80%** martwych tokenów
  (przed: 4,88%). Przed naprawą enkoder HF nie realizował reguły grup
  (96/856 kodów CPV w kształcie 2+3+3, 505/1000 grup jednym tokenem);
  po naprawie jest to 100%. Na TED R3-extra V3 kosztuje +2,93% [2,69; 3,16],
  więc +4,58% nie jest stałą. Szczegóły w `results/digits_cost_new.json` i
  w recenzjach w `tkx_c/review_codex/`, `tkx_c/review_grok/`. To jedyna
  różnica między kandydatami zmierzona w TKX-C — resztę rozstrzyga TKX-D.

## 3. `SlayerLab/TokenizerTest-32m-A/B` — gotowy wzór

Sprawdzone na HF (publiczne, bez logowania):

* A: `SlayerLab/TokenizerTest-32m-A`, commit `4953c238`;
  tokenizer SHA-256 `60e23148…`.
* B: `SlayerLab/TokenizerTest-32m-B`, commit `92995f05`;
  tokenizer SHA-256 `77eeebed…`.
* Oba: 38,9M parametrów, tied embeddings, d_model 384, 15 warstw, 6 głów,
  kontekst 1024, Muon, seed 1337, **te same ~12,4 GB** polskiego tekstu
  (`SlayerLab/slayer-pl-8x3b` @ `d50df04a`).
* A = Fabryka AI BPE 32k; B = tokenizer stubbornGuy 32k. Wynik BPB:
  walidacja **1,0583 vs 1,0622** (B gorszy o +0,37%), held-out W
  **1,0781 vs 1,0883** (+0,94%). To jest **dokładnie** schemat TKX-D:
  porównywać BPB na tych samych bajtach, nie loss/token.
* Wniosek dla nas: można zaadaptować trainer/recipe (albo tylko protokół)
  i podmienić tokenizer na V0/V2/V2b/V3-32k (runda 1); „32m” to nazwa recipe,
  nie liczba parametrów. Nie kopiujemy wag — tylko protokół i ewentualnie skrypt
  treningowy z ich repo (licencja CC-BY-SA-4.0 dla modelu; sprawdzić przed
  użyciem kodu).

## 4. `SlayerLab/Slayer1B-1.09-checkpoints` — jak liczyć BPB

Sprawdzone na HF:

* Repo: `SlayerLab/Slayer1B-1.09-checkpoints`, commit `dc3b6a9b`;
  pliki `wagi_5000.pt` … `wagi_60000.pt` + pełny `ckpt_35000.pt`.
* To **natywne checkpointy trenera** (dict `{"model", "config", "step"}`),
  nie pakiet Transformers/safetensors. Trening w toku; start z wag 1.08,
  60k update'ów po 1 048 576 tokenów.
* Loader/instrukcja: `tutorials/inspect_checkpoint.py` w
  `SlayerLab/Slayer1B-1.09` (commit `58d8f359`), który ładuje
  `train_gpt_ref_r24_2.py` (SHA-256 `46f83b51…`), sprawdza tokenizer
  SHA-256 `0640d3bd…`, robi `torch.load(..., weights_only=True, mmap=True)`,
  `head.weight = tok.weight`, i liczy CE/BPB na bajtach.
* **Rola:** Slayer1B-1.09 z checkpointami to **punkt odniesienia BPB na tych
  samych tekstach co nasze małe modele** (reguła właściciela). Nie jest
  kandydatem do wyboru tokenizera — jest kotwicą porównawczą.
* **Na RTX 5090 (32 GB):** 1B w bf16 mieści się bez kwantyzacji. Wagi ładujemy
  `torch.load(..., weights_only=True, mmap=True)`, `head.weight = tok.weight`.
  (Na zapasowej karcie bez bf16 — np. T4/P100 — 1B w fp32 to ok. 4,4 GB i
  mieści się w 16 GB; wtedy fp32, bez kwantyzacji, z adnotacją w karcie.)
* **Mały test na jednym checkpoincie:** `wagi_60000.pt` (lub `wagi_50000.pt`),
  tokenizer Slayer1B, 200–500 dokumentów z dev TKX-A, kontekst 1024/2048;
  policzyć BPB na tych samych bajtach co V2/V2b/V3. Jeśli pamięć nie
  wystarczy — UNKNOWN z powodem, bez kwantyzacji.
* `hf_do_ckpt.py` w `Slayer1B-1.09` służy do konwersji **HF → ckpt trenera**
  (dla `--init-from`), a nie do odczytu `wagi_*.pt`; do ewaluacji używać
  `inspect_checkpoint.py`/`torch.load`.

## 5. Kolejność prac (PR #3 zostaje draftem)

1. **Najpierw na CPU, lokalnie (0 USD):** zamrozić protokół TKX-D (architektura,
   dane, seed, BPB, sondy, budżet parametrów z embeddingami, 2 seedy),
   zbudować packi treningowe w **bajtach** (nie tokenach), wspólne dla
   wszystkich tokenizerów, z decontaminacją 13-gramów względem dev/test TKX-A,
   przygotować skrypty treningowe i ewaluacyjne oraz gotowe komendy. Nic nie
   zaczynamy na karcie „na próbę”.
2. **Niezależne rundy 2 (Codex) i 3 (Grok)** na tym samym PR #3, jak w TKX-A →
   poprawki → dopiero `GO MERGE`. Push/PR zawsze po zgodzie właściciela.
3. **Wynajęcie karty:** agent **nie dostaje klucza API vast.ai**. Przygotowuje
   dla właściciela „kartkę do wynajmu”: `1× RTX 5090`, obraz **PyTorch z CUDA
   12.8+**, szacunek godzin i USD (przy ok. 0,43 USD/h), region i ustawienia.
   Właściciel wynajmuje i przekazuje SSH; agent loguje się tylko po SSH.
4. **Trening na karcie — runda 1 (32k):** modele ~30M dla V0-32k, V2-32k,
   V2b-32k, V3-32k po naprawie i tokenizer Slayera v6 — **ta sama liczba
   bajtów treningu**, ten sam seed, bf16, wyrównany budżet parametrów
   z embeddingami. BPB zapisywany co 10k kroków; BPB na `dev` TKX-A i `pack-07`
   oraz trzy sondy (rok, kwota, CPV — exact match) na `dev`; finalny BPB na
   teście TKX-A **raz, po wyborze**. Slayer1B-1.09 (checkpointy) jako punkt
   odniesienia BPB na tych samych tekstach. Runda 2 (16k/24k) tylko dla
   zwycięzcy, jeśli 32k nie rozstrzygnie.
5. **Koszt narastająco** w `results/koszt.jsonl` (czas, stawka, USD, kumulatywnie).
   Przy **4 USD stop i pytanie do właściciela**; twardy sufit 5 USD.
6. **Zakończenie:** pobranie wyników, sumy **SHA-256** każdego pliku, raport
   (tabela BPB + sonda + udział embeddingów + koszt w USD i w tokenach) i
   komunikat: **„GOTOWE, można kliknąć Destroy"**. **Destroy klika właściciel** —
   agent nigdy nie niszczy instancji sam. Zapas: Kaggle (karta laptopa się
   zawiesza).
7. **Krok końcowy (po wyborze):** zwycięski wariant **przetrenujemy na pełnych
   danych p0** później, na Kaggle (CPU, ok. 30 GB RAM) — małe modele TKX-D
   służą tylko do wyboru, nie są wynikiem końcowym. Wynik p0 zapisujemy jako
   nową bazę z jawnym SHA-256 i porównaniem z p2.

## 6. Ograniczenia

* Mały model 30M nie jest 150M; wybór tokenizera przenosimy ostrożnie.
* BPB zależy od danych walidacji; dev/test TKX-A to polszczyzna urzędowa +
  ogólna, nie cały świat.
* Slayer1B 1.09 to trening w toku; checkpointy mogą się zmieniać.
* V3 ma nieużyteczne (martwe) tokeny z wymuszonych grup (1,80% przy 32k po
  naprawie, 7,03% przy 16k) — BPB przy stałym budżecie parametrów może to
  „przepłacić”; dlatego V2/V2b/V3 porównujemy wyłącznie na modelach.
  V3-16k/24k wykluczono przed startem karty.
* Wynik na ~30M to przesiew, nie werdykt dla 150M; próbka tokenizera to HPLT
  p2 400 MB, nie korpus modelu.
* Budżet 5 USD ogranicza liczbę przebiegów; priorytet: 2 seedy zwycięzcy
  i kotwica Slayer1B przed dodatkowymi rozmiarami słownika.
* Nie trenujemy modeli w TKX-C; ten plik to plan, nie wynik. Agent nie ma
  klucza vast.ai i nie klika Destroy.
