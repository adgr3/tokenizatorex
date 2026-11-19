# TKX-D — plan małych modeli i pomiaru BPB (bez trenowania tutaj)

Data: 19.11.2026 · Wejście: warianty TKX-C (`tokenizers/variants/`,
`hf/variants/`) · Cel: wybrać tokenizer **na podstawie jakości modelu**, nie
fertility.

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
* **Metryki:**
  * **BPB** = `sum(NLL)/ln(2)/bajty UTF-8`, na tych samych bajtach walidacji;
  * **sonda:** daty, kwoty, CPV, skróty urzędowe (`Dz.U.`, `lit.`, `art.`),
    lata 2015–2035; dokładność/EM, nie tylko perplexity;
  * opcjonalnie: czas kroku, VRAM, przepustowość.
* **Kandydaci:** V0-32k, V2-16k, V2-24k, V2-32k, tokenizer Slayer1B (SHA-256
  `0640d3bd3674d7a6e59c540d945a2ad275a12e1bcaeb6007c37a90751f9815dd`).
  V0 jako kontrola „przed poprawkami”; V2-* jako poprawione.
* **Kryterium:** najniższy BPB na walidacji **i** nie gorsza sonda; różnica
  musi być większa niż szum między seedami (co najmniej 2 seedY albo bootstrap
  po dokumentach). Fertility i Rényi **nie** są kryterium wyboru.
* **Limit:** jeden przebieg ≤ 9 h, łącznie ≤ 10 h GPU; T4/P100 bez bf16 →
  fp32; zapisać kartę i wersje.

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
  i podmienić tokenizer na V0/V2-16/24/32; „32m” to nazwa recipe, nie liczba
  parametrów. Nie kopiujemy wag — tylko protokół i ewentualnie skrypt
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
* **Na T4/P100:** 1B w fp32 to ok. 4,4 GB — mieści się w 16 GB. **Nie używać
  bf16** (T4/P100 nie mają bf16); fp32, bez kwantyzacji. Zapisać kartę.
* **Mały test na jednym checkpoincie:** `wagi_60000.pt` (lub `wagi_50000.pt`),
  tokenizer Slayer1B, 200–500 dokumentów z dev TKX-A, kontekst 1024/2048;
  policzyć BPB i porównać z V2-32k po treningu TKX-D. Jeśli pamięć nie
  wystarczy — UNKNOWN z powodem, bez kwantyzacji.
* `hf_do_ckpt.py` w `Slayer1B-1.09` służy do konwersji **HF → ckpt trenera**
  (dla `--init-from`), a nie do odczytu `wagi_*.pt`; do ewaluacji używać
  `inspect_checkpoint.py`/`torch.load`.

## 5. Kroki TKX-D

1. Zamrozić protokół TKX-D (architektura, dane, seed, BPB, sondy, budżet
   parametrów, 2 seedy).
2. Zbudować packi treningowe w **bajtach** (nie tokenach), wspólne dla
   wszystkich tokenizerów; decontaminacja 13-gramów względem dev/test TKX-A.
3. Wytrenować 5 modeli (V0-32k, V2-16k, V2-24k, V2-32k, Slayer1B) na tym
   samym budżecie bajtów; zapisać BPB co 10k kroków.
4. Sonda dat/kwot/CPV/skrótów na dev; finalny BPB na teście TKX-A (raz).
5. Raport: tabela BPB + sonda + udział embeddingów + koszt; decyzja o
   tokenizerze i słowniku.
6. Ewentualnie powtórzyć zwycięzcę z drugim seedem; różnice < szum oznaczyć
   jako remis.

## 6. Ograniczenia

* Mały model 30M nie jest 150M; wybór tokenizera przenosimy ostrożnie.
* BPB zależy od danych walidacji; dev/test TKX-A to polszczyzna urzędowa +
  ogólna, nie cały świat.
* Slayer1B 1.09 to trening w toku; checkpointy mogą się zmieniać.
* T4/P100 bez bf16; fp32 jest wolniejszy i nie testuje docelowego bf16.
* Nie trenujemy modeli w TKX-C; ten plik to plan, nie wynik.
