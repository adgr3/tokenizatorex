"""Runda 1.9 — szybkość (tokeny/s, MB/s). 1 wątek, ten sam tekst, 3 powtórzenia.

Wynik: audit/results/speed.json (+ speed.md)
"""
from __future__ import annotations

import os
import platform
import statistics
import sys
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common import RESULTS_DIR, SuperBPEEncoder, build_encoders, load_domain, write_json

TARGET_BYTES = 1_000_000
REPEATS = 3


def main() -> None:
    # tekst: fragmenty testowe z kilku dziedzin, do ~1 MB
    parts, total = [], 0
    for dom in ["web", "przetargi_ogloszenia", "prawo_eli", "wikipedia"]:
        for d in load_domain(dom, "test"):
            parts.append(d["text"])
            total += len(d["text"].encode("utf-8"))
            if total >= TARGET_BYTES:
                break
        if total >= TARGET_BYTES:
            break
    text = "\n\n".join(parts)[:TARGET_BYTES]
    nbytes = len(text.encode("utf-8"))
    encoders = build_encoders()
    out = {"meta": {"target_bytes": TARGET_BYTES, "bytes": nbytes,
                    "repeats": REPEATS, "threads": 1,
                    "cache": "dla enkodera Python czyszczony cache przed każdym powtórzeniem (pomiar zimny)",
                    "cpu": platform.processor() or platform.machine(),
                    "platform": platform.platform(), "cpus": os.cpu_count(),
                    "python": platform.python_version()}, "tokenizers": {}}
    # rozgrzewka
    for enc in encoders.values():
        enc.ids(text[:20000])
    for label, enc in encoders.items():
        times = []
        ntok = 0
        for _ in range(REPEATS):
            if isinstance(enc.encode, SuperBPEEncoder):  # referencyjny Python: pomiar zimny
                enc.encode.tok._cache1.clear()
                enc.encode.tok._cache2.clear()
            t0 = time.perf_counter()
            ids = enc.ids(text)
            times.append(time.perf_counter() - t0)
            ntok = len(ids)
        med = statistics.median(times)
        out["tokenizers"][label] = {
            "tokens": ntok, "seconds_median": med, "seconds_all": times,
            "tokens_per_s": ntok / med, "mb_per_s": (nbytes / 1e6) / med,
        }
        print(f"{label:<20} {ntok:>9} tok  {med:6.2f}s  {ntok/med:>10,.0f} tok/s  "
              f"{(nbytes/1e6)/med:6.2f} MB/s")
    write_json(os.path.join(RESULTS_DIR, "speed.json"), out)
    write_md(out)


def write_md(out: dict) -> None:
    lines = ["# Szybkość kodowania (1 wątek, mediana z 3 powtórzeń)", "",
             f"CPU: {out['meta']['cpu']} · {out['meta']['cpus']} rdzeni · "
             f"Python {out['meta']['python']} · tekst {out['meta']['bytes']/1e6:.2f} MB", "",
             "| tokenizer | tokeny | s (mediana) | tokeny/s | MB/s |",
             "|---|---:|---:|---:|---:|"]
    for l, r in out["tokenizers"].items():
        lines.append(f"| {l} | {r['tokens']:,} | {r['seconds_median']:.2f} | "
                     f"{r['tokens_per_s']:,.0f} | {r['mb_per_s']:.2f} |")
    path = os.path.join(RESULTS_DIR, "speed.md")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
