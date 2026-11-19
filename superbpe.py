"""
SuperBPE-PL — byte-level BPE z tokenami-frazami ("superwords"), od zera w czystym Pythonie.

Pomysł (Liu i in., 2025, "SuperBPE: Space Travel for Language Models"):
  * Etap 1 (do punktu przejścia t): zwykły byte-level BPE, merge'e tylko WEWNĄTRZ
    pretokenów (słowo z wiodącą spacją, liczba, interpunkcja) — jak GPT-2/GPT-4.
  * Etap 2 (od t do docelowego słownika): wyłączamy podział na spacjach i BPE może
    łączyć tokeny PRZEZ spację — powstają tokeny typu " na podstawie", " w ramach".
    Granic zdań (. ! ? ; : …) i nowych linii nadal nie przekraczamy, a jeden token
    obejmuje maksymalnie `max_words` słów.

Baseline (zwykły BPE) to po prostu ten sam trening z t = docelowy słownik.

Bez zależności poza `regex` (klasy Unicode \\p{L}).
"""
from __future__ import annotations

import heapq
import json
import unicodedata
from collections import Counter, defaultdict
from typing import Callable, Iterable

import regex as re

# --- pretokenizacja ---------------------------------------------------------------

# Poziom 2 (fragmenty zdań): granica na nowej linii i interpunkcji kończącej zdanie.
# Wzorzec pokrywa KAŻDY znak tekstu (partycja), więc nic nie ginie.
CHUNK_PATTERN = r"[^\r\n.!?;:…]+[.!?;:…]*|[.!?;:…]+|[\r\n]+"

# Poziom 1 (słowa): inspirowany regexem cl100k/o200k, uproszczony dla polskiego
# (bez angielskich skrótów 's 't), cyfry w grupach po max 3.
WORD_PATTERN = (
    r"[^\r\n\p{L}\p{M}\p{N}]?[\p{L}\p{M}]+"   # słowo, opcjonalnie ze spacją/znakiem z przodu
    r"|\p{N}{1,3}"                              # liczby po max 3 cyfry
    r"| ?[^\s\p{L}\p{M}\p{N}]+[\r\n]*"          # interpunkcja / symbole
    r"|\s*[\r\n]+"                              # nowe linie
    r"|\s+(?!\S)"                               # białe znaki (bez ostatniej spacji przed słowem)
    r"|\s+"
)

# Wariant TKX-C: każda cyfra osobno (bez grup \p{N}{1,3}).
WORD_PATTERN_SINGLE_DIGITS = WORD_PATTERN.replace(r"\p{N}{1,3}", r"\p{Nd}")

CHUNK_RE = re.compile(CHUNK_PATTERN)
WORD_RE = re.compile(WORD_PATTERN)
_WORDCOUNT_RE = re.compile(r"[\p{L}\p{M}]+|\p{N}+")
_DIGIT_RE = re.compile(r"\p{Nd}")
_WORD_PATTERN_CACHE: dict[str, re.Pattern] = {}


def normalize_text(text: str, mode: str = "none") -> str:
    """A2: jedno miejsce normalizacji (domyślnie brak zmian = v1)."""
    if mode == "nfc":
        return unicodedata.normalize("NFC", text)
    if mode == "none":
        return text
    raise ValueError(f"nieznany tryb normalizacji: {mode}")


def word_regex(pattern: str = WORD_PATTERN) -> re.Pattern:
    rx = _WORD_PATTERN_CACHE.get(pattern)
    if rx is None:
        rx = re.compile(pattern)
        _WORD_PATTERN_CACHE[pattern] = rx
    return rx


def chunks(text: str, normalize: str = "none") -> list[str]:
    return CHUNK_RE.findall(normalize_text(text, normalize))


def pretokens(text: str, word_pattern: str = WORD_PATTERN, normalize: str = "none") -> list[str]:
    """Pretokeny etapu 1 — zawsze liczone wewnątrz fragmentów (chunków)."""
    out: list[str] = []
    rx = word_regex(word_pattern)
    for ch in CHUNK_RE.findall(normalize_text(text, normalize)):
        out.extend(rx.findall(ch))
    return out


# --- operacje podstawowe ------------------------------------------------------------

def merge_seq(seq: list[int], a: int, b: int, new: int) -> list[int]:
    """Zamień każde wystąpienie pary (a, b) na `new`, od lewej do prawej."""
    out: list[int] = []
    i, n = 0, len(seq)
    while i < n:
        if i < n - 1 and seq[i] == a and seq[i + 1] == b:
            out.append(new)
            i += 2
        else:
            out.append(seq[i])
            i += 1
    return out


def merge_by_rank(seq: list[int], ranks: dict[tuple[int, int], tuple[int, int]]) -> list[int]:
    """Kodowanie: dopóki się da, scalaj parę o NAJNIŻSZEJ randze (najwcześniej wyuczoną)."""
    while len(seq) > 1:
        best, best_rank = None, None
        for p in zip(seq, seq[1:]):
            r = ranks.get(p)
            if r is not None and (best_rank is None or r[0] < best_rank):
                best, best_rank = p, r[0]
        if best is None:
            break
        seq = merge_seq(seq, best[0], best[1], ranks[best][1])
    return seq


# --- pętla treningowa (wspólna dla obu etapów) --------------------------------------

def bpe_train_loop(
    seqs: list[list[int]],
    freqs: list[int],
    vocab: list[bytes],
    target_vocab: int,
    allowed: Callable[[tuple[int, int], bytes], bool] | None = None,
    min_freq: int = 2,
    log: Callable[[str], None] | None = print,
    log_every: int = 1000,
) -> list[tuple[int, int, int]]:
    """
    Inkrementalny BPE: liczniki par + indeks "w których sekwencjach para występuje"
    + kopiec z leniwym usuwaniem. Wynik identyczny z naiwnym BPE (najczęstsza para,
    remis -> najmniejsza para), ale bez przeliczania wszystkiego po każdym merge'u.

    Modyfikuje `seqs` i `vocab` w miejscu. Zwraca listę (a, b, new_id).
    """
    counts: dict[tuple[int, int], int] = defaultdict(int)
    where: dict[tuple[int, int], set[int]] = defaultdict(set)
    for i, (s, f) in enumerate(zip(seqs, freqs)):
        for p in zip(s, s[1:]):
            counts[p] += f
            where[p].add(i)

    heap = [(-c, p) for p, c in counts.items()]
    heapq.heapify(heap)
    banned: set[tuple[int, int]] = set()
    merges: list[tuple[int, int, int]] = []

    while len(vocab) < target_vocab and heap:
        negc, p = heapq.heappop(heap)
        c = counts.get(p, 0)
        if c <= 0 or p in banned:
            continue
        if -negc != c:                      # wpis nieaktualny -> odłóż z aktualną wartością
            heapq.heappush(heap, (-c, p))
            continue
        if c < min_freq:
            break
        a, b = p
        new_bytes = vocab[a] + vocab[b]
        if allowed is not None and not allowed(p, new_bytes):
            banned.add(p)
            continue

        new_id = len(vocab)
        vocab.append(new_bytes)
        merges.append((a, b, new_id))

        delta: dict[tuple[int, int], int] = defaultdict(int)
        for i in list(where[p]):
            s, f = seqs[i], freqs[i]
            ns = merge_seq(s, a, b, new_id)
            old_pairs = list(zip(s, s[1:]))
            new_pairs = list(zip(ns, ns[1:]))
            for q in old_pairs:
                delta[q] -= f
            for q in new_pairs:
                delta[q] += f
            old_set, new_set = set(old_pairs), set(new_pairs)
            for q in old_set - new_set:
                w = where.get(q)
                if w is not None:
                    w.discard(i)
            for q in new_set - old_set:
                where[q].add(i)
            seqs[i] = ns

        for q, d in delta.items():
            if d == 0:
                continue
            counts[q] += d
            if counts[q] <= 0:
                counts.pop(q, None)
                where.pop(q, None)
            elif d > 0:
                heapq.heappush(heap, (-counts[q], q))
        counts.pop(p, None)
        where.pop(p, None)

        if log and len(merges) % log_every == 0:
            log(f"  merge {len(merges):>6}  vocab {len(vocab):>6}  freq {c:>9}  {new_bytes!r}")

    return merges


# --- tokenizer ----------------------------------------------------------------------

class SuperBPETokenizer:
    def __init__(self, digits: str = "grouped", normalize: str = "none") -> None:
        if digits not in ("grouped", "single"):
            raise ValueError(f"nieznany tryb cyfr: {digits}")
        normalize_text("", normalize)  # walidacja trybu
        self.digits = digits
        self.normalize = normalize
        self.word_pattern = (WORD_PATTERN_SINGLE_DIGITS if digits == "single"
                             else WORD_PATTERN)
        self._word_re = word_regex(self.word_pattern)
        self.vocab: list[bytes] = [bytes([i]) for i in range(256)]
        self.stage1: list[tuple[int, int, int]] = []
        self.stage2: list[tuple[int, int, int]] = []
        self.max_words = 4
        self.specials: dict[str, int] = {}
        self.meta: dict = {}
        self._rebuild()

    # ---- indeksy pomocnicze
    def _rebuild(self) -> None:
        self.ranks1 = {(a, b): (r, n) for r, (a, b, n) in enumerate(self.stage1)}
        off = len(self.stage1)
        self.ranks2 = {(a, b): (off + r, n) for r, (a, b, n) in enumerate(self.stage2)}
        self._cache1: dict[str, list[int]] = {}
        self._cache2: dict[str, list[int]] = {}
        self.inv_specials = {v: k for k, v in self.specials.items()}

    @property
    def transition(self) -> int:
        return 256 + len(self.stage1)

    @property
    def vocab_size(self) -> int:
        return len(self.vocab) + len(self.specials)

    def is_superword(self, tid: int) -> bool:
        """Token zawiera spację w środku, czyli przekracza granicę słowa."""
        if tid >= len(self.vocab):
            return False
        return b" " in self.vocab[tid].lstrip(b" ")

    # ---- trening
    def train_stage1(self, pretoken_counts: Counter, target_vocab: int, log=print) -> None:
        items = list(pretoken_counts.items())
        seqs = [list(w.encode("utf-8")) for w, _ in items]
        freqs = [f for _, f in items]
        self.stage1 = bpe_train_loop(seqs, freqs, self.vocab, target_vocab, log=log)
        self._rebuild()

    def truncate_stage1(self, transition: int) -> None:
        """Etap 1 jest deterministyczny, więc t < pełny słownik to prefiks merge'y baseline'u."""
        n = transition - 256
        self.stage1 = self.stage1[:n]
        self.stage2 = []
        self.vocab = self.vocab[:transition]
        self._rebuild()

    def train_stage2(self, chunk_counts: Counter, target_vocab: int, max_words: int = 4, log=print) -> None:
        self.max_words = max_words
        items = list(chunk_counts.items())
        seqs = [self._encode_chunk_stage1(ch) for ch, _ in items]
        freqs = [f for _, f in items]
        stage1_pairs = set(self.ranks1)

        def allowed(p: tuple[int, int], new_bytes: bytes) -> bool:
            if p in stage1_pairs:           # para już ma merge z etapu 1 — nie dublujemy
                return False
            text = new_bytes.decode("utf-8", errors="ignore")
            if self.digits == "single" and _DIGIT_RE.search(text):
                return False                # A1: superwordy nie mogą zawierać cyfr
            words = _WORDCOUNT_RE.findall(text)
            return len(words) <= max_words

        self.stage2 = bpe_train_loop(seqs, freqs, self.vocab, target_vocab, allowed=allowed, log=log)
        self._rebuild()

    def add_specials(self, names: Iterable[str]) -> None:
        for name in names:
            if name not in self.specials:
                self.specials[name] = len(self.vocab) + len(self.specials)
        self._rebuild()

    # ---- kodowanie
    def _encode_pretoken(self, pt: str) -> list[int]:
        ids = self._cache1.get(pt)
        if ids is None:
            ids = merge_by_rank(list(pt.encode("utf-8")), self.ranks1)
            if len(self._cache1) < 2_000_000:
                self._cache1[pt] = ids
        return ids

    def _encode_chunk_stage1(self, ch: str) -> list[int]:
        out: list[int] = []
        for pt in self._word_re.findall(ch):
            out.extend(self._encode_pretoken(pt))
        return out

    def _encode_chunk(self, ch: str) -> list[int]:
        if not self.stage2:
            return self._encode_chunk_stage1(ch)
        ids = self._cache2.get(ch)
        if ids is None:
            ids = merge_by_rank(self._encode_chunk_stage1(ch), self.ranks2)
            if len(self._cache2) < 500_000:
                self._cache2[ch] = ids
        return ids

    def encode_ordinary(self, text: str) -> list[int]:
        text = normalize_text(text, self.normalize)
        out: list[int] = []
        for ch in CHUNK_RE.findall(text):
            out.extend(self._encode_chunk(ch))
        return out

    def encode(self, text: str, allowed_special: bool = True) -> list[int]:
        """Koduje tekst; tokeny specjalne (np. <|endoftext|>) są atomowe."""
        text = normalize_text(text, self.normalize)
        if not (allowed_special and self.specials):
            return self.encode_ordinary(text)
        pat = "(" + "|".join(re.escape(s) for s in sorted(self.specials, key=len, reverse=True)) + ")"
        out: list[int] = []
        for part in re.split(pat, text):
            if part in self.specials:
                out.append(self.specials[part])
            elif part:
                out.extend(self.encode_ordinary(part))
        return out

    def decode_bytes(self, ids: Iterable[int]) -> bytes:
        parts = []
        for i in ids:
            if i in self.inv_specials:
                parts.append(self.inv_specials[i].encode("utf-8"))
            else:
                parts.append(self.vocab[i])
        return b"".join(parts)

    def decode(self, ids: Iterable[int]) -> str:
        return self.decode_bytes(ids).decode("utf-8", errors="replace")

    # ---- zapis / odczyt
    def save(self, path: str) -> None:
        data = {
            "format": "superbpe-pl/1",
            "chunk_pattern": CHUNK_PATTERN,
            "word_pattern": self.word_pattern,
            "digits": self.digits,
            "normalize": self.normalize,
            "max_words": self.max_words,
            "transition": self.transition,
            "vocab_size": self.vocab_size,
            "stage1_merges": [list(m) for m in self.stage1],
            "stage2_merges": [list(m) for m in self.stage2],
            "specials": self.specials,
            "meta": self.meta,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

    @classmethod
    def load(cls, path: str) -> "SuperBPETokenizer":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert data["chunk_pattern"] == CHUNK_PATTERN, "plik zapisany z innym chunk_pattern"
        word_pattern = data.get("word_pattern", WORD_PATTERN)
        digits = data.get("digits")
        if digits is None:
            if word_pattern == WORD_PATTERN:
                digits = "grouped"
            elif word_pattern == WORD_PATTERN_SINGLE_DIGITS:
                digits = "single"
            else:
                raise ValueError("plik zapisany z nieznanym word_pattern")
        normalize = data.get("normalize", "none")
        tok = cls(digits=digits, normalize=normalize)
        assert word_pattern == tok.word_pattern, "plik zapisany z innymi regexami"
        tok._word_re = word_regex(tok.word_pattern)
        tok.stage1 = [tuple(m) for m in data["stage1_merges"]]
        tok.stage2 = [tuple(m) for m in data["stage2_merges"]]
        for a, b, n in tok.stage1 + tok.stage2:
            assert n == len(tok.vocab), "niespójna numeracja merge'y"
            tok.vocab.append(tok.vocab[a] + tok.vocab[b])
        tok.max_words = data.get("max_words", 4)
        tok.specials = data.get("specials", {})
        tok.meta = data.get("meta", {})
        tok._rebuild()
        return tok
