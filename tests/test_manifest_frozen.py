import hashlib
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Hash of audit/data/MANIFEST.json with line endings normalized to LF
MAIN_MANIFEST_SHA256 = "6f72686f716b93f7fadd90090a7f1b51ee29eb88fbbe8e5062a6a7a70cef6dc6"


def test_audit_manifest_frozen():
    p = os.path.join(REPO, "audit", "data", "MANIFEST.json")
    data = open(p, "rb").read()
    # Normalize line endings so hash is independent of CRLF/LF checkout
    data_norm = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    h = hashlib.sha256(data_norm).hexdigest()
    assert h == MAIN_MANIFEST_SHA256, (h, MAIN_MANIFEST_SHA256)
