#!/usr/bin/env python3
"""Portable local replay; Python >=3.10, standard library only, no original paths."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized(value, *, reveal=False):
    result = dict(value)
    result.pop("started_utc", None)
    result.pop("finished_utc", None)
    if reveal:
        result.pop("blind_results_sha256", None)  # New run has new UTC fields.
    return result


def main():
    if sys.version_info < (3, 10):
        raise SystemExit("Python 3.10 or newer is required; no packages need installation.")
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True,
                        help="New output directory; existing directories are refused")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    verified = []
    for manifest_name in ("protocol/FREEZE_A1.json", "seals/BLIND_SEAL.json", "seals/REVEAL_SEAL.json"):
        manifest = json.loads((root / manifest_name).read_text())
        for item in manifest["artifacts"]:
            assert sha(root / item["path"]) == item["sha256"], item["path"]
            verified.append(item["path"])
    original = json.loads((root / "protocol/FREEZE.json").read_text())
    original_matcher = next(x for x in original["artifacts"] if x["path"] == "code/blind_matcher.py")
    assert sha(root / "protocol/blind_matcher_frozen_initial.py") == original_matcher["sha256"]
    new_blind = output / "blind_results.json"
    subprocess.run([sys.executable, str(root / "code/blind_matcher.py"),
                    "--input-root", str(root / "inputs/blind_csv"), "--output", str(new_blind)], check=True)
    assert normalized(json.loads(new_blind.read_text())) == normalized(json.loads((root / "results/blind_results.json").read_text())), "Blind replay changed substantive output"
    # Seal this replay BEFORE its native-reference scorer starts too.
    replay_seal = {"sealed_utc": datetime.now(timezone.utc).isoformat(),
                   "blind_results_sha256": sha(new_blind), "phase": "fresh replay blind result sealed before replay reveal"}
    (output / "BLIND_REPLAY_SEAL.json").write_text(json.dumps(replay_seal, indent=2) + "\n")
    new_reveal = output / "reveal_results.json"
    subprocess.run([sys.executable, str(root / "code/reveal_and_score.py"),
                    "--package-root", str(root), "--blind-results", str(new_blind),
                    "--output", str(new_reveal)], check=True)
    assert normalized(json.loads(new_reveal.read_text()), reveal=True) == normalized(json.loads((root / "results/reveal_results.json").read_text()), reveal=True), "Reveal replay changed substantive output"
    result = {"status": "PASS", "finished_utc": datetime.now(timezone.utc).isoformat(),
              "python_version": sys.version, "verified_frozen_artifacts": sorted(set(verified)),
              "blind_substantive_output_identical": True, "reveal_substantive_output_identical": True,
              "network_or_upstream_execution": False,
              "replay_blind_sha256": sha(new_blind), "replay_reveal_sha256": sha(new_reveal)}
    (output / "REPRODUCTION_RESULT.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
