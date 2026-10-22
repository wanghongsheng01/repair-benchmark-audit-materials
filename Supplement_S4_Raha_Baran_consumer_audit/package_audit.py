#!/usr/bin/env python3
"""Package an explicit author-artifact allowlist; never bundle external inputs."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent
FILES = [
    ".gitignore", "PROTOCOL_FROZEN.md", "protocol_freeze_receipt.json",
    "IMPLEMENTATION_PRE_DATA.md", "implementation_pre_data_receipt.json",
    "A1_POSITIONAL_SCHEMA_CLARIFICATION.md", "A1_receipt.json",
    "independent_normalizer_semantics_correction.json", "raha_candidate_protocol_proposal.json",
    "candidate_source_manifest.json", "restoration_manifest.json",
    "RESULTS.md", "README_REPRODUCE.md", "restore_inputs.py", "restore_from_cache.py",
    "run_native_audit.py", "replay_audit.py", "verify_independent.py",
    "derive_adapter_witnesses.py", "verify_package.py", "package_audit.py",
]
RESULTS = [
    "beers_native.json", "flights_native.json", "hospital_native.json", "movies_1_native.json",
    "rayyan_native.json", "tax_native.json", "toy_native.json", "native_execution_summary.json",
    "run_native_audit_invocation.json", "run_native_audit_stdout.log", "run_native_audit_stderr.log",
    "verify_independent_invocation.json", "verify_independent_stdout.log", "verify_independent_stderr.log",
    "independent_verification.json", "adapter_witnesses.json",
]
INITIAL = [
    "run_native_audit.py", "replay_audit.py",
    "results/beers_native.json", "results/flights_native.json", "results/hospital_native.json",
    "results/movies_1_native.json", "results/rayyan_native.json", "results/tax_native.json",
    "results/toy_native.json", "results/native_execution_summary.json",
    "results/run_native_audit_invocation.json", "results/run_native_audit_stdout.log",
    "results/run_native_audit_stderr.log",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    paths = sorted(FILES + ["results/" + x for x in RESULTS] + ["initial_strict_header_attempt/" + x for x in INITIAL])
    if len(paths) != len(set(paths)):
        raise RuntimeError("Duplicate package member")
    records = []
    for name in paths:
        payload = (ROOT / name).read_bytes()
        records.append({"path": name, "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()})
    manifest = {"artifact": "Supplement_S4_Raha_Baran_consumer_audit",
                "created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "scientific_scope": "All seven pinned repository pairs; default five / synthetic tax extension / toy separate; E1 and E2 negative; six Rayyan E3 adapter-value mismatches.",
                "contains_third_party_source_or_data": False,
                "source_recovery": "Restore exact official module plus fourteen CSVs using restoration_manifest.json; network or authorized local cache required.",
                "contains_review_or_submission_decision_reports": False,
                "files": records}
    (ROOT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in paths + ["MANIFEST.json"]:
            entry = zipfile.ZipInfo(name, date_time=(2026, 10, 9, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, (ROOT / name).read_bytes())
    with zipfile.ZipFile(args.output) as archive:
        assert sorted(archive.namelist()) == sorted(paths + ["MANIFEST.json"])
        assert archive.testzip() is None
        for record in records:
            assert hashlib.sha256(archive.read(record["path"])).hexdigest() == record["sha256"]
    receipt = {"archive": str(args.output.resolve()), "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
               "bytes": args.output.stat().st_size, "members": len(paths) + 1,
               "manifested_files": len(paths), "verified_members_and_hashes": True,
               "created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    (ROOT / "package_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
