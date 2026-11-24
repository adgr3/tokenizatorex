"""R6: tokeny specjalne w tekście użytkownika + kontrola tekstów pomiarowych.

Sprawdza w tokenizers 0.23.3:
* domyślne `encode` zamienia literalny `<|endoftext|>` na ID specjalne 31999,
* zalecany tryb `encode_special_tokens = True` rozbija go na zwykłe tokeny
  (round-trip bez zmian),
* `<tool_call>` / `</tool_call>` w V0J2 są zwykłymi tokenami słownika, nie ID
  specjalnymi,
* teksty pomiarowe (8 źródeł) nie zawierają literalnych nazw tokenów specjalnych.

Wynik: results/tkx_v2_r6_special_tokens.json
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import tokenizers
from tokenizers import Tokenizer

REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "results"
TKX_DANE = Path(os.environ.get("TKX_DANE", "data"))
SPEC1 = TKX_DANE / "spec1" / "test.jsonl"
TC1 = TKX_DANE / "tc1" / "test.jsonl"
AUDIT_RAW = REPO / "audit" / "data" / "raw"

NAMES = ["<|endoftext|>", "<tool_call>", "</tool_call>", '<tool_call>{"',
         '<tool_call>{"name":', "<|im_start|>", "<|im_end|>"]


def load_jsonl(path: Path):
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            o = json.loads(line)
            out.append(o.get("text") or json.dumps(o, ensure_ascii=False))
    return out


def load_audit(domain: str):
    out = []
    for p in sorted((AUDIT_RAW / domain).glob("*.json")):
        d = json.load(open(p, encoding="utf-8"))
        if d.get("split") == "test":
            out.append(d["text"])
    return out


def check_tokenizer(path: Path) -> dict:
    tok = Tokenizer.from_file(str(path))
    added = tok.get_added_tokens_decoder()
    special_ids = {i for i, t in added.items() if t.special}
    rows = {}
    for name in NAMES:
        default = tok.encode(name, add_special_tokens=False)
        tok.encode_special_tokens = True
        try:
            recommended = tok.encode(name, add_special_tokens=False)
            rec_decoded = tok.decode(recommended.ids, skip_special_tokens=False)
        finally:
            tok.encode_special_tokens = False
        rows[name] = {
            "default_ids": default.ids,
            "default_special": any(i in special_ids for i in default.ids),
            "recommended_ids": recommended.ids,
            "recommended_special": any(i in special_ids for i in recommended.ids),
            "recommended_roundtrip": rec_decoded == name,
        }
    return {
        "path": str(path.relative_to(REPO)).replace("\\", "/"),
        "added_special_ids": sorted(special_ids),
        "names": rows,
        "default_injects": rows["<|endoftext|>"]["default_special"],
        "recommended_no_special": not rows["<|endoftext|>"]["recommended_special"],
        "recommended_roundtrip": rows["<|endoftext|>"]["recommended_roundtrip"],
    }


def main() -> None:
    sources = {
        "1_bzp": load_jsonl(SPEC1),
        "2_du_eli": load_audit("prawo_eli"),
        "3_kio": load_audit("przetargi_kio"),
        "4_samorzad": load_audit("samorzad_uchwaly"),
        "5_granty": load_audit("granty_ogloszenia"),
        "6_json_narzedzia": load_jsonl(TC1),
        "7_ogolny": load_audit("web"),
        "json_bzp_tabele": load_audit("tabele_json"),
    }
    occurrences = {name: 0 for name in NAMES}
    docs_with = 0
    for docs in sources.values():
        for d in docs:
            hit = False
            for name in NAMES:
                c = d.count(name)
                occurrences[name] += c
                hit = hit or c > 0
            docs_with += int(hit)
    # `<tool_call>`/`</tool_call>` to zwykłe tokeny słownika V0J2, nie ID specjalne,
    # więc tryb zalecany nie zmienia ich tokenizacji. Zmieniają ją tylko nazwy
    # dodane jako special=True (np. <|endoftext|>).
    special_names = ["<|endoftext|>", "<|im_start|>", "<|im_end|>"]
    special_occ = sum(occurrences[n] for n in special_names
                      if n in occurrences)
    template_occ = sum(occurrences[n] for n in ("<tool_call>", "</tool_call>")
                       if n in occurrences)

    out = {
        "meta": {
            "script": "scripts/sprawdz_tokeny_specjalne_r6.py",
            "tokenizers_version": tokenizers.__version__,
            "names": NAMES,
            "recommended_tokenizers": "tokenizer.encode_special_tokens = True",
            "recommended_transformers": "tokenizer_config.json: split_special_tokens=true",
        },
        "tokenizers": {
            "V0-32k": check_tokenizer(REPO / "hf/variants/V0-32k/tokenizer.json"),
            "V0J2-32k": check_tokenizer(REPO / "hf/variants/V0J2-32k/tokenizer.json"),
            "release-HF": check_tokenizer(REPO / "hf/tokenizatorex-32k/tokenizer.json"),
        },
        "measurement_texts": {
            "docs": sum(len(v) for v in sources.values()),
            "docs_with_special_string": docs_with,
            "occurrences": occurrences,
            "total_occurrences": sum(occurrences.values()),
            "special_occurrences": special_occ,
            "template_token_occurrences": template_occ,
            "note": "<tool_call>/</tool_call> są zwykłymi tokenami słownika V0J2, "
                    "nie ID specjalnymi; tryb zalecany nie zmienia ich tokenizacji. "
                    "Napisów dodanych jako special=True (<|endoftext|> itd.) w tekstach "
                    "pomiarowych nie ma.",
            "fertility_unchanged": special_occ == 0,
        },
    }
    with open(RESULTS / "tkx_v2_r6_special_tokens.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps({"default_injects": out["tokenizers"]["V0-32k"]["default_injects"],
                      "recommended_no_special": out["tokenizers"]["V0-32k"]["recommended_no_special"],
                      "measurement": out["measurement_texts"]},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
