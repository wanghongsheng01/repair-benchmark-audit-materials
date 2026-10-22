#!/usr/bin/env python3
"""Run the frozen native audit and independent replay with invocation receipts."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    output = ROOT / "results"
    output.mkdir(exist_ok=True)
    runs = []
    for script in ["run_native_audit.py", "verify_independent.py"]:
        stem = script.removesuffix(".py")
        command = [sys.executable, str(ROOT / script)]
        before = {str(p.relative_to(ROOT)): checksum(p) for p in [ROOT / script, ROOT / "PROTOCOL_FROZEN.md", ROOT / "IMPLEMENTATION_PRE_DATA.md", ROOT / "restoration_manifest.json", ROOT / "local_source" / "raha" / "dataset.py"]}
        record = {"argv": command, "cwd": str(ROOT), "started_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "input_code_sha256": before}
        (output / (stem + "_invocation.json")).write_text(json.dumps(record, indent=2) + "\n")
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        with (output / (stem + "_stdout.log")).open("w") as stdout, (output / (stem + "_stderr.log")).open("w") as stderr:
            process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=stderr, text=True)
            for line in process.stdout:
                stdout.write(line)
                stdout.flush()
                print(line, end="", flush=True)
            returncode = process.wait()
        record.update({"finished_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "returncode": returncode,
                       "stdout_sha256": checksum(output / (stem + "_stdout.log")), "stderr_sha256": checksum(output / (stem + "_stderr.log")),
                       "input_code_unchanged": all(checksum(ROOT / relative) == expected for relative, expected in before.items())})
        (output / (stem + "_invocation.json")).write_text(json.dumps(record, indent=2) + "\n")
        runs.append(record)
        if returncode:
            print("AUDIT_STOPPED", script, returncode, flush=True)
            sys.exit(returncode)
    print("FROZEN_SEVEN_PAIR_AUDIT_OK", flush=True)


if __name__ == "__main__":
    main()
