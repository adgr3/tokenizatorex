"""Testy poprawności: python -m pytest -q"""
from collections import Counter

import pytest

from superbpe import (
    SuperBPETokenizer, bpe_train_loop, chunks, merge_by_rank, merge_seq, pretokens,
    CHUNK_RE, WORD_RE, _WORDCOUNT_RE,
)

CORPUS = (
    "Zgodnie z art. 5 ustawy, na podstawie decyzji. W ramach projektu zrobiliśmy dużo.\n"
    "Na podstawie umowy w ramach programu. Zgodnie z planem, w ramach budżetu!\n"
    "Ala ma kota, a kot ma Alę. Dom, domu, domowi, domem, domach.\n"
) * 30 + "Rok 2026: 12345 zł; e-mail? Tak…\n"

WEIRD = "Zażółć gęślą jaźń 🤖  漢字\r\n\ttab  dwie  spacje...?! 3.14159 <|nie-special|>\n\n"


def naive_bpe(seqs, freqs, n_merges):
    """Referencja: przeliczamy wszystkie pary po każdym merge'u (wolno, ale oczywiście poprawnie)."""
    seqs = [list(s) for s in seqs]
    merges, nxt = [], 256
    for _ in range(n_merges):
        c = Counter()
        for s, f in zip(seqs, freqs):
            for p in zip(s, s[1:]):
                c[p] += f
        if not c:
            break
        best = max(c.items(), key=lambda kv: (kv[1], tuple(-x for x in kv[0])))
        if best[1] < 2:
            break
        p = best[0]
        merges.append((p[0], p[1], nxt))
        seqs = [merge_seq(s, p[0], p[1], nxt) for s in seqs]
        nxt += 1
    return merges, seqs


def test_readme_example():
    tok = SuperBPETokenizer()
    tok.train_stage1(Counter({"aaabdaaabac": 1}), 259, log=None)
    v = tok.vocab
    assert [v[n] for _, _, n in tok.stage1] == [b"aa", b"ab", b"aaab"]   # Z=aa, Y=ab, X=ZY
    assert len(tok.encode_ordinary("aaabdaaabac")) == 5                 # XdXac


def test_partition_lossless():
    for t in (CORPUS, WEIRD, "", "   ", "\n", "...", "a"):
        assert "".join(chunks(t)) == t
        assert "".join(pretokens(t)) == t
        for ch in chunks(t):
            assert "".join(WORD_RE.findall(ch)) == ch


def test_incremental_equals_naive():
    cnt = Counter(pretokens(CORPUS))
    seqs = [list(w.encode()) for w in cnt]
    freqs = list(cnt.values())
    vocab = [bytes([i]) for i in range(256)]
    fast = bpe_train_loop([list(s) for s in seqs], freqs, vocab, 256 + 150, log=None)
    slow, _ = naive_bpe(seqs, freqs, len(fast))
    assert fast == slow


@pytest.fixture(scope="module")
def tok():
    t = SuperBPETokenizer()
    t.train_stage1(Counter(pretokens(CORPUS)), 256 + 120, log=None)
    t.train_stage2(Counter(chunks(CORPUS)), 256 + 200, max_words=3, log=None)
    t.add_specials(["<|endoftext|>"])
    return t


def test_roundtrip(tok):
    for t in (CORPUS, WEIRD, "", "x" * 1000):
        assert tok.decode(tok.encode(t)) == t


def test_superwords_learned_and_bounded(tok):
    sup = [tok.vocab[n] for _, _, n in tok.stage2 if tok.is_superword(n)]
    assert sup, "etap 2 powinien nauczyć się tokenów-fraz"
    assert any(b" w ramach" in s or b"na podstawie" in s for s in sup)
    for s in sup:
        assert len(_WORDCOUNT_RE.findall(s.decode("utf-8", "ignore"))) <= 3
        assert not any(c in s for c in (b"\n", b".", b"!", b"?", b";", b":")) or s.rstrip(b".!?;:\xe2\x80\xa6") != s


def test_no_superword_crosses_sentence(tok):
    ids = tok.encode("w ramach. W ramach\nw ramach")
    for i in ids:
        b = tok.vocab[i]
        assert b"\n" not in b.strip(b"\n") or b.strip(b"\n") == b""
        assert b". " not in b and b".W" not in b


def test_encode_matches_training_state():
    """Kodowanie (merge'e wg rangi) musi dać dokładnie to, co trening zostawił w korpusie."""
    t = SuperBPETokenizer()
    cnt = Counter(pretokens(CORPUS))
    words = list(cnt)
    seqs = [list(w.encode()) for w in words]
    t.stage1 = bpe_train_loop(seqs, list(cnt.values()), t.vocab, 256 + 100, log=None)
    t._rebuild()
    for w, s in zip(words, seqs):
        assert t._encode_pretoken(w) == s

    cc = Counter(chunks(CORPUS))
    cks = list(cc)
    seqs2 = [t._encode_chunk_stage1(c) for c in cks]
    t.stage2 = bpe_train_loop(seqs2, list(cc.values()), t.vocab, 256 + 180, log=None)
    t._rebuild()
    for c, s in zip(cks, seqs2):
        assert t._encode_chunk(c) == s


def test_specials_atomic(tok):
    ids = tok.encode("Ala<|endoftext|>kot")
    assert tok.specials["<|endoftext|>"] in ids
    assert tok.encode("<|endoftext|>", allowed_special=False) != [tok.specials["<|endoftext|>"]]


def test_save_load(tok, tmp_path):
    p = tmp_path / "t.json"
    tok.save(str(p))
    t2 = SuperBPETokenizer.load(str(p))
    assert t2.vocab == tok.vocab and t2.specials == tok.specials
    assert t2.encode(CORPUS + WEIRD) == tok.encode(CORPUS + WEIRD)


def test_truncate_stage1_is_prefix():
    a = SuperBPETokenizer()
    a.train_stage1(Counter(pretokens(CORPUS)), 256 + 120, log=None)
    b = SuperBPETokenizer()
    b.train_stage1(Counter(pretokens(CORPUS)), 256 + 60, log=None)
    a.truncate_stage1(256 + 60)
    assert a.stage1 == b.stage1 and a.vocab == b.vocab
