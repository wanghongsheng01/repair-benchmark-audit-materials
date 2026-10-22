#!/usr/bin/env python3
"""CSV-only position, duplicate-preserving multiset, and exact assignment control.

No identity/event dependency. A fail-closed Python audit hook records all data
reads and allows only the eight specified clean/dirty CSVs after startup.
"""
import argparse
import csv
import encodings.utf_8_sig  # Load optional-BOM codec before the data-read guard.
import hashlib
import io
import json
import os
from pathlib import Path
import sys
from collections import Counter
from datetime import datetime, timezone
from functools import lru_cache

CASES = (
    ("employees-egtask", "emp"),
    ("employees-random-egtask", "emp"),
    ("employees-symmetrictest-egtask", "emp"),
    ("synthetic_01-egtask", "r"),
)
ENUMERATION_LIMIT = 10000


def utc():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def read_csv(path):
    data = path.read_bytes()
    rows = list(csv.reader(io.StringIO(data.decode("utf-8-sig"), newline="")))
    if not rows or len(set(rows[0])) != len(rows[0]):
        raise ValueError("Missing or duplicate header")
    header, values = rows[0], rows[1:]
    if not 1 <= len(values) <= 12 or any(len(row) != len(header) for row in values):
        raise ValueError("Expected 1..12 rectangular rows")
    return header, values, hashlib.sha256(data).hexdigest()


def exact_assignment(clean, dirty, header):
    n = len(clean)
    full = (1 << n) - 1
    cost = [[sum(a != b for a, b in zip(d, c)) for c in clean] for d in dirty]

    @lru_cache(None)
    def suffix(mask):
        if mask == full:
            return (0, 1)
        i = mask.bit_count()
        best, count = None, 0
        for j in range(n):
            if mask & (1 << j):
                continue
            rest, ways = suffix(mask | (1 << j))
            candidate = cost[i][j] + rest
            if best is None or candidate < best:
                best, count = candidate, ways
            elif candidate == best:
                count += ways
        return (best, count)

    optimal_cost, optimal_count = suffix(0)
    reachable = {0}
    prefix_count = {0: 1}
    transitions = {}
    possible_indices = [set() for _ in dirty]
    binding_counts = [Counter() for _ in dirty]
    # Numerical mask order is topological because every edge adds a bit.
    for mask in range(full + 1):
        if mask not in reachable:
            continue
        i = mask.bit_count()
        edges = []
        if mask != full:
            for j in range(n):
                if mask & (1 << j):
                    continue
                nxt = mask | (1 << j)
                if cost[i][j] + suffix(nxt)[0] == suffix(mask)[0]:
                    edges.append({"clean_row_1based": j + 1, "next_mask": nxt,
                                  "edge_hamming_cost": cost[i][j]})
                    reachable.add(nxt)
                    prefix_count[nxt] = prefix_count.get(nxt, 0) + prefix_count[mask]
                    possible_indices[i].add(j)
                    binding_counts[i][j] += prefix_count[mask] * suffix(nxt)[1]
        transitions[mask] = edges
    assert prefix_count[full] == optimal_count
    assert all(sum(counts.values()) == optimal_count for counts in binding_counts)

    cells, material = [], []
    for i, dirty_row in enumerate(dirty):
        for k, attr in enumerate(header):
            values = sorted({clean[j][k] for j in possible_indices[i]})
            labels = sorted({dirty_row[k] != value for value in values})
            cell = {"dirty_row_1based": i + 1, "attribute": attr,
                    "dirty_value": dirty_row[k], "possible_clean_target_values": values,
                    "possible_changed_labels": labels,
                    "target_value_unique": len(values) == 1,
                    "changed_label_unique": len(labels) == 1}
            cells.append(cell)
            if len(values) > 1 or len(labels) > 1:
                material.append(cell)

    enumerated = []
    if optimal_count <= ENUMERATION_LIMIT:
        def visit(mask, assignment):
            if mask == full:
                enumerated.append(assignment)
                return
            for edge in transitions[mask]:
                visit(edge["next_mask"], assignment + [edge["clean_row_1based"]])
        visit(0, [])
        assert len(enumerated) == optimal_count

    return {
        "cost_definition": "sum over all dirty rows and columns of unequal exact decoded CSV strings",
        "cost_matrix_dirty_by_clean": cost,
        "optimal_total_hamming_cost": optimal_cost,
        "optimal_assignment_count": optimal_count,
        "assignment_direction": "dirty row -> clean row; rows are 1-based data rows, header excluded",
        "dag_state_definition": "mask marks used clean rows; dirty index is popcount(mask)",
        "optimal_assignment_dag": [
            {"used_clean_mask": mask, "next_dirty_row_1based": mask.bit_count() + 1,
             "remaining_optimal_cost": suffix(mask)[0],
             "optimal_prefix_count": prefix_count[mask], "optimal_suffix_count": suffix(mask)[1],
             "edges": transitions[mask]} for mask in sorted(reachable)
        ],
        "possible_row_bindings": [
            {"dirty_row_1based": i + 1,
             "clean_rows_1based": [j + 1 for j in sorted(possible_indices[i])],
             "optimal_assignment_counts_per_clean_row": {
                 str(j + 1): binding_counts[i][j] for j in sorted(possible_indices[i])}}
            for i in range(n)
        ],
        "cell_target_and_label_support": cells,
        "all_cell_labels_unique": all(c["changed_label_unique"] for c in cells),
        "all_cell_target_values_unique": all(c["target_value_unique"] for c in cells),
        "material_ambiguity_cells": material,
        "material_ambiguity_cell_count": len(material),
        "enumeration_limit": ENUMERATION_LIMIT,
        "all_optimal_assignments_enumerated": optimal_count <= ENUMERATION_LIMIT,
        "optimal_assignments_dirty_to_clean_1based": enumerated,
    }


def analyze_case(root, case_id, table):
    clean_path = root / case_id / ("clean_" + table + ".csv")
    dirty_path = root / case_id / ("dirty_" + table + ".csv")
    ch, clean, csha = read_csv(clean_path)
    dh, dirty, dsha = read_csv(dirty_path)
    if ch != dh or len(clean) != len(dirty):
        raise ValueError("Schemas and row counts must agree")
    positional_changes = [
        {"dirty_row_1based": i + 1, "attribute": attr,
         "dirty_value": dirty[i][k], "target_value": clean[i][k]}
        for i in range(len(clean)) for k, attr in enumerate(ch)
        if clean[i][k] != dirty[i][k]
    ]
    clean_bag, dirty_bag = Counter(map(tuple, clean)), Counter(map(tuple, dirty))
    def row_counts(counter):
        return [{"row": list(row), "multiplicity": count} for row, count in sorted(counter.items())]
    return {
        "case_id": case_id, "table": table, "schema": ch,
        "rows": len(clean), "cells": len(clean) * len(ch),
        "input_sha256": {clean_path.name: csha, dirty_path.name: dsha},
        "position": {"changed_cell_count": len(positional_changes), "changes": positional_changes},
        "multiset": {"equal": clean_bag == dirty_bag,
                     "clean_minus_dirty": row_counts(clean_bag - dirty_bag),
                     "dirty_minus_clean": row_counts(dirty_bag - clean_bag),
                     "clean_unmatched_row_count": sum((clean_bag - dirty_bag).values()),
                     "dirty_unmatched_row_count": sum((dirty_bag - clean_bag).values()),
                     "cell_localization": "not provided; unequal row bags do not identify cell edits"},
        "minimum_hamming": exact_assignment(clean, dirty, ch),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    input_root = args.input_root.resolve()
    output = args.output.resolve()
    allowed = {str(input_root / case / (prefix + table + ".csv"))
               for case, table in CASES for prefix in ("clean_", "dirty_")}
    read_log = []

    def audit(event, arguments):
        if event != "open":
            return
        path, mode, flags = arguments
        if not isinstance(path, (str, bytes, os.PathLike)):
            raise PermissionError("No file-descriptor opens in the blind matcher")
        resolved = os.path.abspath(os.fsdecode(path))
        writing = flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
        if writing:
            if resolved != str(output):
                raise PermissionError("Blind matcher may write only its declared result")
        elif resolved not in allowed:
            raise PermissionError("Blind matcher read outside eight allowed CSVs: " + resolved)
        else:
            read_log.append(str(Path(resolved).relative_to(input_root)))

    started = utc()
    sys.addaudithook(audit)
    cases = [analyze_case(input_root, case, table) for case, table in CASES]
    result = {"schema_version": "audit-blind-matching/1", "started_utc": started,
              "finished_utc": utc(), "phase": "CSV-only blind matching",
              "read_access_guard": "fail-closed Python audit hook; installed after stdlib imports and before data access",
              "data_reads_in_order": read_log,
              "identity_event_reads": 0,
              "cases": cases}
    with output.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")


if __name__ == "__main__":
    main()
