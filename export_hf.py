"""
Eksport do formatu Hugging Face `tokenizer.json` + sprawdzenie zgodności z naszym enkoderem.

  python export_hf.py tokenizers/superbpe-32k-t24k.json --check ../data/heldout.txt

Baseline daje się odwzorować 1:1 (Split po fragmentach -> Split po słowach -> ByteLevel).
SuperBPE ma DWA poziomy pretokenizacji (merge'e etapu 1 tylko w słowach, etapu 2 w całym
fragmencie), a HF BPE stosuje wszystkie merge'e w jednym przebiegu wg rangi. Dlatego dla
SuperBPE eksport dzieli tylko na fragmenty i w rzadkich przypadkach (np. liczby >3 cyfr)
może wybrać inną segmentację. `--check` mierzy, jak często — wynik raportujemy uczciwie.
"""
import argparse
import os

from tokenizers import Regex, Tokenizer, decoders, models, pre_tokenizers

from superbpe import CHUNK_PATTERN, CHUNK_RE, WORD_PATTERN, SuperBPETokenizer


def bytes_to_unicode() -> dict[int, str]:
    """Mapowanie bajt -> drukowalny znak (to samo co GPT-2; spacja = 'Ġ')."""
    bs = list(range(ord("!"), ord("~") + 1)) + list(range(ord("¡"), ord("¬") + 1)) + list(range(ord("®"), ord("ÿ") + 1))
    cs = bs[:]
    n = 0
    for b in range(256):
        if b not in bs:
            bs.append(b)
            cs.append(256 + n)
            n += 1
    return dict(zip(bs, map(chr, cs)))


def to_hf(tok: SuperBPETokenizer) -> Tokenizer:
    b2u = bytes_to_unicode()
    s = lambda b: "".join(b2u[x] for x in b)  # noqa: E731
    vocab: dict[str, int] = {}
    for i, b in enumerate(tok.vocab):
        if s(b) in vocab:
            raise ValueError(f"zduplikowany token {b!r} (id {vocab[s(b)]} i {i}) — HF tego nie obsłuży")
        vocab[s(b)] = i
    merges = [(s(tok.vocab[a]), s(tok.vocab[b])) for a, b, _ in tok.stage1 + tok.stage2]

    hf = Tokenizer(models.BPE(vocab=vocab, merges=merges, ignore_merges=False))
    pre = [pre_tokenizers.Split(Regex(CHUNK_PATTERN), behavior="isolated")]
    if not tok.stage2:
        pre.append(pre_tokenizers.Split(Regex(WORD_PATTERN), behavior="isolated"))
    pre.append(pre_tokenizers.ByteLevel(add_prefix_space=False, use_regex=False))
    hf.pre_tokenizer = pre_tokenizers.Sequence(pre)
    hf.decoder = decoders.ByteLevel()
    for name, i in sorted(tok.specials.items(), key=lambda kv: kv[1]):
        hf.add_special_tokens([name])
        assert hf.token_to_id(name) == i
    return hf


def check(tok: SuperBPETokenizer, hf: Tokenizer, text: str) -> dict:
    chunks = CHUNK_RE.findall(text)
    same = 0
    ours_total = hf_total = 0
    for ch in chunks:
        a = tok.encode_ordinary(ch)
        b = hf.encode(ch, add_special_tokens=False).ids
        same += a == b
        ours_total += len(a)
        hf_total += len(b)
    full_rt = hf.decode(hf.encode(text, add_special_tokens=False).ids) == text
    return {"chunks": len(chunks), "identical_chunks": same / len(chunks),
            "tokens_ours": ours_total, "tokens_hf": hf_total, "hf_roundtrip": full_rt}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("tokenizer")
    ap.add_argument("--out-dir", default="hf")
    ap.add_argument("--check", help="plik tekstowy do porównania segmentacji")
    ap.add_argument("--check-mb", type=float, default=2)
    a = ap.parse_args()

    tok = SuperBPETokenizer.load(a.tokenizer)
    hf = to_hf(tok)
    name = os.path.splitext(os.path.basename(a.tokenizer))[0]
    out = os.path.join(a.out_dir, name)
    os.makedirs(out, exist_ok=True)
    hf.save(os.path.join(out, "tokenizer.json"))
    print(f"zapisano {out}/tokenizer.json")
    if a.check:
        with open(a.check, encoding="utf-8") as f:
            text = f.read(int(a.check_mb * 10**6))
        print(check(tok, hf, text))


if __name__ == "__main__":
    main()
