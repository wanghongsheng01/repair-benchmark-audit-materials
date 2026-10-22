#!/usr/bin/env python3
"""Independent stdlib-only reconstruction; imports neither pandas nor harness.

Coordinate digest: sorted UTF-8 'row,column\n'. Target digest: sorted UTF-8
'row,column:SHA256(value UTF-8)\n'. Table digest: compact UTF-8 JSON rows,
including the header, each followed by newline. No raw values are distributed.
"""
import csv
import datetime
import hashlib
import html
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent


def digest(data):
    return hashlib.sha256(data).hexdigest()


def normalize(value):
    decoded = html.unescape(value)
    # Upstream passes re.UNICODE as fourth positional argument: count=32,
    # not flags. Preserve that literal behavior; do not repair upstream.
    collapsed = re.sub(r"[\t\n ]+", " ", decoded, count=32)
    return collapsed.strip("\t\n ")


def read_table(path):
    with open(path, newline="", encoding="utf-8") as stream:
        reader = csv.reader(stream)
        columns = next(reader)
        records = [tuple(record) for record in reader]
    if len(set(columns)) != len(columns) or any(len(record) != len(columns) for record in records):
        raise ValueError("Unsupported CSV schema: " + str(path))
    return columns, records


def coordinate_digest(keys):
    data = "".join("{},{}\n".format(*key) for key in sorted(keys))
    return digest(data.encode("utf-8"))


def dictionary_summary(values):
    target_lines = []
    for key in sorted(values):
        target_lines.append("{},{}:{}\n".format(key[0], key[1], digest(values[key].encode("utf-8"))))
    return {"count": len(values), "coordinates_sha256": coordinate_digest(values),
            "target_values_sha256": digest("".join(target_lines).encode("utf-8"))}


def table_digest(columns, rows):
    result = hashlib.sha256()
    result.update((json.dumps(columns, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8"))
    for record in rows:
        result.update((json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8"))
    return result.hexdigest()


def difference(left, right):
    result = {}
    for r, a in enumerate(left):
        for c, value in enumerate(a):
            if value != right[r][c]:
                result[r, c] = right[r][c]
    return result


def set_delta(before, after):
    b, a = set(before), set(after)
    removed, added = b.difference(a), a.difference(b)
    return {"before_count": len(b), "after_count": len(a), "common_count": len(b.intersection(a)),
            "removed_count": len(removed), "added_count": len(added),
            "removed_coordinates_sha256": coordinate_digest(removed), "added_coordinates_sha256": coordinate_digest(added),
            "removed_rows": len(set(r for r, c in removed)), "added_rows": len(set(r for r, c in added)),
            "removed_columns": sorted(set(c for r, c in removed)), "added_columns": sorted(set(c for r, c in added)),
            "jaccard": len(b.intersection(a)) / len(b.union(a)) if b.union(a) else 1.0}


def value_delta(before, after):
    changes = difference(before, after)
    return {"count": len(changes), "coordinates_sha256": coordinate_digest(changes),
            "rows": len({key[0] for key in changes}), "columns": sorted({key[1] for key in changes})}


def score(predictions, gold):
    detection_tp = len(set(predictions).intersection(gold))
    correction_tp = sum(value == gold[key] for key, value in predictions.items() if key in gold)
    output = []
    for hits in [detection_tp, correction_tp]:
        precision = hits / len(predictions) if predictions else 0.0
        recall = hits / len(gold) if gold else 0.0
        f1 = 2.0 * precision * recall / (precision + recall) if precision + recall else 0.0
        output.extend([precision, recall, f1])
    return output


def main():
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    manifest = json.loads((ROOT / "restoration_manifest.json").read_text())
    for record in manifest["files"]:
        data = (ROOT / record["local_path"]).read_bytes()
        assert digest(data) == record["sha256"], "Source fingerprint drift"
        assert hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest() == record["git_blob_sha1"]
    roster = json.loads((ROOT / "raha_candidate_protocol_proposal.json").read_text())["roster"]
    all_reports = []
    mismatches = []
    for entry in roster:
        name = entry["name"]
        native_path = ROOT / "results" / (name + "_native.json")
        observed = json.loads(native_path.read_text())
        if observed["status"] != "completed":
            mismatches.append({"case": name, "field": "status", "actual": observed["status"]})
            continue
        header, dirty = read_table(ROOT / "local_source" / "datasets" / name / "dirty.csv")
        other_header, clean = read_table(ROOT / "local_source" / "datasets" / name / "clean.csv")
        assert len(header) == len(other_header) and len(dirty) == len(clean)
        n_dirty = [tuple(normalize(x) for x in row) for row in dirty]
        n_clean = [tuple(normalize(x) for x in row) for row in clean]
        nn_dirty = [tuple(normalize(x) for x in row) for row in n_dirty]
        nn_clean = [tuple(normalize(x) for x in row) for row in n_clean]
        raw_gold = difference(dirty, clean)
        gold = difference(n_dirty, n_clean)
        twice_gold = difference(nn_dirty, nn_clean)
        expected = {"rows": len(dirty), "columns": len(header), "headers": header,
                    "clean_headers": other_header, "header_names_equal": header == other_header,
                    "cells_per_pair_side": len(dirty) * len(header),
                    "raw_dirty_table_sha256": table_digest(header, dirty), "raw_clean_table_sha256": table_digest(other_header, clean),
                    "native_dirty_table_sha256": table_digest(header, n_dirty), "native_clean_table_sha256": table_digest(other_header, n_clean)}
        expected["E1"] = {"raw_labels": dictionary_summary(raw_gold), "native_labels": dictionary_summary(gold),
                          "label_delta": set_delta(raw_gold, gold), "dirty_raw_to_native": value_delta(dirty, n_dirty),
                          "clean_raw_to_native": value_delta(clean, n_clean)}
        target_drift = {key: twice_gold[key] for key in gold if key in twice_gold and gold[key] != twice_gold[key]}
        exports = {}
        for kind, normalized in [("dirty", n_dirty), ("clean", n_clean)]:
            path = ROOT / "local_roundtrip" / name / (kind + ".csv")
            export_header, export_table = read_table(path)
            # Explicit every-record and every-field agreement, not only digest.
            assert export_header == (header if kind == "dirty" else other_header) and export_table == normalized, "Native export values differ from independent normalization"
            exports[kind] = {"bytes": path.stat().st_size, "sha256": digest(path.read_bytes())}
        expected["E2"] = {"native_export_api": "Dataset.write_csv_dataset", "native_reload_api": "Dataset.__init__ / read_csv_dataset",
                          "dirty_value_changes": value_delta(n_dirty, nn_dirty), "clean_value_changes": value_delta(n_clean, nn_clean),
                          "reloaded_dirty_table_sha256": table_digest(header, nn_dirty), "reloaded_clean_table_sha256": table_digest(other_header, nn_clean),
                          "reloaded_labels": dictionary_summary(twice_gold), "label_delta": set_delta(gold, twice_gold),
                          "common_error_target_changes": dictionary_summary(target_drift), "export_files": exports}
        probes = {"native_coordinates_native_clean": gold,
                  "native_coordinates_raw_clean": {key: clean[key[0]][key[1]] for key in gold},
                  "raw_coordinates_raw_clean": raw_gold,
                  "raw_coordinates_native_clean": {key: n_clean[key[0]][key[1]] for key in raw_gold}}
        expected["E3"] = {}
        for label, probe in probes.items():
            data = {"dictionary": dictionary_summary(probe), "native_scores": score(probe, gold)}
            if label.startswith("native_coordinates_"):
                materialized = {}
                for key, value in probe.items():
                    converted = normalize(value)
                    if converted != n_dirty[key[0]][key[1]]:
                        materialized[key] = converted
                data.update({"materialized_dictionary": dictionary_summary(materialized),
                             "materialized_native_scores": score(materialized, gold),
                             "direct_to_materialized_label_delta": set_delta(probe, materialized),
                             "common_target_changes": sum(value != materialized[key] for key, value in probe.items() if key in materialized)})
            expected["E3"][label] = data
        expected["E4"] = {kind + "_self_pair": {"labels": dictionary_summary({}), "empty_probe_scores": [0.0] * 6} for kind in ["dirty", "clean"]}
        expected["E4"]["normalized_oracle_expected_scores"] = [1.0] * 6 if gold else [0.0] * 6
        expected["E4"]["normalized_oracle_pass"] = True
        for key, value in expected.items():
            if value != observed[key]:
                mismatches.append({"case": name, "field": key, "expected": value, "actual": observed[key]})
        report = {"name": name, "stratum": entry["stratum"], "native_file_sha256": digest(native_path.read_bytes()),
                  "all_checked_fields_match": not any(x["case"] == name for x in mismatches),
                  "rows": len(dirty), "cells": len(dirty) * len(header), "raw_labels": len(raw_gold), "native_labels": len(gold),
                  "normalization_removed_labels": len(set(raw_gold) - set(gold)), "normalization_added_labels": len(set(gold) - set(raw_gold)),
                  "nonidempotent_dirty_values": len(difference(n_dirty, nn_dirty)), "nonidempotent_clean_values": len(difference(n_clean, nn_clean)),
                  "roundtrip_removed_labels": len(set(gold) - set(twice_gold)), "roundtrip_added_labels": len(set(twice_gold) - set(gold)),
                  "roundtrip_common_target_changes": len(target_drift),
                  "native_clean_probe": score(probes["native_coordinates_native_clean"], gold),
                  "raw_clean_probe": score(probes["native_coordinates_raw_clean"], gold),
                  "raw_coordinates_native_clean_probe": score(probes["raw_coordinates_native_clean"], gold)}
        all_reports.append(report)
        print("INDEPENDENT_CASE", name, json.dumps(report, sort_keys=True), flush=True)
    counts = ["rows", "cells", "raw_labels", "native_labels", "normalization_removed_labels", "normalization_added_labels", "nonidempotent_dirty_values", "nonidempotent_clean_values", "roundtrip_removed_labels", "roundtrip_added_labels", "roundtrip_common_target_changes"]
    strata = {}
    for stratum in ["default_benchmark", "scale_extension", "toy_control"]:
        selected = [r for r in all_reports if r["stratum"] == stratum]
        strata[stratum] = {"datasets": [r["name"] for r in selected], **{key: sum(r[key] for r in selected) for key in counts}}
    receipt = {"status": "PASS" if len(all_reports) == 7 and not mismatches else "FAIL",
               "started_at_utc": started, "finished_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "python": sys.version, "verifier_sha256": digest(Path(__file__).read_bytes()),
               "source_manifest_sha256": digest((ROOT / "restoration_manifest.json").read_bytes()),
               "protocol_sha256": digest((ROOT / "PROTOCOL_FROZEN.md").read_bytes()),
               "upstream_program_imported_by_verifier": False, "pandas_imported_by_verifier": False,
               "strata": strata, "cases": all_reports, "mismatches": mismatches}
    (ROOT / "results" / "independent_verification.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print("INDEPENDENT_VERIFICATION_" + receipt["status"], flush=True)
    if receipt["status"] != "PASS":
        sys.exit(1)


if __name__ == "__main__":
    main()
