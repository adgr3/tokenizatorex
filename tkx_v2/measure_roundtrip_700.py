"""Pomiar O1/O2 na 700 dokumentach (7 źródeł x 100, dopełnione do 700).

Wynik: results/tkx_v2_roundtrip.json. Nie zapisuje tekstów.
"""
from __future__ import annotations

import json
import os
import sys
import unicodedata
from pathlib import Path

from tokenizers import Tokenizer

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
REPO = Path(__file__).resolve().parents[1]
AUDIT_RAW = REPO / "audit" / "data" / "raw"
TKX_DANE = Path(os.environ.get("TKX_DANE", "data"))
SPEC1 = TKX_DANE / "spec1" / "test.jsonl"
POLISH = {
    "bzp_ogloszenia": "spec1",
    "du_eli": "prawo_eli",
    "kio": "przetargi_kio",
    "samorzad": "samorzad_uchwaly",
    "granty": "granty_ogloszenia",
    "json_bzp_tabele": "tabele_json",
    "general_web": "web",
}


def load_spec1():
    out = []
    with open(SPEC1, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                t = json.loads(line).get("text")
                if t:
                    out.append(t)
    return out


def load_audit(domain):
    d = AUDIT_RAW / domain
    out = []
    for name in sorted(os.listdir(d)):
        if not name.endswith(".json"):
            continue
        doc = json.load(open(d / name, encoding="utf-8"))
        if doc.get("split") != "test":
            continue
        out.append(doc["text"])
    return out


def load_polish():
    return {k: (load_spec1() if v == "spec1" else load_audit(v)) for k, v in POLISH.items()}


def local(name):
    return Tokenizer.from_file(str(REPO / "hf" / "variants" / name / "tokenizer.json"))


def slayer():
    from huggingface_hub import hf_hub_download
    p = hf_hub_download("SlayerLab/Slayer1B-1.08", "tokenizer.json", local_files_only=True)
    return Tokenizer.from_file(p)


def main():
    polish = load_polish()
    cases = []
    seen = set()
    for sname, docs in polish.items():
        for d in docs[:100]:
            cases.append((sname, d))
            seen.add(d)
    for sname, docs in polish.items():
        for d in docs:
            if len(cases) >= 700:
                break
            if d not in seen:
                cases.append((sname, d))
                seen.add(d)
    assert len(cases) == 700 and len(seen) == 700

    toks = {
        "V0-32k": local("V0-32k"),
        "V0J2-32k": local("V0J2-32k"),
        "V3-32k": local("V3-32k"),
        "Slayer1B-1.08": slayer(),
    }
    out = {"cases": len(cases), "unique_texts": len(seen), "tokenizers": {},
           "per_source": {}, "nfd_by_source": {}}
    for label, tok in toks.items():
        bad, bad_nfd = [], []
        per = {}
        for sname, text in cases:
            dec = tok.decode(tok.encode(text, add_special_tokens=False).ids)
            is_nfd = text != unicodedata.normalize("NFC", text)
            per.setdefault(sname, {"n": 0, "bad": 0, "nfd": 0})
            per[sname]["n"] += 1
            per[sname]["nfd"] += int(is_nfd)
            if dec != text:
                per[sname]["bad"] += 1
                item = {"source": sname, "chars": len(text), "nfd": is_nfd}
                bad.append(item)
                if is_nfd:
                    bad_nfd.append(item)
        out["tokenizers"][label] = {
            "cases": len(cases), "bad": len(bad), "bad_nfd": len(bad_nfd),
            "ok": len(bad) == 0, "examples_bad": bad[:8],
        }
        out["per_source"][label] = per
    for sname in POLISH:
        out["nfd_by_source"][sname] = sum(1 for s, t in cases
                                         if s == sname and t != unicodedata.normalize("NFC", t))
    all_bzp = load_spec1()
    out["bzp_full"] = {
        "docs": len(all_bzp),
        "nfd": sum(1 for t in all_bzp if t != unicodedata.normalize("NFC", t)),
    }
    with open(REPO / "results/tkx_v2_roundtrip.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps(out, ensure_ascii=False, indent=1)[:2000])


if __name__ == "__main__":
    main()
