"""Wspólne narzędzia audytu TKX-A.

Uwaga na H9: katalog ``tokenizers/`` w katalogu repo przesłania pakiet
Hugging Face ``tokenizers``, gdy katalog repo jest na początku ``sys.path``.
Dlatego NAJPIERW importujemy pakiet HF (tutaj, przed dopisaniem repo do
``sys.path``), a repo dopisujemy przez ``sys.path.append`` (nie ``insert(0)``).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from dataclasses import dataclass

# --- H9: najpierw pakiet HF, potem repo -------------------------------------
from tokenizers import Tokenizer as HFTokenizer  # noqa: E402

AUDIT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(AUDIT_DIR)
if REPO_ROOT not in sys.path:
    sys.path.append(REPO_ROOT)  # NIE insert(0) — patrz H9

from superbpe import SuperBPETokenizer  # noqa: E402

DATA_DIR = os.path.join(AUDIT_DIR, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
BENCH_DIR = os.path.join(DATA_DIR, "bench")
CACHE_DIR = os.path.join(DATA_DIR, "cache")
RESULTS_DIR = os.path.join(AUDIT_DIR, "results")
TOK_DIR = os.path.join(DATA_DIR, "tokenizer_files")
MANIFEST_PATH = os.path.join(DATA_DIR, "MANIFEST.json")

SEED = 20261119
BOOTSTRAP_N = 1000
DEV_SHARE = 0.40


def ensure_dirs() -> None:
    for d in (DATA_DIR, RAW_DIR, BENCH_DIR, CACHE_DIR, RESULTS_DIR, TOK_DIR):
        os.makedirs(d, exist_ok=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def read_json(path: str):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str, obj) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")


# --- korpus -----------------------------------------------------------------

@dataclass
class Document:
    id: str
    domain: str
    url: str
    date: str
    text: str
    source: str = ""
    split: str = ""

    def to_dict(self) -> dict:
        return {"id": self.id, "domain": self.domain, "url": self.url,
                "date": self.date, "source": self.source, "split": self.split}


def clean_text(text: str) -> str:
    """Normalizacja białych znaków (BEZ zmiany znaków Unicode / bez NFC)."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [" ".join(line.split()) for line in text.split("\n")]
    text = "\n".join(lines)
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
    return text.strip()


def word_count(text: str) -> int:
    return len(text.split())


def is_nfd(text: str) -> bool:
    import unicodedata
    return unicodedata.normalize("NFC", text) != text


def save_document(doc: Document, raw_dir: str = RAW_DIR) -> None:
    d = os.path.join(raw_dir, doc.domain)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, doc.id.replace("/", "_").replace("\\", "_") + ".json")
    write_json(path, {
        "id": doc.id, "domain": doc.domain, "url": doc.url, "date": doc.date,
        "source": doc.source, "split": doc.split, "text": doc.text,
        "words": word_count(doc.text), "nfd": is_nfd(doc.text),
        "sha256": sha256_text(doc.text),
    })


def load_domain(domain: str, split: str | None = None) -> list[dict]:
    d = os.path.join(RAW_DIR, domain)
    docs = []
    if not os.path.isdir(d):
        return docs
    for name in sorted(os.listdir(d)):
        if not name.endswith(".json"):
            continue
        doc = read_json(os.path.join(d, name))
        if split is None or doc.get("split") == split:
            docs.append(doc)
    return docs


# --- tokenizery -------------------------------------------------------------

@dataclass
class Encoder:
    label: str
    group: str
    vocab: int
    encode: object
    note: str = ""
    kind: str = "hf"

    def ids(self, text: str) -> list[int]:
        return self.encode(text)


class SuperBPEEncoder:
    def __init__(self, tok: SuperBPETokenizer):
        self.tok = tok

    def __call__(self, text: str) -> list[int]:
        return self.tok.encode_ordinary(text)

    def decode(self, ids) -> str:
        return self.tok.decode(ids)


class HFEncoder:
    def __init__(self, tok: HFTokenizer):
        self.tok = tok

    def __call__(self, text: str) -> list[int]:
        return self.tok.encode(text, add_special_tokens=False).ids

    def decode(self, ids) -> str:
        return self.tok.decode(ids, skip_special_tokens=False)


def load_superbpe(rel_path: str) -> SuperBPETokenizer:
    return SuperBPETokenizer.load(os.path.join(REPO_ROOT, rel_path))


def load_hf_file(path: str) -> HFTokenizer:
    return HFTokenizer.from_file(path)


def load_hf_repo(repo: str, cache_dir: str = TOK_DIR) -> tuple[HFTokenizer, str]:
    """Pobiera tokenizer z HF i zapisuje kopię; zwraca (tokenizer, ścieżka)."""
    os.makedirs(cache_dir, exist_ok=True)
    path = os.path.join(cache_dir, repo.replace("/", "__") + ".json")
    if not os.path.exists(path):
        tok = HFTokenizer.from_pretrained(repo)
        tok.save(path)
    return HFTokenizer.from_file(path), path


def tiktoken_encoder(name: str):
    import tiktoken
    enc = tiktoken.get_encoding(name)

    class TK:
        n_vocab = enc.n_vocab

        def __call__(self, text: str) -> list[int]:
            return enc.encode(text, disallowed_special=())

        def decode(self, ids) -> str:
            return enc.decode(ids)

    return TK()


def tokenizer_specs() -> list[dict]:
    """Zestaw tokenizerów zadania (zawsze ten sam)."""
    return [
        {"label": "TOKENIZATOREX", "kind": "superbpe", "path": "tokenizers/tokenizatorex-32k.json",
         "group": "nasz", "note": "referencyjny enkoder superbpe.py"},
        {"label": "TOKENIZATOREX-HF", "kind": "hf_file", "path": "hf/tokenizatorex-32k/tokenizer.json",
         "group": "nasz", "note": "eksport HF (tego użyje model)"},
        {"label": "TOKENIZATOREX-base", "kind": "superbpe", "path": "tokenizers/tokenizatorex-base-32k.json",
         "group": "nasz", "note": "kontrola: ten sam trening bez SuperBPE"},
        {"label": "Slayer1B", "kind": "hf_repo", "repo": "SlayerLab/Slayer1B-1.08",
         "group": "polski", "note": "GoLLeM-v6; SHA-256 zgodny z kartą modelu"},
        {"label": "APT3-1B", "kind": "hf_repo", "repo": "Azurro/APT3-1B-Base",
         "group": "polski", "note": "stratny (NFKC itd.)"},
        {"label": "Pollock-2.0", "kind": "hf_repo", "repo": "SlayerLab/pollock-2.0-polishdynaword-150m",
         "group": "polski", "note": "SlayerLab"},
        {"label": "Bielik-v3", "kind": "hf_repo", "repo": "speakleash/Bielik-11B-v3.1-Instruct",
         "group": "polski", "note": "APT4 (gated, dostęp potwierdzony przez hf auth whoami)"},
        {"label": "PLLuM-12B", "kind": "hf_repo", "repo": "CYFRAGOVPL/PLLuM-12B-chat-2512",
         "group": "polski", "note": "tokenizer Mistral Nemo / Tekken"},
        {"label": "GPT-4o", "kind": "tiktoken", "name": "o200k_base",
         "group": "świat", "note": "o200k"},
    ]


def build_encoders(labels: list[str] | None = None) -> dict[str, Encoder]:
    out: dict[str, Encoder] = {}
    for spec in tokenizer_specs():
        if labels is not None and spec["label"] not in labels:
            continue
        kind = spec["kind"]
        if kind == "superbpe":
            tok = load_superbpe(spec["path"])
            enc = SuperBPEEncoder(tok)
            vocab = tok.vocab_size
        elif kind == "hf_file":
            tok = load_hf_file(os.path.join(REPO_ROOT, spec["path"]))
            enc = HFEncoder(tok)
            vocab = tok.get_vocab_size()
        elif kind == "hf_repo":
            tok, _ = load_hf_repo(spec["repo"])
            enc = HFEncoder(tok)
            vocab = tok.get_vocab_size()
        elif kind == "tiktoken":
            enc = tiktoken_encoder(spec["name"])
            vocab = enc.n_vocab
        else:  # pragma: no cover
            raise ValueError(kind)
        out[spec["label"]] = Encoder(spec["label"], spec["group"], vocab, enc, spec["note"], kind)
    return out


def tokenizer_manifest() -> list[dict]:
    """Manifest plików tokenizerów: ścieżka/plik + SHA-256 + źródło."""
    out = []
    for spec in tokenizer_specs():
        row = {"label": spec["label"], "group": spec["group"], "note": spec["note"], "kind": spec["kind"]}
        if spec["kind"] in ("superbpe", "hf_file"):
            p = os.path.join(REPO_ROOT, spec["path"])
            row.update({"file": spec["path"], "sha256": sha256_file(p)})
        elif spec["kind"] == "hf_repo":
            _, p = load_hf_repo(spec["repo"])
            row.update({"repo": spec["repo"], "file": os.path.relpath(p, AUDIT_DIR),
                        "sha256": sha256_file(p)})
        elif spec["kind"] == "tiktoken":
            row.update({"encoding": spec["name"]})
        out.append(row)
    return out


# --- statystyka -------------------------------------------------------------

def bootstrap_ci(values: list[float], n: int = BOOTSTRAP_N, seed: int = SEED,
                 alpha: float = 0.05) -> tuple[float, float, float]:
    """Średnia i 95% CI z bootstrapu (po dokumentach)."""
    import random
    if not values:
        return (float("nan"), float("nan"), float("nan"))
    rng = random.Random(seed)
    k = len(values)
    means = []
    for _ in range(n):
        s = 0.0
        for _ in range(k):
            s += values[rng.randrange(k)]
        means.append(s / k)
    means.sort()
    lo = means[int((alpha / 2) * n)]
    hi = means[min(n - 1, int((1 - alpha / 2) * n))]
    return sum(values) / k, lo, hi


def bootstrap_paired_ratio(num_a: list[float], num_b: list[float], denom: list[float],
                           n: int = BOOTSTRAP_N, seed: int = SEED,
                           alpha: float = 0.05) -> dict:
    """Bootstrap parowany: stosunek sum tokenów (A/B) przy tych samych dokumentach."""
    import random
    assert len(num_a) == len(num_b) == len(denom)
    rng = random.Random(seed)
    k = len(num_a)
    ratios = []
    for _ in range(n):
        ta = tb = dw = 0.0
        for _ in range(k):
            i = rng.randrange(k)
            ta += num_a[i]
            tb += num_b[i]
            dw += denom[i]
        if tb:
            ratios.append((ta - tb) / dw)  # różnica tokenów na słowo
    ratios.sort()
    lo = ratios[int((alpha / 2) * n)]
    hi = ratios[min(n - 1, int((1 - alpha / 2) * n))]
    obs = (sum(num_a) - sum(num_b)) / sum(denom) if sum(denom) else float("nan")
    return {"diff_per_word": obs, "ci_lo": lo, "ci_hi": hi,
            "significant": lo > 0 or hi < 0,
            "practical": abs(obs) >= 0.01 * (sum(num_b) / sum(denom)) if sum(denom) else False}


def percentile(values: list[float], q: float) -> float:
    if not values:
        return float("nan")
    vals = sorted(values)
    pos = (len(vals) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(vals) - 1)
    frac = pos - lo
    return vals[lo] * (1 - frac) + vals[hi] * frac
