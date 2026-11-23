"""Generuje manifest korpusu TKX-V2 do tkx_v2/MANIFEST.json (bez zmiany audit/)."""
import json, os, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIT = os.path.join(REPO, "audit")
if AUDIT not in sys.path:
    sys.path.append(AUDIT)

from prepare_corpus import build_manifest, write_json  # read-only reuse

out = os.path.join(REPO, "tkx_v2", "MANIFEST.json")
os.makedirs(os.path.dirname(out), exist_ok=True)
m = build_manifest()
write_json(out, m)
print("zapisano", out)
for d, s in sorted(m["domains"].items()):
    print(f"  {d:<22} {s['docs']:>4} dok. {s['words']:>9,} słów")
