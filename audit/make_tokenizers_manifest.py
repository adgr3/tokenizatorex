"""Zapisuje audit/results/tokenizers_manifest.json (plik + SHA-256 + commit HF)."""
from __future__ import annotations

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common import RESULTS_DIR, TOK_DIR, tokenizer_manifest, write_json  # noqa: E402

import tiktoken  # noqa: E402
from huggingface_hub import HfApi  # noqa: E402


def main() -> None:
    api = HfApi()
    rows = tokenizer_manifest()
    for row in rows:
        if row.get("kind") == "hf_repo":
            try:
                info = api.model_info(row["repo"])
                row["repo_commit"] = info.sha
            except Exception as ex:  # noqa: BLE001
                row["repo_commit"] = f"UNKNOWN ({type(ex).__name__})"
        if row.get("kind") == "tiktoken":
            row["tiktoken_version"] = getattr(tiktoken, "__version__", "UNKNOWN")
    payload = {
        "note": "Wszystkie enkodery bez tokenów specjalnych; SHA-256 pliku, którego użył audyt.",
        "tokenizer_files_dir": os.path.relpath(TOK_DIR, os.path.dirname(RESULTS_DIR)),
        "tokenizers": rows,
    }
    write_json(os.path.join(RESULTS_DIR, "tokenizers_manifest.json"), payload)
    for r in rows:
        print(f"{r['label']:<20} {r.get('vocab', '')} {r.get('sha256', r.get('encoding', ''))[:16]} "
              f"{r.get('repo_commit', '')[:8]}")


if __name__ == "__main__":
    main()
