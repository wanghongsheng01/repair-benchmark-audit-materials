#!/usr/bin/env python3
"""Locate E3's mismatching replacement values without distributing source text.

This is a post-run mechanical explanation of the frozen endpoint. It introduces
no new corpus, predictions, corruption, or outcome-selection rule.
"""
import csv
import datetime
import hashlib
import html
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent


def sha(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def norm(value):
    return re.sub(r"[\t\n ]+", " ", html.unescape(value), count=32).strip("\t\n ")


def main():
    roster = json.loads((ROOT / "raha_candidate_protocol_proposal.json").read_text())["roster"]
    reports = []
    for entry in roster:
        name = entry["name"]
        base = ROOT / "local_source" / "datasets" / name
        with (base / "dirty.csv").open(newline="", encoding="utf-8") as f:
            dirty = list(csv.reader(f))
        with (base / "clean.csv").open(newline="", encoding="utf-8") as f:
            clean = list(csv.reader(f))
        witnesses = []
        errors = 0
        for i, (drow, crow) in enumerate(zip(dirty[1:], clean[1:])):
            for j, (d, c) in enumerate(zip(drow, crow)):
                nd, nc = norm(d), norm(c)
                if nd != nc:
                    errors += 1
                    if c != nc:
                        witnesses.append({"row_index_0based": i, "column_index_0based": j,
                                          "dirty_header": dirty[0][j], "clean_header": clean[0][j],
                                          "raw_clean_sha256": sha(c), "native_clean_sha256": sha(nc),
                                          "html_unescape_changes_value": html.unescape(c) != c,
                                          "whitespace_step_changes_value": nc != html.unescape(c)})
        native = json.loads((ROOT / "results" / (name + "_native.json")).read_text())
        assert errors == native["E1"]["native_labels"]["count"]
        expected = (errors - len(witnesses)) / errors if errors else 0.0
        assert native["E3"]["native_coordinates_raw_clean"]["native_scores"][3] == expected
        reports.append({"name": name, "native_error_coordinates": errors,
                        "mismatching_raw_clean_values": len(witnesses), "witnesses": witnesses})
    result = {"created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "purpose": "Post-run explanation of frozen E3; source values omitted", "cases": reports,
              "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (ROOT / "results" / "adapter_witnesses.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({r["name"]: r["mismatching_raw_clean_values"] for r in reports}))


if __name__ == "__main__":
    main()
