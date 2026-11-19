"""Print short, generic excerpts of the documents where competitors beat TKX."""
from __future__ import annotations

import json
import os
import sys

sys.dont_write_bytecode = True
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import rtlib as R  # noqa: E402


def main() -> None:
    data = json.load(open(os.path.join(os.path.dirname(__file__), "r3_worst50.json"),
                          encoding="utf-8"))
    lines = []
    seen = set()
    for key in ("top50_slayer", "top50_apt3"):
        lines.append(f"===== {key}")
        for r in data[key][:10]:
            if r["id"] in seen:
                continue
            seen.add(r["id"])
            adv = r.get("adv_slayer", r.get("adv_apt3"))
            lines.append(f"{r['id']} | {r['domain']} | adv={adv:+.4f} | words={r['words']} "
                         f"| tokens={r['tokens']}")
            for s in r["snippets"][:3]:
                lines.append("  | " + s)
            lines.append("")
    path = os.path.join(os.path.dirname(__file__), "r3_examples.txt")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("saved", path)


if __name__ == "__main__":
    main()
