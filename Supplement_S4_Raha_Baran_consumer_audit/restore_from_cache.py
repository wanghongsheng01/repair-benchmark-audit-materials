#!/usr/bin/env python3
"""Copy only checksum-matched public study inputs from an authorized cache."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", type=Path, required=True, help="Authorized local_source directory")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "restoration_manifest.json").read_text())
    for item in manifest["files"]:
        relative = Path(item["upstream_path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Unsafe source path")
        payload = (args.cache / relative).read_bytes()
        if len(payload) != item["bytes"] or hashlib.sha256(payload).hexdigest() != item["sha256"]:
            raise ValueError("Cached source identity mismatch: " + str(relative))
        if hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload).hexdigest() != item["git_blob_sha1"]:
            raise ValueError("Cached source Git identity mismatch: " + str(relative))
        target = ROOT / "local_source" / relative
        if target.exists() and target.read_bytes() != payload:
            raise ValueError("Refusing to overwrite different source: " + str(relative))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        print("CACHE_SOURCE_VERIFIED", relative, flush=True)
    print("AUTHORIZED_CACHE_RESTORE_OK", len(manifest["files"]), flush=True)


if __name__ == "__main__":
    main()
