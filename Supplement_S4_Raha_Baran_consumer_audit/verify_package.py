#!/usr/bin/env python3
"""Verify the distributed author-owned artifact before any replay rewrites logs."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    manifest = json.loads((ROOT / "MANIFEST.json").read_text())
    for record in manifest["files"]:
        path = Path(record["path"])
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("Unsafe manifest path")
        payload = (ROOT / path).read_bytes()
        if len(payload) != record["bytes"] or hashlib.sha256(payload).hexdigest() != record["sha256"]:
            raise ValueError("Distributed file identity mismatch: " + str(path))
    print("CONSUMER_AUDIT_PACKAGE_OK", len(manifest["files"]))


if __name__ == "__main__":
    main()
