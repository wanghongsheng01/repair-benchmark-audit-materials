#!/usr/bin/env python3
"""Restore only the 14 frozen official CSVs and reviewed Dataset source.

No upstream program is executed. Existing files are verified, never silently
replaced. Run explicitly with --fetch to authorize the network reads.
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parent
COMMIT = "7be1334b8c7bbdac3f47ef514fb3e1e8c5fc181c"
BASE = "https://raw.githubusercontent.com/BigDaMa/raha/" + COMMIT + "/"
SOURCE_SHA256 = "43805c3daeca0addeed1ca1b8fb4927ccedf6b98994856deea93dc0c4756ac1b"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch", action="store_true")
    args = parser.parse_args()
    proposal = json.loads((ROOT / "raha_candidate_protocol_proposal.json").read_text())
    manifest_path = ROOT / "restoration_manifest.json"
    old = json.loads(manifest_path.read_text()) if manifest_path.exists() else None
    old_by_path = {x["upstream_path"]: x for x in old["files"]} if old else {}
    targets = [dict(f) for row in proposal["roster"] for f in row["files"]]
    targets.append({"path": "raha/dataset.py", "sha256": SOURCE_SHA256})
    records = []
    for f in targets:
        relative = f["path"]
        dest = ROOT / "local_source" / relative
        if dest.exists():
            data = dest.read_bytes()
            fetched = False
        elif args.fetch:
            # Exact pinned HTTPS public source. No credentials or alternate host.
            with urllib.request.urlopen(BASE + relative, timeout=45) as response:
                if response.geturl() != BASE + relative:
                    raise RuntimeError("Unexpected source redirect")
                data = response.read()
            fetched = True
        else:
            raise RuntimeError("Missing input; run explicitly with --fetch: " + relative)
        digest = hashlib.sha256(data).hexdigest()
        blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        if "sha" in f and blob != f["sha"]:
            raise RuntimeError("Git blob identity mismatch: " + relative)
        if "size" in f and len(data) != f["size"]:
            raise RuntimeError("Source size mismatch: " + relative)
        if "sha256" in f and digest != f["sha256"]:
            raise RuntimeError("Source SHA256 mismatch: " + relative)
        if relative in old_by_path and digest != old_by_path[relative]["sha256"]:
            raise RuntimeError("Restoration identity mismatch: " + relative)
        if fetched:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
        records.append({"upstream_path": relative, "local_path": str(dest.relative_to(ROOT)),
                        "url": BASE + relative, "bytes": len(data), "sha256": digest,
                        "git_blob_sha1": blob, "fetched_now": fetched,
                        "checked_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()})
        print("INPUT_VERIFIED", relative, len(data), digest, flush=True)
    result = {"commit": COMMIT, "third_party_files_excluded_from_distribution": True,
              "files": records, "data_records_inspected": False}
    if not old:
        manifest_path.write_text(json.dumps(result, indent=2) + "\n")
    else:
        (ROOT / "restoration_recheck.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
