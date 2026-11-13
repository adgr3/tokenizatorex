"""
Teksty testowe z różnych dziedzin (po ~2 MB), żeby sprawdzić tokenizery poza siecią WWW.

  python prepare_benchmark.py --out ../data/bench

Źródła (publiczne, bez logowania):
  web         — held-out z SlayerLab/hplt-v3-pl-cleaned (inny shard niż trening)
  wikipedia, literatura, prawo, sejm, nauka, dyskusje
              — domeny z SlayerLab/polish-dynaword
  angielski   — Salesforce/wikitext (wikitext-103, test), żeby pokazać koszt "polskości"

Pliki parquet czytamy zdalnie (polars pobiera tylko potrzebne fragmenty).
Każdy dokument przycinamy do 20 tys. znaków, żeby jedna książka nie zdominowała próbki.
"""
import argparse
import os
import random

import polars as pl

HF = "https://huggingface.co/datasets"
DYNAWORD = f"{HF}/SlayerLab/polish-dynaword/resolve/main/data"
DOMAINS = {
    "wikipedia": f"{DYNAWORD}/wikipedia/wikipedia.parquet",
    "literatura": f"{DYNAWORD}/wolne_lektury/wolne_lektury.parquet",
    "prawo": f"{DYNAWORD}/dziennik_ustaw/dziennik_ustaw.parquet",
    "sejm": f"{DYNAWORD}/sejm_committee_transcripts/sejm_committee_transcripts.parquet",
    "nauka": f"{DYNAWORD}/biblioteka_nauki/biblioteka_nauki.parquet",
    "dyskusje": f"{DYNAWORD}/plwiki_talk/plwiki_talk.parquet",
    "angielski": f"{HF}/Salesforce/wikitext/resolve/main/wikitext-103-raw-v1/test-00000-of-00001.parquet",
}
DOC_CAP = 20_000


def sample_remote(url: str, target: int, seed: int, pool_rows: int = 6000) -> list[str]:
    texts = pl.scan_parquet(url).select("text").head(pool_rows).collect().get_column("text").to_list()
    random.Random(seed).shuffle(texts)
    out, total = [], 0
    for t in texts:
        t = (t or "").replace("\r\n", "\n").strip()
        if len(t) < 200:
            continue
        t = t[:DOC_CAP]
        out.append(t)
        total += len(t.encode("utf-8"))
        if total >= target:
            break
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="../data/bench")
    ap.add_argument("--mb", type=float, default=2)
    ap.add_argument("--heldout", default="../data/heldout.txt")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    target = int(a.mb * 10**6)

    with open(a.heldout, encoding="utf-8") as f:
        web = f.read(target)
    with open(os.path.join(a.out, "web.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write(web)
    print(f"web: {len(web.encode()) / 1e6:.1f} MB")

    for name, url in DOMAINS.items():
        docs = sample_remote(url, target, seed=7)
        if name == "angielski":   # wikitext ma jeden akapit na wiersz — sklejamy w ciągły tekst
            docs = sample_remote_lines(url, target)
        with open(os.path.join(a.out, f"{name}.txt"), "w", encoding="utf-8", newline="\n") as f:
            f.write("\n\n".join(docs))
        print(f"{name}: {len(docs)} dok., {sum(len(d.encode()) for d in docs) / 1e6:.1f} MB")


def sample_remote_lines(url: str, target: int) -> list[str]:
    lines = pl.read_parquet(url, columns=["text"]).get_column("text").to_list()
    out, total = [], 0
    for t in lines:
        t = t.strip()
        if len(t) < 200 or t.startswith("="):
            continue
        out.append(t)
        total += len(t.encode("utf-8"))
        if total >= target:
            break
    return out


if __name__ == "__main__":
    main()
