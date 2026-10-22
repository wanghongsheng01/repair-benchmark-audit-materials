#!/usr/bin/env python3
"""Post-seal native-reference scoring; never changes the blind assignment DAG."""
import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

METRICS = ("tp", "fp", "fn", "tn", "label_correct", "repair_correct", "target_correct", "identity_correct_rows")


def utc():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_manifest(root, manifest):
    for entry in manifest["artifacts"]:
        assert digest(root / entry["path"]) == entry["sha256"], entry["path"]


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.reader(handle))


def native_text(cell):
    assert cell["null_reference"] is False, "Unsupported null-reference observation"
    assert isinstance(cell["text"], str)
    return cell["text"]


def ratio_bounds(bounds, key, denominator):
    values = bounds[key]
    return {"min": values["min"] / denominator if denominator else None,
            "max": values["max"] / denominator if denominator else None,
            "denominator": denominator}


def score_case(root, case):
    cid, table, header = case["case_id"], case["table"], case["schema"]
    n, cells = case["rows"], case["cells"]
    data_dir, reveal_dir = root / "inputs/blind_csv" / cid, root / "reveal" / cid
    raw_clean, raw_dirty = (read_csv(data_dir / (kind + "_" + table + ".csv")) for kind in ("clean", "dirty"))
    assert raw_clean[0] == raw_dirty[0] == header
    clean, dirty = raw_clean[1:], raw_dirty[1:]
    clean_map, dirty_map = (json.loads((reveal_dir / (kind + "_crosswalk_after_export.json")).read_text()) for kind in ("clean", "dirty"))
    assert set(clean_map) == set(dirty_map) == {table}
    cr, dr = clean_map[table], dirty_map[table]
    assert len(cr) == len(dr) == n
    assert len({r["oid"] for r in cr}) == len({r["oid"] for r in dr}) == n
    assert {r["oid"] for r in cr} == {r["oid"] for r in dr}
    for native_rows, csv_rows in ((cr, clean), (dr, dirty)):
        for native, values in zip(native_rows, csv_rows):
            assert set(native["cells"]) == set(header)
            assert [native_text(native["cells"][a]) for a in header] == values, "Export order/value disagreement"
    clean_index = {r["oid"]: j for j, r in enumerate(cr)}
    dirty_index = {r["oid"]: i for i, r in enumerate(dr)}
    native_assignment = [clean_index[r["oid"]] + 1 for r in dr]
    truth = [clean[j - 1] for j in native_assignment]
    changes = [{"dirty_row_1based": i + 1, "table": table, "oid": dr[i]["oid"],
                "attribute": a, "dirty_value": dirty[i][k], "clean_target_value": truth[i][k]}
               for i in range(n) for k, a in enumerate(header) if dirty[i][k] != truth[i][k]]
    event_objects = json.loads((reveal_dir / "events_native.json").read_text())
    events = []
    for e in event_objects:
        assert e["oid"] in dirty_index and e["attribute"] in header
        assert e["cell_ref"] == e["oid"] + "." + e["attribute"]
        events.append({"dirty_row_1based": dirty_index[e["oid"]] + 1,
                       "table": table, "oid": e["oid"], "attribute": e["attribute"],
                       "dirty_value": native_text(e["new"]), "clean_target_value": native_text(e["original"]),
                       "type": e["type"], "exported": e["exported"]})
    def event_tuple(e):
        return (e["oid"], e["attribute"], e["dirty_value"], e["clean_target_value"])
    event_counter = Counter(event_tuple(e) for e in events if e["dirty_value"] != e["clean_target_value"])
    change_counter = Counter(event_tuple(e) for e in changes)
    event_csv = read_csv(reveal_dir / "events_native.csv")
    json_export = Counter((e["oid"] + "." + e["attribute"], e["dirty_value"], e["clean_target_value"])
                          for e in events if e["exported"])
    assert Counter(map(tuple, event_csv)) == json_export, "Native event JSON/CSV disagreement"
    concordance = {"native_events_equal_observed_changes": event_counter == change_counter,
                   "event_json_csv_equal": True,
                   "unexplained_observed_changes": [list(x) for x in (change_counter - event_counter).elements()],
                   "unrealized_or_incorrect_events": [list(x) for x in (event_counter - change_counter).elements()],
                   "csv_crosswalk_order_and_values_equal": True}
    assert concordance["native_events_equal_observed_changes"], concordance

    def binding_score(i, j):
        score = dict.fromkeys(METRICS, 0)
        for k in range(len(header)):
            predicted = dirty[i][k] != clean[j][k]
            actual = dirty[i][k] != truth[i][k]
            score["tp"] += predicted and actual
            score["fp"] += predicted and not actual
            score["fn"] += not predicted and actual
            score["tn"] += not predicted and not actual
            score["label_correct"] += predicted == actual
            score["repair_correct"] += predicted and actual and clean[j][k] == truth[i][k]
            score["target_correct"] += clean[j][k] == truth[i][k]
        score["identity_correct_rows"] = int(j + 1 == native_assignment[i])
        return score

    weights = [[binding_score(i, j) for j in range(n)] for i in range(n)]
    dag = {node["used_clean_mask"]: node for node in case["minimum_hamming"]["optimal_assignment_dag"]}
    full = (1 << n) - 1

    def endpoint(metric, minimize):
        @lru_cache(None)
        def solve(mask):
            if mask == full:
                return (0, ())
            i = mask.bit_count()
            candidates = []
            for edge in dag[mask]["edges"]:
                j = edge["clean_row_1based"] - 1
                rest, witness = solve(edge["next_mask"])
                candidates.append((weights[i][j][metric] + rest, (j + 1,) + witness))
            objective = min(c[0] for c in candidates) if minimize else max(c[0] for c in candidates)
            return next(c for c in candidates if c[0] == objective)
        return solve(0)

    bounds = {}
    for metric in METRICS:
        low, lw = endpoint(metric, True)
        high, hw = endpoint(metric, False)
        bounds[metric] = {"min": low, "max": high,
                          "min_witness_dirty_to_clean_1based": list(lw),
                          "max_witness_dirty_to_clean_1based": list(hw)}
    m = case["minimum_hamming"]
    # Exhaustive enumeration is an additional cross-check when the sealed output includes it.
    if m["all_optimal_assignments_enumerated"]:
        for metric in METRICS:
            scores = [sum(weights[i][j - 1][metric] for i, j in enumerate(a))
                      for a in m["optimal_assignments_dirty_to_clean_1based"]]
            assert min(scores) == bounds[metric]["min"] and max(scores) == bounds[metric]["max"]
    actual_count = len(changes)
    predicted_count = m["optimal_total_hamming_cost"]
    rates = {"changed_label_accuracy": ratio_bounds(bounds, "label_correct", cells),
             "cell_precision": ratio_bounds(bounds, "tp", predicted_count),
             "cell_recall": ratio_bounds(bounds, "tp", actual_count),
             "repair_value_precision": ratio_bounds(bounds, "repair_correct", predicted_count),
             "repair_value_recall": ratio_bounds(bounds, "repair_correct", actual_count),
             "all_cell_target_value_accuracy": ratio_bounds(bounds, "target_correct", cells),
             "native_identity_row_accuracy": ratio_bounds(bounds, "identity_correct_rows", n)}
    position_counts = {metric: sum(weights[i][i][metric] for i in range(n)) for metric in METRICS}
    pbound = {metric: {"min": value, "max": value} for metric, value in position_counts.items()}
    position_rates = {"changed_label_accuracy": ratio_bounds(pbound, "label_correct", cells),
                      "cell_precision": ratio_bounds(pbound, "tp", case["position"]["changed_cell_count"]),
                      "cell_recall": ratio_bounds(pbound, "tp", actual_count),
                      "repair_value_precision": ratio_bounds(pbound, "repair_correct", case["position"]["changed_cell_count"]),
                      "repair_value_recall": ratio_bounds(pbound, "repair_correct", actual_count),
                      "all_cell_target_value_accuracy": ratio_bounds(pbound, "target_correct", cells)}

    def witness_with_binding(i_target, j_target):
        @lru_cache(None)
        def visit(mask):
            if mask == full:
                return ()
            i = mask.bit_count()
            for edge in dag[mask]["edges"]:
                j = edge["clean_row_1based"] - 1
                if i == i_target and j != j_target:
                    continue
                suffix = visit(edge["next_mask"])
                if suffix is not None:
                    return (j + 1,) + suffix
            return None
        answer = visit(0)
        assert answer is not None
        return list(answer)

    ambiguity_witnesses = []
    for cell in m["material_ambiguity_cells"]:
        i, k = cell["dirty_row_1based"] - 1, header.index(cell["attribute"])
        alternatives = []
        for value in cell["possible_clean_target_values"]:
            j = next(j - 1 for j in m["possible_row_bindings"][i]["clean_rows_1based"] if clean[j - 1][k] == value)
            alternatives.append({"target_value": value, "changed_label": value != dirty[i][k],
                                 "matches_native_target": value == truth[i][k],
                                 "complete_optimal_assignment_dirty_to_clean_1based": witness_with_binding(i, j)})
        ambiguity_witnesses.append({**cell, "native_target_value": truth[i][k], "alternatives": alternatives})
    native_cost = sum(m["cost_matrix_dirty_by_clean"][i][j - 1] for i, j in enumerate(native_assignment))
    unique_contradiction = m["optimal_assignment_count"] == 1 and bounds["identity_correct_rows"]["max"] != n
    return {
        "case_id": cid, "rows": n, "cells": cells,
        "native_identity_assignment": native_assignment,
        "native_dirty_oids_in_export_order": [r["oid"] for r in dr],
        "native_clean_oids_in_export_order": [r["oid"] for r in cr],
        "native_identity_cost": native_cost,
        "native_identity_is_optimal": native_cost == predicted_count,
        "native_changes": changes, "native_events": events, "native_concordance": concordance,
        "position_scores": {"counts": position_counts, "rates": position_rates},
        "multiset": {"equal": case["multiset"]["equal"], "control_false_alarm": bool(actual_count == 0 and not case["multiset"]["equal"]),
                     "cell_precision_recall": None, "reason": "Bag inequality does not provide cell localization"},
        "minimum_hamming_score_bounds": {"counts": bounds, "rates": rates},
        "all_optima_semantically_correct": bounds["label_correct"]["min"] == cells and bounds["target_correct"]["min"] == cells,
        "unique_optimum_contradicts_native_identity": unique_contradiction,
        "unique_identity_contradiction_witness": {
            "native_assignment": native_assignment,
            "unique_optimum": bounds["identity_correct_rows"]["min_witness_dirty_to_clean_1based"]} if unique_contradiction else None,
        "ambiguity_witnesses": ambiguity_witnesses,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--blind-results", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.package_root.resolve()
    seal = json.loads((root / "seals/BLIND_SEAL.json").read_text())
    verify_manifest(root, seal)
    freeze = json.loads((root / "protocol/FREEZE_A1.json").read_text())
    verify_manifest(root, freeze)
    reveal_inputs = json.loads((root / "seals/REVEAL_INPUTS.json").read_text())
    for item in reveal_inputs["sources"]:
        assert digest(root / item["path"]) == item["sha256"], item["path"]
    blind_path = args.blind_results or root / "results/blind_results.json"
    blind = json.loads(blind_path.read_text())
    started = utc()
    cases = [score_case(root, case) for case in blind["cases"]]
    result = {"schema_version": "audit-blind-reveal/1", "started_utc": started, "finished_utc": utc(),
              "blind_results_sha256": digest(blind_path), "blind_seal_sha256": digest(root / "seals/BLIND_SEAL.json"),
              "reveal_code_sha256": digest(Path(__file__)), "cases": cases,
              "conclusion": "Conventional minimum-Hamming matching suffices for all four saved observations; additional identity evidence is not necessary for their semantic labels/repair values."
              if all(c["all_optima_semantically_correct"] for c in cases)
              else "At least one case has semantic uncertainty/error under the frozen cost rule; inspect complete witnesses.",
              "total_native_events": sum(len(c["native_events"]) for c in cases),
              "total_native_changes": sum(len(c["native_changes"]) for c in cases),
              "zero_event_control_count": sum(not c["native_events"] for c in cases),
              "minimum_hamming_zero_control_false_positive_cells_max": sum(c["minimum_hamming_score_bounds"]["counts"]["fp"]["max"] for c in cases if not c["native_events"]),
              "multiset_zero_control_false_alarms": sum(c["multiset"]["control_false_alarm"] for c in cases),
              "sample_size_increase": 0}
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")


if __name__ == "__main__":
    main()
