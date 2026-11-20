"""Przykłady kawałków dla V0/V2/V2b/V3 do tabel w raportach (kanoniczny HF)."""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from measure_lib import COMPARE4, load_hf  # noqa: E402

RES = os.path.join(ROOT, "tkx_c", "results")

EXAMPLES = [
    "w roku 2024 r.",
    "1 234 567,89 zł",
    "w|·roku·|2|0|2|4|·r.",
    "45233140-2",
    "Dz.U. z 2024 r. poz. 1320",
    "ZP.271.12.2026",
]


def pieces(tok, text: str) -> list[str]:
    ids = tok.encode(text, add_special_tokens=False).ids
    # POPRAWKA: dekoduj KAŻDY token osobno (ByteLevel id_to_token dawało
    # np. '·zÅĤ' zamiast '·zł'). Spacja byte-level jest wyświetlana jako '·'.
    return [tok.decode([i], skip_special_tokens=False).replace(" ", "·").replace("\n", "\\n")
            for i in ids]


def main() -> None:
    toks = {v: load_hf(v) for v in COMPARE4}
    out = {"meta": {"canonical": "HF export / variants", "note": "· = spacja"},
           "examples": {}}
    for text in EXAMPLES:
        out["examples"][text] = {v: pieces(toks[v], text) for v in COMPARE4}
    with open(os.path.join(RES, "examples.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
        f.write("\n")
    for text in EXAMPLES[:2]:
        print("\n" + repr(text))
        for v in COMPARE4:
            print(" ", v, "|".join(out["examples"][text][v]))


if __name__ == "__main__":
    main()
