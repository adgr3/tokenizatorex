"""Testy spójności TKX-ZOO (tylko nowe pliki, bez danych właściciela)."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(REPO, "results")
ZOO = os.path.join(REPO, "tkx_zoo")


def load(rel):
    p = os.path.join(REPO, rel)
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def test_manifest_metadata():
    m = load("tkx_zoo/MANIFEST.json")
    assert m["branch"] == "feat/tkx-zoo"
    assert m["base_commit"].startswith("f12fc2c")
    assert m["seed"] == 20261123
    assert m["pythonhashseed"] == 0
    assert m["bootstrap"] == 1000


def test_manifest_only_tokenizer_files_and_hashes():
    if not os.path.isdir(os.path.join(ZOO, "hf")):
        pytest.skip("brak lokalnych plików tokenizerów — uruchom "
                    "tkx_zoo/pobierz_tokenizery.py")
    m = load("tkx_zoo/MANIFEST.json")
    recorded = checked = 0
    for label, entry in m.items():
        if not isinstance(entry, dict) or "files" not in entry:
            continue
        for f in entry["files"]:
            name = f["name"]
            assert name.startswith("tokenizer"), (label, name)
            assert "safetensors" not in name and "pytorch_model" not in name
            path = f.get("path")
            if not path:
                continue
            recorded += 1
            full = os.path.join(REPO, path.replace("/", os.sep))
            # pliki obcych tokenizatorów nie są w repo; odtwarza je
            # tkx_zoo/pobierz_tokenizery.py ( sprawdzenie SHA-256 tam )
            if not os.path.isfile(full):
                continue
            assert sha256(full) == f["sha256"], (label, name)
            checked += 1
    assert recorded >= 15


def test_no_third_party_tokenizer_files_tracked():
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=REPO).decode("utf-8").split("\0")
    tracked = [p for p in tracked if p]
    allowed = ("hf/", "tkx_v21/hf/")
    bad = []
    for p in tracked:
        name = os.path.basename(p)
        if name not in ("tokenizer.json", "tokenizer_config.json", "tokenizer.model"):
            continue
        if not p.startswith(allowed):
            bad.append(p)
    assert not bad, bad
    assert not any(p.startswith("tkx_zoo/hf/") for p in tracked)
    with open(os.path.join(ZOO, ".gitignore"), encoding="utf-8") as f:
        assert "hf/" in f.read()
    assert os.path.isfile(os.path.join(ZOO, "pobierz_tokenizery.py"))


def test_danielk_pr_commit_and_sha256():
    m = load("tkx_zoo/MANIFEST.json")
    t1 = m["DanielK-t1-pl-polish-32k"]
    t2 = m["DanielK-t2-pl-cnc-32k"]
    assert t1["revision"] == t2["revision"] == "0cf4eff0e622d23cd38a6c6d190dbba5f5e0fec8"
    assert "pull/29" in t1["repo"] and "pull/29" in t2["repo"]
    assert t1["files"][0]["source_path"] == "DanielK/artifacts/bpe2_t1_pl_polish_32k/tokenizer.json"
    assert t2["files"][0]["source_path"] == "DanielK/artifacts/bpe2_t2_pl_cnc_32k/tokenizer.json"
    assert t1["files"][0]["sha256"] == "d784f63a0d3f20660edd4e1eb2682ede6063b7e5698a17fdde3bac48daf0cda5"
    assert t2["files"][0]["sha256"] == "8bb98a27a0f1e019c13f5741bde5e7cbbad4a7be4178c428acffb07cd55ce4a1"


def test_gated_llama_base_is_marked_without_substitution():
    m = load("tkx_zoo/MANIFEST.json")
    e = m["Llama-3.1-8B"]
    assert e["status"] == "unavailable"
    assert "baza niedostępna (gated, czeka na zatwierdzenie Meta)" in e["note"]
    assert e["repo"] == "meta-llama/Llama-3.1-8B"
    assert e["files"] == []
    assert m["base_comparison"]["PLLuM-8B"]["status"] == e["note"]


def test_source_order_and_existing_reference_values():
    fert = load("results/tkx_zoo_fertility.json")
    v2 = load("results/tkx_v2_fertility.json")
    v21 = load("results/tkx_v21_dev.json")
    assert list(fert["sources"])[:8] == list(v2["sources"])
    v0 = fert["sources"]["1_bzp"]["tokenizers"]["V0-32k"]
    assert v0["fertility"] == v2["sources"]["1_bzp"]["tokenizers"]["TKX/V0-32k"]["fertility"]
    assert v0["origin"] == "existing:results/tkx_v2_fertility.json"
    j2 = fert["sources"]["1_bzp"]["tokenizers"]["V0J2-32k"]
    assert j2["fertility"] == v21["sources"]["bzp_ogloszenia"]["tokenizers"]["V0J2-32k"]["fertility"]
    assert j2["origin"] == "existing:results/tkx_v21_dev.json"


def test_method_parameters_and_ci():
    fert = load("results/tkx_zoo_fertility.json")
    assert fert["seed"] == 20261123 and fert["bootstrap"] == 1000
    assert fert["pythonhashseed"] == 0
    for s in fert["sources"].values():
        for row in s["tokenizers"].values():
            if row.get("origin") == "new":
                lo, hi = row["fertility_ci_lo"], row["fertility_ci_hi"]
                assert lo <= row["fertility"] + 1e-9
                assert hi + 1e-9 >= row["fertility"]


def test_vocab_cost_formula():
    c = load("results/tkx_zoo_vocab_cost.json")
    for label, r in c["vocab_x_dmodel"].items():
        for d in ("768", "1024"):
            row = r[d]
            assert row["params"] == r["vocab"] * int(d)
            assert abs(row["pct_150m"] - 100.0 * row["params"] / 150_000_000) < 1e-9
            assert abs(row["pct_150m_untied"] - 2 * row["pct_150m"]) < 1e-9


def test_formats_shape():
    fmt = load("results/tkx_zoo_formats.json")
    toks = [t for t in load("results/tkx_zoo_fertility.json")["tokenizers"]
            if t != "Llama-3.1-8B"]
    assert len(next(iter(fmt["date_formats"].values()))) == 12
    assert len(next(iter(fmt["amount_formats"].values()))) == 9
    assert len(next(iter(fmt["paragraph_forms"].values()))) == 9
    for t in toks:
        assert t in fmt["date_formats"] and t in fmt["amount_formats"]
        assert t in fmt["paragraph_forms"] and t in fmt["segmentation"]
        assert len(fmt["segmentation"][t]) == 3
        assert fmt["digit_split"][t]["style"]


def test_regression_split_all_tokenizers():
    reg = load("results/tkx_zoo_regression_split.json")
    assert reg["phrases"] == ["15 maja", "100 mln zł", "3 miesiące", "5 min"]
    toks = load("results/tkx_zoo_fertility.json")["tokenizers"]
    assert set(toks) - {"Llama-3.1-8B"} <= set(reg["tokenizers"])
    for t, row in reg["tokenizers"].items():
        for p in reg["phrases"]:
            v = row[p]
            assert v["n"] == len(v["tokens"])
            assert isinstance(v["same_as_v0"], bool)
    assert reg["tokenizers"]["V0-32k"]["15 maja"]["same_as_v0"]


def test_section_sign_and_roundtrip():
    sec = load("results/tkx_zoo_section_sign.json")
    rt = load("results/tkx_zoo_roundtrip.json")
    assert rt["cases"] == 700
    for t, row in sec["tokenizers"].items():
        assert row["one_token"] == (row["tokens"] == 1)
    for t, row in rt["tokenizers"].items():
        assert row["cases"] == 700 and isinstance(row["bad"], int)


def test_no_owner_raw_text_in_results():
    for name in os.listdir(RESULTS):
        if not name.startswith("tkx_zoo_") or not name.endswith(".json"):
            continue
        data = load(os.path.join("results", name))

        def keys(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    yield k
                    yield from keys(v)
            elif isinstance(obj, list):
                for v in obj:
                    yield from keys(v)

        assert "text" not in set(keys(data)), name
