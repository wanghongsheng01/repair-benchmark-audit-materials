#!/usr/bin/env python3
"""Execute only the inspected official Dataset module on the frozen corpus."""
import csv
import datetime
import hashlib
import importlib.util
import json
import platform
from pathlib import Path
import sys
import traceback

import pandas

ROOT = Path(__file__).resolve().parent
SOURCE_HASH = "43805c3daeca0addeed1ca1b8fb4927ccedf6b98994856deea93dc0c4756ac1b"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def coords_hash(coords):
    h = hashlib.sha256()
    for i, j in sorted(coords):
        h.update((str(i) + "," + str(j) + "\n").encode())
    return h.hexdigest()


def target_hash(dictionary):
    h = hashlib.sha256()
    for (i, j), value in sorted(dictionary.items()):
        h.update((str(i) + "," + str(j) + ":" + sha(value.encode("utf-8")) + "\n").encode())
    return h.hexdigest()


def table_hash(headers, rows):
    h = hashlib.sha256()
    for row in [headers] + list(rows):
        h.update((json.dumps(list(row), ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8"))
    return h.hexdigest()


def read_raw(path):
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))
    header = rows.pop(0)
    if not header or len(set(header)) != len(header):
        raise ValueError("Empty/duplicate CSV headers")
    if any(len(row) != len(header) for row in rows):
        raise ValueError("Ragged or empty CSV record")
    return header, rows


def map_summary(d):
    return {"count": len(d), "coordinates_sha256": coords_hash(d), "target_values_sha256": target_hash(d)}


def label_delta(a, b):
    left, right = set(a), set(b)
    removed, added = left - right, right - left
    return {"before_count": len(left), "after_count": len(right), "common_count": len(left & right),
            "removed_count": len(removed), "added_count": len(added),
            "removed_coordinates_sha256": coords_hash(removed), "added_coordinates_sha256": coords_hash(added),
            "removed_rows": len({i for i, j in removed}), "added_rows": len({i for i, j in added}),
            "removed_columns": sorted({j for i, j in removed}), "added_columns": sorted({j for i, j in added}),
            "jaccard": 1.0 if not (left | right) else len(left & right) / len(left | right)}


def changed_values(before, after):
    changes = [(i, j) for i, (a, b) in enumerate(zip(before, after)) for j, (x, y) in enumerate(zip(a, b)) if x != y]
    return {"count": len(changes), "coordinates_sha256": coords_hash(changes),
            "rows": len({i for i, j in changes}), "columns": sorted({j for i, j in changes})}


def run_case(Dataset, entry):
    name = entry["name"]
    paths = {kind: ROOT / "local_source" / "datasets" / name / (kind + ".csv") for kind in ["dirty", "clean"]}
    hd, rawd = read_raw(paths["dirty"])
    hc, rawc = read_raw(paths["clean"])
    if len(hd) != len(hc) or len(rawd) != len(rawc):
        raise ValueError("Raw pair shape mismatch")
    d = Dataset({"name": name, "path": str(paths["dirty"]), "clean_path": str(paths["clean"])})
    if list(d.dataframe.columns) != hd or list(d.clean_dataframe.columns) != hc or tuple(d.dataframe.shape) != (len(rawd), len(hd)) or d.dataframe.shape != d.clean_dataframe.shape:
        raise ValueError("Native parser shape/header disagrees with raw parser")
    nd = list(d.dataframe.itertuples(index=False, name=None))
    nc = list(d.clean_dataframe.itertuples(index=False, name=None))
    raw_errors = {(i, j): rawc[i][j] for i in range(len(rawd)) for j in range(len(hd)) if rawd[i][j] != rawc[i][j]}
    native_errors = d.get_actual_errors_dictionary()
    result = {"name": name, "stratum": entry["stratum"], "status": "completed",
              "rows": len(rawd), "columns": len(hd), "cells_per_pair_side": len(rawd) * len(hd), "headers": hd,
              "clean_headers": hc, "header_names_equal": hd == hc,
              "identity": "Official evaluator uses row/column positions; independent real-entity row identity is not certified.",
              "na_policy": "dtype=str, keep_default_na=False; empty strings retained by native loader",
              "raw_dirty_table_sha256": table_hash(hd, rawd), "raw_clean_table_sha256": table_hash(hc, rawc),
              "native_dirty_table_sha256": table_hash(hd, nd), "native_clean_table_sha256": table_hash(hc, nc),
              "E1": {"raw_labels": map_summary(raw_errors), "native_labels": map_summary(native_errors),
                     "label_delta": label_delta(raw_errors, native_errors),
                     "dirty_raw_to_native": changed_values(rawd, nd), "clean_raw_to_native": changed_values(rawc, nc)}}
    out = ROOT / "local_roundtrip" / name
    out.mkdir(parents=True, exist_ok=True)
    Dataset.write_csv_dataset(str(out / "dirty.csv"), d.dataframe)
    Dataset.write_csv_dataset(str(out / "clean.csv"), d.clean_dataframe)
    dd = Dataset({"name": name + "_roundtrip", "path": str(out / "dirty.csv"), "clean_path": str(out / "clean.csv")})
    rd = list(dd.dataframe.itertuples(index=False, name=None))
    rc = list(dd.clean_dataframe.itertuples(index=False, name=None))
    roundtrip_errors = dd.get_actual_errors_dictionary()
    value_drift = {key: roundtrip_errors[key] for key in set(native_errors) & set(roundtrip_errors) if native_errors[key] != roundtrip_errors[key]}
    result["E2"] = {"native_export_api": "Dataset.write_csv_dataset",
                    "native_reload_api": "Dataset.__init__ / read_csv_dataset",
                    "dirty_value_changes": changed_values(nd, rd), "clean_value_changes": changed_values(nc, rc),
                    "reloaded_dirty_table_sha256": table_hash(hd, rd), "reloaded_clean_table_sha256": table_hash(hc, rc),
                    "reloaded_labels": map_summary(roundtrip_errors), "label_delta": label_delta(native_errors, roundtrip_errors),
                    "common_error_target_changes": map_summary(value_drift),
                    "export_files": {k: {"bytes": (out / (k + ".csv")).stat().st_size, "sha256": sha((out / (k + ".csv")).read_bytes())} for k in ["dirty", "clean"]}}
    probes = {
        "native_coordinates_native_clean": dict(native_errors),
        "native_coordinates_raw_clean": {key: rawc[key[0]][key[1]] for key in native_errors},
        "raw_coordinates_raw_clean": raw_errors,
        "raw_coordinates_native_clean": {key: nc[key[0]][key[1]] for key in raw_errors},
    }
    result["E3"] = {}
    for label, probe in probes.items():
        row = {"dictionary": map_summary(probe), "native_scores": d.get_data_cleaning_evaluation(probe)}
        if label.startswith("native_coordinates_"):
            d.create_repaired_dataset(probe)
            materialized = d.get_correction_dictionary()
            row["materialized_dictionary"] = map_summary(materialized)
            row["materialized_native_scores"] = d.get_data_cleaning_evaluation(materialized)
            row["direct_to_materialized_label_delta"] = label_delta(probe, materialized)
            row["common_target_changes"] = sum(probe[key] != materialized[key] for key in set(probe) & set(materialized))
        result["E3"][label] = row
    result["E4"] = {}
    for kind in ["dirty", "clean"]:
        selfpair = Dataset({"name": name + "_self_" + kind, "path": str(paths[kind]), "clean_path": str(paths[kind])})
        result["E4"][kind + "_self_pair"] = {"labels": map_summary(selfpair.get_actual_errors_dictionary()),
                                                "empty_probe_scores": selfpair.get_data_cleaning_evaluation({})}
    expected = [1.0] * 6 if native_errors else [0.0] * 6
    result["E4"]["normalized_oracle_expected_scores"] = expected
    result["E4"]["normalized_oracle_pass"] = result["E3"]["native_coordinates_native_clean"]["native_scores"] == expected
    return result


def main():
    source = ROOT / "local_source" / "raha" / "dataset.py"
    if sha(source.read_bytes()) != SOURCE_HASH:
        raise RuntimeError("Reviewed source identity mismatch")
    # Only this previously inspected file; never import upstream package __init__.
    spec = importlib.util.spec_from_file_location("reviewed_raha_dataset", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    proposal = json.loads((ROOT / "raha_candidate_protocol_proposal.json").read_text())
    output = ROOT / "results"
    output.mkdir(exist_ok=True)
    records = []
    for entry in proposal["roster"]:
        name = entry["name"]
        started = datetime.datetime.now(datetime.timezone.utc).isoformat()
        try:
            record = run_case(module.Dataset, entry)
        except Exception as exc:
            record = {"name": name, "stratum": entry["stratum"], "status": "failed", "error": repr(exc), "traceback": traceback.format_exc()}
        record["started_at_utc"] = started
        record["finished_at_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        (output / (name + "_native.json")).write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
        records.append(record)
        print("NATIVE_CASE", name, record["status"], json.dumps(record.get("E1", {}).get("label_delta", {})), flush=True)
    summary = {"official_source_sha256": SOURCE_HASH, "python": sys.version, "pandas": pandas.__version__,
               "platform": platform.platform(), "native_harness_sha256": sha(Path(__file__).read_bytes()),
               "protocol_sha256": sha((ROOT / "PROTOCOL_FROZEN.md").read_bytes()),
               "implementation_note_sha256": sha((ROOT / "IMPLEMENTATION_PRE_DATA.md").read_bytes()),
               "case_count": len(records), "completed": sum(r["status"] == "completed" for r in records),
               "case_files": [r["name"] + "_native.json" for r in records],
               "finished_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    (output / "native_execution_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    if summary["completed"] != summary["case_count"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
