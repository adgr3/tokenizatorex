"""
Niezalezna powtorka TKX-C (Codex, runda 2) -- CZESC A.
Liczby liczone wlasnym kodem, bez czytania results/raportow wykonawcy.

Zasady:
- HF tokenizers importowany PRZED ewentualnym sys.path.append (pulapka 6).
- Tokenizer = eksport HF hf/variants/*/tokenizer.json (kanoniczny).
- test/dev wg audit/data/MANIFEST.json, teksty surowe audit/data/raw/.
- bootstrap 1000x, seed 20261119, jeden generator NumPy.
- tekst po NFC dla wariantow V2+ (w praktyce porownujemy zawsze NFC(all)).
"""
import tokenizers as hf_tok  # HF pierwszy (pulapka: lokalny katalog tokenizers/)
from tokenizers import Tokenizer

import collections
import hashlib
import json
import string
import os
import pathlib
import re
import statistics
import sys
import unicodedata

import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[2]
RAW = REPO / "audit" / "data" / "raw"
HF = REPO / "hf" / "variants"

VARIANTS = [
    "V0-32k", "V1-32k", "V2-32k", "V2-24k", "V2-16k",
    "V2-base-32k", "V2-base-24k", "V2-base-16k",
    "V2b-32k", "V2b-24k", "V2b-16k",
    "V3-32k", "V3-24k", "V3-16k",
]
MAIN = ["V0-32k", "V2-32k", "V2b-32k", "V3-32k"]
SEED = 20261119
NBOOT = 1000
OFFICIAL_A = ["granty_ogloszenia", "prawo", "prawo_eli", "przetargi_kio",
              "przetargi_ogloszenia", "samorzad_uchwaly", "tabele_json"]
OFFICIAL_B = ["granty_ogloszenia", "prawo_eli", "przetargi_kio",
              "przetargi_ogloszenia", "samorzad_uchwaly", "tabele_json", "sejm"]
# zbior odtworzony niezaleznie: jako jedyny reprodukuje wszystkie trzy liczby
# wykonawcy (13,99 / 11,08 / 5,26) metoda stosunku sum tokenow
OFFICIAL_C = ["granty_ogloszenia", "ocr_prasa", "prawo_eli", "przetargi_kio",
              "przetargi_ogloszenia", "samorzad_uchwaly", "tabele_json"]

rng = np.random.default_rng(SEED)


def nfc(s):
    return unicodedata.normalize("NFC", s)


def load_docs():
    manifest = json.loads((REPO / "audit" / "data" / "MANIFEST.json").read_text(encoding="utf-8"))
    docs = {}
    for f in RAW.rglob("*.json"):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if "text" in d and "split" in d:
            docs[d["id"]] = d
    by_split = {"test": [], "dev": []}
    for rec in manifest["documents"]:
        d = docs.get(rec["id"])
        if d is None:
            continue
        d = dict(d)
        d["text_nfc"] = nfc(d["text"])
        assert d["split"] == rec["split"], (d["id"], d["split"], rec["split"])
        by_split[d["split"]].append(d)
    return manifest, by_split


def boot_ci_point(vals_a, vals_b, statistic="ratio_pct"):
    """Bootstrap po dokumentach; vals_a/b sa rownoleglymi listami (per doc)."""
    a = np.asarray(vals_a, dtype=np.float64)
    b = np.asarray(vals_b, dtype=np.float64)
    assert len(a) == len(b) and len(a) > 0

    def stat(idx):
        sa, sb = a[idx].sum(), b[idx].sum()
        if statistic == "ratio_pct":
            return 100.0 * (sa - sb) / sb if sb else float("nan")
        return float("nan")

    point = stat(np.arange(len(a)))
    n = len(a)
    boots = np.empty(NBOOT, dtype=np.float64)
    for i in range(NBOOT):
        boots[i] = stat(rng.integers(0, n, size=n))
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {"point": round(float(point), 4), "ci95": [round(float(lo), 4), round(float(hi), 4)]}


def boot_ci_delta(vals_new, vals_base):
    """Wzrost liczby tokenow po NFD, % (nowy vs baza), bootstrap."""
    return boot_ci_point(vals_new, vals_base, "ratio_pct")


def main():
    manifest, by_split = load_docs()
    test, dev = by_split["test"], by_split["dev"]
    print(f"docs: test={len(test)} dev={len(dev)}", flush=True)
    domains = sorted(manifest["domains"].keys())

    # ---------- A1: rozmiary slownikow ----------
    A1 = {}
    for v in VARIANTS:
        d = json.loads((HF / v / "tokenizer.json").read_text(encoding="utf-8"))
        vocab = d["model"]["vocab"]
        added = d.get("added_tokens", [])
        expected = int(re.search(r"(\d+)k$", v).group(1)) * 1000
        forced = {
            "2digit_00_99": sum(f"{i:02d}" in vocab for i in range(100)),
            "3digit_000_999": sum(f"{i:03d}" in vocab for i in range(1000)),
            "space_2digit": sum("Ġ" + f"{i:02d}" in vocab for i in range(100)),
            "space_3digit": sum("Ġ" + f"{i:03d}" in vocab for i in range(1000)),
            "space_1digit": sum("Ġ" + str(i) in vocab for i in range(10)),
        }
        A1[v] = {
            "vocab_model": len(vocab), "added_tokens": len(added),
            "total": len(vocab) + len(added), "expected": expected,
            "matches": len(vocab) + len(added) == expected,
            "normalizer": (d.get("normalizer") or {}).get("type"),
            "forced": forced,
        }
    print("A1 done", flush=True)

    # ---------- ladowanie tokenizerow + kodowanie ----------
    toks = {v: Tokenizer.from_file(str(HF / v / "tokenizer.json")) for v in VARIANTS}
    print("tokenizers loaded", flush=True)

    # per-doc token counts (dla kazdego wariantu) na test i dev
    counts_test = {v: [] for v in VARIANTS}
    counts_dev = {v: [] for v in VARIANTS}
    used_test = {v: set() for v in VARIANTS}
    used_dev = {v: set() for v in VARIANTS}
    roundtrip = {v: {"ok": 0, "total": 0, "len_ok": 0, "bad": []} for v in VARIANTS}
    nfd_counts = {v: {"nfc": [], "nfd": []} for v in MAIN}

    for i, doc in enumerate(test):
        t_nfd = unicodedata.normalize("NFD", doc["text_nfc"])
        for v in VARIANTS:
            # PROTOKOL: NFC w potoku tylko dla V2+; V0/V1 dostaja surowy tekst.
            t = doc["text"] if v in ("V0-32k", "V1-32k") else doc["text_nfc"]
            enc = toks[v].encode(t, add_special_tokens=False)
            counts_test[v].append(len(enc.ids))
            used_test[v].update(enc.ids)
            dec = toks[v].decode(enc.ids, skip_special_tokens=False)
            roundtrip[v]["total"] += 1
            if dec == t:
                roundtrip[v]["ok"] += 1
            # suma dlugosci kawalkow (bajty po dekodowaniu kazdego tokenu)
            # ByteLevel: dlugosc napisu tokenu (w symbolach alfabetu bajtowego)
            # = liczba bajtow tego kawalka; porownujemy z dlugoscia UTF-8 tekstu.
            pieces_len = sum(len(p) for p in enc.tokens)
            if pieces_len == len(t.encode("utf-8")):
                roundtrip[v]["len_ok"] += 1
            elif len(roundtrip[v]["bad"]) < 3:
                roundtrip[v]["bad"].append(doc["id"])
            if v in MAIN:
                # A6 mierzy NFD wzgledem tekstu po NFC (tak jak protokol/nfd.json)
                nfd_counts[v]["nfc"].append(len(toks[v].encode(doc["text_nfc"], add_special_tokens=False).ids))
                nfd_counts[v]["nfd"].append(len(toks[v].encode(t_nfd, add_special_tokens=False).ids))
        if (i + 1) % 500 == 0:
            print(f"  test {i+1}/{len(test)}", flush=True)

    for i, doc in enumerate(dev):
        for v in MAIN:
            t = doc["text"] if v in ("V0-32k", "V1-32k") else doc["text_nfc"]
            enc = toks[v].encode(t, add_special_tokens=False)
            counts_dev[v].append(len(enc.ids))
            used_dev[v].update(enc.ids)
        if (i + 1) % 500 == 0:
            print(f"  dev {i+1}/{len(dev)}", flush=True)
    print("encoding done", flush=True)

    # ---------- A3: prawdziwy koszt vs V0 ----------
    base = np.asarray(counts_test["V0-32k"], dtype=np.float64)
    A3 = {"per_domain": {}, "official_A": {}, "official_B": {}, "official_C": {}, "all15": {}}
    for v in ["V2-32k", "V2b-32k", "V3-32k"]:
        cur = np.asarray(counts_test[v], dtype=np.float64)
        A3["per_domain"][v] = {}
        for dom in domains:
            idx = [i for i, d in enumerate(test) if d["domain"] == dom]
            A3["per_domain"][v][dom] = boot_ci_point(cur[idx], base[idx])
        for name, domset in [("official_A", OFFICIAL_A), ("official_B", OFFICIAL_B),
                             ("official_C", OFFICIAL_C)]:
            idx = [i for i, d in enumerate(test) if d["domain"] in domset]
            A3[name][v] = boot_ci_point(cur[idx], base[idx])
        idx = list(range(len(test)))
        A3["all15"][v] = boot_ci_point(cur[idx], base[idx])
    print("A3 done", flush=True)

    # ---------- A4: kalendarz ----------
    A4 = {}
    for v in ["V0-32k", "V1-32k", "V2-32k", "V2b-32k", "V3-32k", "V2-base-32k"]:
        t = toks[v]
        tmpl = {}
        year = {}
        for y in range(2015, 2036):
            s = f"w roku {y} r. zadanie"
            tmpl[str(y)] = len(t.encode(s, add_special_tokens=False).ids)
            year[str(y)] = len(t.encode(str(y), add_special_tokens=False).ids)
        A4[v] = {"template": tmpl, "year_only": year,
                 "template_constant": len(set(tmpl.values())) == 1,
                 "year_constant": len(set(year.values())) == 1}
    print("A4 done", flush=True)

    # ---------- A2: reguly cyfr ----------
    A2 = {}
    for v in ["V1-32k", "V2-32k", "V2b-32k"]:
        d = json.loads((HF / v / "tokenizer.json").read_text(encoding="utf-8"))
        vocab = d["model"]["vocab"]
        digits = "0123456789"
        letters = string.ascii_letters
        two_plus = [t for t in vocab if sum(c in digits for c in t) >= 2]
        # 'Ġ' to symbol spacji w alfabetach ByteLevel, nie litara
        digit_letter = [t for t in vocab if any(c in digits for c in t) and any(c in letters for c in t)]
        A2[v] = {"tokens_ge2_digits": len(two_plus), "tokens_digit_and_letter": len(digit_letter),
                 "examples_digit_letter": digit_letter[:10]}
    # V2b: spacja przed cyfra, superwordy z koncowa spacja przed cyfra w tekscie, ·roku·
    v = "V2b-32k"
    d = json.loads((HF / v / "tokenizer.json").read_text(encoding="utf-8"))
    vocab = d["model"]["vocab"]
    space_digits = {"Ġ" + str(i): ("Ġ" + str(i) in vocab) for i in range(10)}
    # tokeny z koncowa spacja (ByteLevel: koncowa spacja to zwykly znak ' ' w tokenie? sprawdzamy oba)
    vocab_space_end = [t for t in vocab if t.endswith(" ")]
    vocab_space_end_sample = vocab_space_end[:20]
    # w kodowaniu test: czy jakikolwiek token konczacy sie spacja jest nastepnikiem tokenu zaczynajacego sie cyfra
    bad_space_before_digit = 0
    examples = []
    roku_key = "ĠrokuĠ"
    roku_count = 0
    for doc in test:
        enc = toks[v].encode(doc["text_nfc"], add_special_tokens=False)
        ts = enc.tokens
        roku_count += sum(1 for t in ts if t == roku_key)
        for j in range(len(ts) - 1):
            if ts[j].endswith(" ") and ts[j + 1][:1].isdigit():
                bad_space_before_digit += 1
                if len(examples) < 5:
                    examples.append((ts[j], ts[j + 1]))
    A2[v].update({
        "space_digit_tokens_exist": space_digits,
        "all_space_digit_exist": all(space_digits.values()),
        "vocab_tokens_ending_space": len(vocab_space_end),
        "vocab_tokens_ending_space_sample": vocab_space_end_sample,
        "bad_space_before_digit_in_test": bad_space_before_digit,
        "bad_examples": examples,
        "roku_in_vocab": roku_key in vocab,
        "roku_count_in_test": roku_count,
    })
    for vv, key in [("V0-32k", "roku"), ("V2-32k", "roku"), ("V3-32k", "roku")]:
        dv = json.loads((HF / vv / "tokenizer.json").read_text(encoding="utf-8"))
        A2.setdefault(vv, {})["roku_token_variants"] = [t for t in dv["model"]["vocab"] if "roku" in t][:10]
    print("A2 done", flush=True)

    # ---------- A2 tabela kawalkow ----------
    EXAMPLES = [
        "2024", "2027", "45233140-2", "1 234 567,89", "0,125", "00-950",
        "ZP.271.12.2026", "20.11.2026", "Dz.U. z 2024 r. poz. 1320",
        "art. 275 pkt 1", "0012", "123456789012345", "COVID-19", "A4", "H2O",
    ]
    A2_PIECES = {}
    for s in EXAMPLES:
        A2_PIECES[s] = {}
        for v in MAIN:
            enc = toks[v].encode(s, add_special_tokens=False)
            A2_PIECES[s][v] = {"n": len(enc.ids), "pieces": enc.tokens}
    print("A2 pieces done", flush=True)

    # ---------- A6: NFD ----------
    A6 = {}
    for v in MAIN:
        idx_all = list(range(len(test)))
        A6[v] = {
            "all_test": boot_ci_delta(nfd_counts[v]["nfd"], nfd_counts[v]["nfc"]),
        }
        for name, domset in [("official_A", OFFICIAL_A), ("official_B", OFFICIAL_B),
                             ("official_C", OFFICIAL_C)]:
            idx = [i for i, d in enumerate(test) if d["domain"] in domset]
            A6[v][name] = boot_ci_delta(
                [nfd_counts[v]["nfd"][i] for i in idx],
                [nfd_counts[v]["nfc"][i] for i in idx],
            )
    print("A6 done", flush=True)

    # ---------- A7: round-trip ----------
    A7 = {}
    for v in VARIANTS:
        r = roundtrip[v]
        A7[v] = {
            "ok": r["ok"], "total": r["total"], "pct": round(100.0 * r["ok"] / r["total"], 4),
            "len_ok": r["len_ok"], "len_pct": round(100.0 * r["len_ok"] / r["total"], 4),
            "bad_examples": r["bad"],
        }
    print("A7 done", flush=True)

    # ---------- A8: martwe tokeny ----------
    A8 = {}
    for v in MAIN:
        total = A1[v]["total"]
        dt = total - len(used_test[v])
        dd = total - len(used_dev[v])
        forced_dead = 0
        forced_total = 0
        d = json.loads((HF / v / "tokenizer.json").read_text(encoding="utf-8"))
        id2tok = {i: t for t, i in d["model"]["vocab"].items()}
        forced_ids = set()
        for tid, tk in id2tok.items():
            core = tk[1:] if tk.startswith("Ġ") else tk
            if re.fullmatch(r"\d{2,3}", core) or tk in ("Ġ" + str(i) for i in range(10)):
                forced_ids.add(tid)
        forced_total = len(forced_ids)
        forced_dead = len(forced_ids - used_test[v])
        A8[v] = {
            "vocab_total": total, "used_test": len(used_test[v]), "dead_test": dt,
            "dead_test_pct": round(100.0 * dt / total, 4),
            "used_dev": len(used_dev[v]), "dead_dev": dd,
            "dead_dev_pct": round(100.0 * dd / total, 4),
            "forced_group_tokens": forced_total, "forced_group_dead_test": forced_dead,
        }
    # wszystkie rozmiary
    for v in VARIANTS:
        if v in A8:
            continue
        txts = [d["text"] if v in ("V0-32k", "V1-32k") else d["text_nfc"] for d in test]
        encs = toks[v].encode_batch(txts, add_special_tokens=False)
        used = set()
        for e in encs:
            used.update(e.ids)
        total = A1[v]["total"]
        A8[v] = {"vocab_total": total, "used_test": len(used), "dead_test": total - len(used),
                 "dead_test_pct": round(100.0 * (total - len(used)) / total, 4),
                 "used_dev": None, "dead_dev": None, "dead_dev_pct": None,
                 "forced_group_tokens": None, "forced_group_dead_test": None}
        # dev dla nie-main
        txts_d = [d["text"] if v in ("V0-32k", "V1-32k") else d["text_nfc"] for d in dev]
        encs_d = toks[v].encode_batch(txts_d, add_special_tokens=False)
        usedd = set()
        for e in encs_d:
            usedd.update(e.ids)
        A8[v]["used_dev"] = len(usedd)
        A8[v]["dead_dev"] = total - len(usedd)
        A8[v]["dead_dev_pct"] = round(100.0 * (total - len(usedd)) / total, 4)
    print("A8 done", flush=True)

    # ---------- A9: dlugosci dokumentow (pelne) ----------
    full = json.loads((REPO / "tkx_c" / "data" / "full_docs.json").read_text(encoding="utf-8"))
    A9 = {"note": full.get("note"), "by_domain": {}}
    full_by_dom = collections.defaultdict(list)
    for d in full["documents"]:
        full_by_dom[d["domain"]].append(d["text"])
    for dom, texts in sorted(full_by_dom.items()):
        A9["by_domain"][dom] = {}
        for v in MAIN:
            encs = toks[v].encode_batch([nfc(t) for t in texts], add_special_tokens=False)
            lens = [len(e.ids) for e in encs]
            A9["by_domain"][dom][v] = {
                "n_docs": len(lens),
                "median": float(statistics.median(lens)),
                "p90": float(np.percentile(lens, 90)),
                "pct_le_2048": round(100.0 * sum(x <= 2048 for x in lens) / len(lens), 3),
                "pct_le_4096": round(100.0 * sum(x <= 4096 for x in lens) / len(lens), 3),
            }
    print("A9 done", flush=True)

    # ---------- A5: spójność zapisów ----------
    PATTERNS = {
        "kwoty": re.compile(r"\b\d+[.,]\d{2}\b"),
        "daty": re.compile(r"\b\d{1,2}[.\-]\d{1,2}[.\-]\d{4}\b|\b\d{4}-\d{2}-\d{2}\b"),
        "dz_u": re.compile(r"Dz\.U\.\s*z\s*\d{4}\s*r\.\s*poz\.\s*\d+", re.I),
        "cpv": re.compile(r"\b\d{8}-\d\b"),
        "znaki_sprawy": re.compile(r"\b[A-Z]{2,4}[./\s]*\d{1,6}[./][\d./]{2,20}\b"),
        "przepisy": re.compile(r"\bart\.\s*\d{1,4}(?:\s*pkt\s*\d{1,3})?", re.I),
    }
    A5 = {}
    for name, rx in PATTERNS.items():
        A5[name] = {}
        for v in MAIN:
            t = toks[v]
            counter = collections.Counter()      # dokladna sekwencja kawalkow
            len_counter = collections.Counter()  # liczba kawalkow (podzial)
            for doc in test:
                text = doc["text_nfc"]
                for m in rx.finditer(text):
                    enc = t.encode(m.group(0), add_special_tokens=False)
                    counter[tuple(enc.tokens)] += 1
                    len_counter[len(enc.ids)] += 1
            if counter:
                total = sum(counter.values())
                most_common_n = counter.most_common(1)[0][1]
                tot_len = sum(len_counter.values())
                top_len_n = len_counter.most_common(1)[0][1]
                A5[name][v] = {
                    "n_occurrences": total,
                    "pct_other_splits": round(100.0 * (total - most_common_n) / total, 4),
                    "most_common_pattern": list(counter.most_common(1)[0][0]),
                    "most_common_share": round(100.0 * most_common_n / total, 4),
                    "pct_other_piece_counts": round(100.0 * (tot_len - top_len_n) / tot_len, 4),
                    "most_common_piece_count": len_counter.most_common(1)[0][0],
                    "piece_count_hist": {str(k): vv for k, vv in sorted(len_counter.items())},
                }
            else:
                A5[name][v] = {"n_occurrences": 0, "pct_other_splits": None}
    print("A5 done", flush=True)

    # ---------- A10: te same dane treningowe ----------
    train_file = REPO / "audit" / "tmp" / "stability_train.txt"
    A10 = {
        "training_file": str(train_file.relative_to(REPO)),
        "sha256": hashlib.sha256(train_file.read_bytes()).hexdigest(),
        "bytes": train_file.stat().st_size,
        "protocol_statement": "wszystkie warianty (V0-V3) trenowane na tej samej probce p2 "
                              "(audit/tmp/stability_train.txt), seed 42 / train.py; "
                              "V2b i V3 dodane 20.11 na tej samej probce (PROTOKOL §9.1, §9.7)",
        "variant_configs": {},
    }
    for v in VARIANTS:
        cfg = json.loads((REPO / "tokenizers" / "variants" / v / "superbpe.json").read_text(encoding="utf-8"))
        A10["variant_configs"][v] = {k: cfg.get(k) for k in ("seed", "data", "train_file", "vocab_size",
                                                             "stage2_tokens", "normalize", "space_first",
                                                             "groups3", "digits") if k in cfg}
        if not A10["variant_configs"][v]:
            A10["variant_configs"][v] = list(cfg.keys())
    print("A10 done", flush=True)

    out = {
        "meta": {
            "seed": SEED, "nboot": NBOOT, "tokenizers_version": hf_tok.__version__,
            "numpy_version": np.__version__, "head": "d3a004e",
            "split_counts": {"test": len(test), "dev": len(dev)},
            "official_sets": {"A": OFFICIAL_A, "B": OFFICIAL_B, "C": OFFICIAL_C},
        },
        "A1_vocab": A1,
        "A2_digit_rules": A2,
        "A2_pieces": A2_PIECES,
        "A3_true_cost": A3,
        "A4_calendar": A4,
        "A5_consistency": A5,
        "A6_nfd": A6,
        "A7_roundtrip": A7,
        "A8_dead_tokens": A8,
        "A9_doc_lengths": A9,
        "A10_training_data": A10,
    }
    dest = REPO / "tkx_c" / "review_codex" / "results_codex.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("WROTE", dest, flush=True)
    # skrot do pozniejszego porownania
    print("SHA256 results:", hashlib.sha256(dest.read_bytes()).hexdigest(), flush=True)


if __name__ == "__main__":
    main()
