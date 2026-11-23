import hashlib, os, sys
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN_MANIFEST_SHA256 = "60a93ad65b95d37eb38629929b1c5d1ec485deb7c6f0bf9b81355211d6a7e9d2"

def test_audit_manifest_frozen():
    p = os.path.join(REPO, "audit", "data", "MANIFEST.json")
    h = hashlib.sha256(open(p, "rb").read()).hexdigest()
    assert h == MAIN_MANIFEST_SHA256, (h, MAIN_MANIFEST_SHA256)
