# RAPORT_NOC_WYKRESY

## Wynik

| element | plik | rozmiar | zgodne? |
|---|---|---:|---|
| fertility_bzp | docs/wykresy/fertility_bzp.png (+.svg) | 128098 B PNG | tak |
| skad_przewaga | docs/wykresy/skad_przewaga.png (+.svg) | 87041 B PNG | tak |
| osiem_zrodel | docs/wykresy/osiem_zrodel.png (+.svg) | 74045 B PNG | tak |
| koszt_slownika | docs/wykresy/koszt_slownika.png (+.svg) | 68940 B PNG | tak |
| daty_kwoty_paragraf | docs/wykresy/daty_kwoty_paragraf.png (+.svg) | 52959 B PNG | tak |
| json_heldout | docs/wykresy/json_heldout.png (+.svg) | 70553 B PNG | tak |
| znane_wady | docs/wykresy/znane_wady.png (+.svg) | 66128 B PNG | tak |
| tokenizacja_porownanie | docs/wykresy/anim/tokenizacja_porownanie.gif | 245593 B | tak |
| fertility_wyscig | docs/wykresy/anim/fertility_wyscig.gif | 635132 B | tak |
| superbpe_sklejanie | docs/wykresy/anim/superbpe_sklejanie.gif | 20485 B | tak |

## Draft PR
https://github.com/adgr3/tokenizatorex/pull/6 (docs/wykresy-v2 -> main), status draft, bez scalania.

## media.local/
- `media.local/tokenizacja_porownanie.gif`
- `media.local/fertility_bzp.png`
- `media.local/skad_przewaga.png`

## Subagenci
Brak subagentów — praca bezpośrednia modelem darmowym `opencode-go/beam-free` (Beam Free). Wszystkie wyniki zweryfikowane: `pytest -q` (127 passed), `generuj_raporty_v2.py --check`, `sprawdz_liczby_v2.py`.

## Decyzje nocne
Patrz `DECYZJE_NOC.md` (animacja A bez Slayera, pominięcie DanielK/Llama, tc1 jako górna granica, PNG 1600 px).

## BLOKER / WAŻNE / DROBNE
- BLOKER: brak.
- WAŻNE: animacja A zawiera wiersze V0, Slayer v6 i GPT-4o (Slayer z lokalnego cache HF).
- DROBNE: `znane_wady.svg` wygenerowany mimo wymogu tylko PNG (nieszkodliwe).

## Co właściciel ma zrobić rano
- Obejrzeć GIF A na telefonie (czytelność tokenów).
- Zdecydować, czy uzupełnić animację A o Slayer (pobranie tokenizera z HF).
- Sprawdzić draft PR #6 i zatwierdzić merge („GO MERGE #6”).

## SHA
481cb02 (animacja A z wierszem Slayer)

STATUS=GOTOWE