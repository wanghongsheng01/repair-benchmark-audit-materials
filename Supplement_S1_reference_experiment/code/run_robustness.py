#!/usr/bin/env python3
"""Portable, per-case protocol regression and saved-record replay (stdlib).

Default inputs/output are within the adjacent public_artifact directory. There
are no ancestor-source dependencies. This does not execute upstream programs,
access a network, create business labels, or assert natural-defect accuracy.
"""
from __future__ import annotations
import argparse
import collections
import copy
import datetime
import hashlib
import json
import platform
from pathlib import Path

from reference_repair import canonical, digest, ordered, patch, rebuild
from verify_certificate import check, verify


def load_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def apply_operations(value, operations):
    """Replay deterministic interventions; paths are JSON key/index arrays."""
    value = copy.deepcopy(value)
    for operation in operations:
        cursor = value
        for key in operation["path"][:-1]:
            cursor = cursor[key]
        key = operation["path"][-1]
        if operation["op"] == "set":
            cursor[key] = copy.deepcopy(operation["value"])
        elif operation["op"] == "delete":
            del cursor[key]
        elif operation["op"] == "append":
            cursor[key].append(copy.deepcopy(operation["value"]))
        else:
            raise ValueError("unknown intervention")
    return value


def put(path, value):
    return {"op": "set", "path": path, "value": value}


def remove(path):
    return {"op": "delete", "path": path}


def append(path, value):
    return {"op": "append", "path": path, "value": value}


def _sha_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inputs(directory):
    mutation_path, clean_path = directory / "tasks.jsonl", directory / "clean_controls.jsonl"
    mutations, clean = load_jsonl(mutation_path), load_jsonl(clean_path)
    tasks = mutations + clean
    if len(mutations) != 696 or len(clean) != 158 or len({t["task_id"] for t in tasks}) != 854:
        raise ValueError("expected exactly 696 mutations and 158 unique clean controls")
    return tasks, [{"file": path.name, "sha256": _sha_file(path), "bytes": path.stat().st_size} for path in (mutation_path, clean_path)]


def wrong_certificate(task, target, template):
    """Coherent arithmetic for deliberately false E, with correct D/R/G hashes."""
    prediction = copy.deepcopy(template)
    before = collections.Counter(map(canonical, task["current_edges"]))
    after = collections.Counter(map(canonical, target))
    expand = lambda counts: ordered([json.loads(k) for k, n in counts.items() for _ in range(n)])
    prediction["edges"] = target
    prediction["certificate"].update(removed=expand(before-after), added=expand(after-before), preserved=expand(before&after))
    return prediction


def run(input_dir, output_dir):
    tasks, fingerprints = inputs(input_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    code_dir = Path(__file__).resolve().parent
    code_hashes = {name: _sha_file(code_dir / name) for name in ("reference_repair.py", "verify_certificate.py", "run_robustness.py")}
    code_set = digest(code_hashes)
    counts = collections.defaultdict(collections.Counter)
    streams = {name: (output_dir / (name + ".jsonl")).open("w", encoding="utf-8")
               for name in ("valid_cases", "extended_cases", "refusal_cases", "tamper_cases", "idempotence_cases", "gold_independence_cases")}
    ids = set()
    edit_volume = collections.Counter()

    def save(family, base, kind, operations, prediction, expected_valid, **extra):
        case_id = family + "/" + base["task_id"] + "/" + kind
        if case_id in ids:
            raise ValueError("duplicate case ID: " + case_id)
        ids.add(case_id)
        altered = apply_operations(base, operations)
        verdict = check(altered, prediction)
        if verdict["valid"] is not expected_valid:
            raise AssertionError((case_id, verdict))
        row = {"case_id": case_id, "base_id": base["task_id"], "kind": kind,
               "task_operations": operations, "input_sha256": digest(altered),
               "prediction": prediction, "expected_valid": expected_valid,
               "checker": verdict, "code_set_sha256": code_set, **extra}
        streams[family + "_cases"].write(canonical(row) + "\n")
        counts[family][kind] += 1
        return row

    try:
        for task in tasks:
            snapshot = canonical(task)
            prediction, direct = patch(task), rebuild(task)
            if ordered(prediction["edges"]) != ordered(task["gold_edges"]) or ordered(direct["edges"]) != ordered(task["gold_edges"]):
                raise AssertionError("public gold mismatch: " + task["task_id"])
            if canonical(task) != snapshot:
                raise AssertionError("repair mutated caller input")
            save("valid", task, "ordinary", [], prediction, True, direct_rebuild=direct,
                 patch_exact=True, rebuild_exact=True)
            if task["mutation"] != "clean":
                for key in ("added", "removed", "preserved"):
                    edit_volume[key] += len(prediction["certificate"][key])
                edit_volume["rebuilt_output_occurrences"] += len(task["gold_edges"])

            again_ops = [put(["current_edges"], prediction["edges"])]
            again = patch(apply_operations(task, again_ops))
            if ordered(again["edges"]) != ordered(prediction["edges"]):
                raise AssertionError("idempotence failed")
            save("idempotence", task, "output_as_input", again_ops, again, True)
            save("gold_independence", task, "poisoned_saved_gold", [put(["gold_edges"], [])], prediction, True)

            # One occurrence removed; all ordinary targets are nonempty.
            bad = copy.deepcopy(prediction)
            part = "added" if bad["certificate"]["added"] else "preserved"
            bad["certificate"][part].pop()
            save("tamper", task, "deleted_certificate_occurrence", [], bad, False)
            save("tamper", task, "changed_registry_metadata", [put(["registry", "untrusted_extra"], True)], prediction, False)
            observed = {"role": "extra", "target": "metric:constructed_extra", "qualifiers": {}}
            save("tamper", task, "changed_observed_adjacency", [append(["current_edges"], observed)], prediction, False)
            for kind, path, value in (
                ("wrong_schema", ["certificate", "schema"], "REFERENCE_OCCURRENCE_CERTIFICATE_V2"),
                ("wrong_rule", ["certificate", "rule"], "UNSPECIFIED_RULE"),
                ("wrong_reason", ["reason"], "NOT_RESOLVED"),
                ("wrong_answered", ["answered"], False),
                ("wrong_certificate_identity", ["certificate", "metric"], "constructed_other_metric"),
                ("wrong_output", ["edges"], []),
            ):
                save("tamper", task, kind, [], apply_operations(prediction, [put(path, value)]), False)
            false_target = ordered(task["gold_edges"] + [observed])
            save("tamper", task, "coherent_false_projection", [], wrong_certificate(task, false_target, prediction), False)

            refusal_recipes = []
            for label, value in (("false", False), ("null", None), ("integer_one", 1), ("string_true", "True")):
                refusal_recipes.append(("completeness_"+label, [put(["contract", "complete"], value)], "INCOMPLETE_AUTHORITY"))
            refusal_recipes.extend([
                ("completeness_omitted", [remove(["contract", "complete"])], "INCOMPLETE_AUTHORITY"),
                ("missing_required_declaration_fields", [remove(["contract", "metric", "type_params"])], "MALFORMED_AUTHORITY"),
                ("unsupported_type", [put(["contract", "metric", "type"], "not_a_supported_type")], "UNSUPPORTED"),
                ("metric_identity_mismatch", [put(["metric_id"], "constructed_other_metric")], "METRIC_IDENTITY_MISMATCH"),
                ("duplicate_metric_registry_identity", [append(["registry", "metrics"], task["registry"]["metrics"][0])], "DUPLICATE_REGISTRY_IDENTITY"),
                ("malformed_observed_adjacency", [put(["current_edges"], "not_an_edge_list")], "MALFORMED_TASK"),
            ])
            first = task["gold_edges"][0]["target"]
            if first.startswith("metric:"):
                remaining = [n for n in task["registry"]["metrics"] if n != first[7:]]
                refusal_recipes.append(("missing_registry_target", [put(["registry", "metrics"], remaining)], "NONUNIQUE_BINDING"))
            else:
                name = next(n for n, targets in task["registry"]["measures"].items() if first in targets)
                lookup = ["registry", "measures", name]
                refusal_recipes.extend([
                    ("missing_registry_target", [put(lookup, [])], "NONUNIQUE_BINDING"),
                    ("ambiguous_measure_registry", [append(lookup, "measure:constructed_alternative." + name)], "NONUNIQUE_BINDING"),
                    ("empty_measure_target", [put(lookup, [""])], "INVALID_TYPED_TARGET"),
                    ("wrong_type_measure_target", [put(lookup, ["metric:" + name])], "INVALID_TYPED_TARGET"),
                    ("duplicate_measure_registry_identity", [append(lookup, first)], "DUPLICATE_REGISTRY_IDENTITY"),
                ])
            for kind, operations, reason in refusal_recipes:
                altered = apply_operations(task, operations)
                snapshot = canonical(altered)
                refusal, refused_rebuild = patch(altered), rebuild(altered)
                if refusal["answered"] is not False or refusal["reason"] != reason or canonical(refusal["edges"]) != canonical(altered["current_edges"]):
                    raise AssertionError((task["task_id"], kind, refusal))
                if refused_rebuild != refusal or canonical(altered) != snapshot:
                    raise AssertionError("refusal failed preservation/rebuild agreement")
                save("refusal", task, kind, operations, refusal, True, direct_rebuild=refused_rebuild,
                     expected_reason=reason, input_preserved=True)
                forged = copy.deepcopy(prediction)
                forged["certificate"]["authority_digest"] = digest({"contract": altered["contract"], "registry": altered["registry"]})
                # Rehash the changed evidence to recreate the old audit counterexample.
                forged["certificate"]["metric"] = altered["metric_id"]
                if isinstance(altered["current_edges"], list):
                    forged["certificate"]["observed_adjacency_digest"] = digest(ordered(altered["current_edges"]))
                save("tamper", task, "forged_success_after_" + kind, operations, forged, False)

            if task["mutation"] == "clean" and len(task["gold_edges"]) >= 2:
                variants = {"all_deleted": [],
                            "all_roles_corrupted": [dict(edge, role="constructed_wrong_role") for edge in task["gold_edges"]],
                            "all_occurrences_duplicated": task["gold_edges"] * 2}
                for kind, observed_edges in variants.items():
                    operations = [put(["current_edges"], observed_edges)]
                    altered = apply_operations(task, operations)
                    extended, rebuilt = patch(altered), rebuild(altered)
                    if ordered(extended["edges"]) != ordered(task["gold_edges"]) or ordered(rebuilt["edges"]) != ordered(task["gold_edges"]):
                        raise AssertionError("extended gold mismatch")
                    save("extended", task, kind, operations, extended, True, direct_rebuild=rebuilt,
                         patch_exact=True, rebuild_exact=True)
    finally:
        for stream in streams.values():
            stream.close()
    if counts["valid"]["ordinary"] != 854 or dict(counts["extended"]) != {"all_deleted": 48, "all_roles_corrupted": 48, "all_occurrences_duplicated": 48}:
        raise AssertionError("unexpected valid/extended denominators")
    files = {name + ".jsonl": {"sha256": _sha_file(output_dir / (name + ".jsonl")),
                               "records": sum(counts[name.replace("_cases", "")].values())}
             for name in streams}
    summary = {"schema": "AUDIT_V5_PROTOCOL_REGRESSION_RECEIPT", "executed_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "inputs": fingerprints, "code_sha256": code_hashes, "code_set_sha256": code_set,
               "unique_cases": len(ids), "case_counts": {key: dict(value) for key, value in counts.items()},
               "mutation_edit_volume": dict(edit_volume), "files": files,
               "python": platform.python_version(), "machine": platform.machine(), "system": platform.system(),
               "input_files_unchanged": all(_sha_file(input_dir / row["file"]) == row["sha256"] for row in fingerprints),
               "scope": "deterministic implementation regression; reused declarations; no independent business gold, natural defects, or performance conclusion"}
    (output_dir / "robustness_receipt.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def replay_saved(input_dir, output_dir):
    """Recheck all saved cases without calling patch, rebuild, or a resolver."""
    tasks, fingerprints = inputs(input_dir)
    by_id = {task["task_id"]: task for task in tasks}
    receipt = json.loads((output_dir / "robustness_receipt.json").read_text())
    if fingerprints != receipt["inputs"]:
        raise ValueError("input fingerprint mismatch")
    code_dir = Path(__file__).resolve().parent
    for name, expected_hash in receipt["code_sha256"].items():
        if _sha_file(code_dir / name) != expected_hash:
            raise ValueError("checker/runner source fingerprint mismatch: " + name)
    required_files = {"valid_cases.jsonl": 854, "extended_cases.jsonl": 144,
                      "refusal_cases.jsonl": 10850, "tamper_cases.jsonl": 19390,
                      "idempotence_cases.jsonl": 854, "gold_independence_cases.jsonl": 854}
    if {name: facts["records"] for name, facts in receipt["files"].items()} != required_files:
        raise ValueError("frozen regression suite denominator mismatch")
    unique, counts = set(), collections.Counter()
    valid_base_ids = set()
    extended_base_ids = collections.defaultdict(set)
    for name, facts in receipt["files"].items():
        path = output_dir / name
        if _sha_file(path) != facts["sha256"]:
            raise ValueError("saved record hash mismatch: " + name)
        records = load_jsonl(path)
        if len(records) != facts["records"]:
            raise ValueError("saved record denominator mismatch")
        for row in records:
            if row["case_id"] in unique:
                raise ValueError("duplicate saved case")
            unique.add(row["case_id"])
            task = apply_operations(by_id[row["base_id"]], row["task_operations"])
            if digest(task) != row["input_sha256"] or row["code_set_sha256"] != receipt["code_set_sha256"]:
                raise ValueError("saved input/code identity mismatch")
            verdict = check(task, row["prediction"])
            if verdict != row["checker"] or verdict["valid"] is not row["expected_valid"]:
                raise ValueError("saved protocol verdict mismatch: " + row["case_id"])
            if row.get("patch_exact") and ordered(row["prediction"]["edges"]) != ordered(task["gold_edges"]):
                raise ValueError("saved patch gold mismatch")
            if row.get("rebuild_exact") and ordered(row["direct_rebuild"]["edges"]) != ordered(task["gold_edges"]):
                raise ValueError("saved rebuild gold mismatch")
            if name == "valid_cases.jsonl":
                valid_base_ids.add(row["base_id"])
            if name == "extended_cases.jsonl":
                extended_base_ids[row["kind"]].add(row["base_id"])
            counts[name] += 1
    if len(unique) != receipt["unique_cases"]:
        raise ValueError("case total mismatch")
    if valid_base_ids != set(by_id):
        raise ValueError("ordinary case input coverage mismatch")
    multi_ids = {task["task_id"] for task in tasks if task["mutation"] == "clean" and len(task["gold_edges"]) >= 2}
    if dict(extended_base_ids) != {kind: multi_ids for kind in ("all_deleted", "all_roles_corrupted", "all_occurrences_duplicated")}:
        raise ValueError("extended case input coverage mismatch")
    result = {"status": "PASS", "unique_cases": len(unique), "file_counts": dict(counts),
              "checker": "verify_certificate.check", "calls_patch_or_rebuild": False}
    (output_dir / "saved_records_recheck.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    local_root = Path(__file__).resolve().parent.parent
    default_data = local_root / "data" if (local_root / "data").is_dir() else local_root / "public_artifact/data"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=default_data)
    parser.add_argument("--output-dir", type=Path, default=default_data.parent / "results/robustness")
    parser.add_argument("--verify-only", action="store_true")
    arguments = parser.parse_args()
    if not arguments.verify_only:
        receipt = run(arguments.input_dir, arguments.output_dir)
        print(json.dumps({key: receipt[key] for key in ("unique_cases", "case_counts", "mutation_edit_volume", "input_files_unchanged")}, indent=2))
    print(json.dumps(replay_saved(arguments.input_dir, arguments.output_dir), indent=2))


if __name__ == "__main__":
    main()
