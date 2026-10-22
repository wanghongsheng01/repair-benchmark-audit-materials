#!/usr/bin/env python3
"""Run one author-constructed current boundary example (stdlib only).

All inputs, copied author modules, and outputs are siblings of this script.
No , upstream source, network, original data, or previous results are read.
The original intent is a literal author definition, not business gold.
"""
from __future__ import annotations

import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import sys
import time

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)


def digest_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def save(name, value):
    path = HERE / name
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2,
                               allow_nan=False) + "\n", encoding="utf-8")
    return {"path": name, "sha256": digest_file(path), "bytes": path.stat().st_size}


def load_author_module(name):
    path = HERE / name
    spec = importlib.util.spec_from_file_location("tiny_example_" + path.stem, path)
    require(spec is not None and spec.loader is not None, "missing sibling module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    timer = time.perf_counter_ns()
    manifest_path = HERE / "code_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    require({x["local_path"] for x in manifest["author_code"]} ==
            {"reference_repair.py", "verify_certificate.py"},
            "unexpected author module inventory")
    code_hashes = {}
    for source in manifest["author_code"]:
        path = HERE / source["local_path"]
        require(path.parent == HERE and digest_file(path) == source["sha256"] and
                path.stat().st_size == source["bytes"], "copied author code changed")
        code_hashes[source["local_path"]] = digest_file(path)

    case_path = HERE / "author_case.json"
    case_hash = digest_file(case_path)
    case = json.loads(case_path.read_text(encoding="utf-8"))
    require(case["schema"] == "audit-author-constructed-wrong-authority-case",
            "unexpected example schema")
    task = case["task_with_incorrect_asserted_authority"]
    original = case["constructed_original"]["expected_edges"]
    asserted_projection = case["constructed_asserted_authority_projection"]
    require(case["constructed_original"]["definition_basis"] ==
            "author_literal_definition_only", "original-intent scope changed")
    require(task["contract"]["complete"] is True, "example must assert complete")
    require(canonical(task["current_edges"]) == canonical(original),
            "current input must match the author's constructed original")
    require(canonical(original) != canonical(asserted_projection),
            "example must distinguish original from asserted authority")
    input_snapshot = canonical(task)
    original_snapshot = canonical(original)
    repair = load_author_module("reference_repair.py")
    checker = load_author_module("verify_certificate.py")

    prediction = repair.patch(task)
    verdict = checker.check(task, prediction)
    require(canonical(task) == input_snapshot, "patch/check mutated the input")
    require(canonical(original) == original_snapshot, "original definition mutated")
    require(digest_file(case_path) == case_hash, "case file changed during execution")

    certificate = prediction["certificate"]
    comparison = {
        "original_intent_basis": "author_literal_definition_only",
        "current_matches_constructed_original": canonical(task["current_edges"]) == canonical(original),
        "output_matches_constructed_original": canonical(prediction["edges"]) == canonical(original),
        "output_matches_constructed_asserted_authority_projection": canonical(prediction["edges"]) == canonical(asserted_projection),
        "output_differs_from_current": canonical(prediction["edges"]) != canonical(task["current_edges"]),
        "input_unchanged_by_patch_and_checker": canonical(task) == input_snapshot,
        "original_qualifier": original[0]["qualifiers"],
        "asserted_qualifier": task["contract"]["metric"]["type_params"]["metrics"][0]["offset_window"],
        "output_qualifier": prediction["edges"][0]["qualifiers"],
        "removed_occurrences": len(certificate["removed"]),
        "added_occurrences": len(certificate["added"]),
        "preserved_occurrences": len(certificate["preserved"]),
        "business_truth": "UNKNOWN",
    }
    require(prediction["answered"] is True and prediction["reason"] == "RESOLVED",
            "constructed example did not resolve")
    require(certificate["schema"] == "REFERENCE_OCCURRENCE_CERTIFICATE_V3",
            "not a current certificate")
    require(verdict == {"valid": True, "protocol_status": "RESOLVED", "failure": None},
            "current checker did not accept the constructed output")
    require(comparison["output_matches_constructed_asserted_authority_projection"] and
            not comparison["output_matches_constructed_original"] and
            comparison["output_differs_from_current"], "boundary witness absent")
    elapsed = time.perf_counter_ns() - timer
    artifacts = [save("input_task.json", task), save("patch_result.json", prediction),
                 save("check_result.json", verdict), save("original_comparison.json", comparison)]
    code_hashes["run_example.py"] = digest_file(Path(__file__).resolve())
    receipt = {
        "schema": "audit-current-software-example-execution-v1",
        "started_at_utc": started,
        "finished_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "invocation_argv": [sys.executable, *sys.argv],
        "working_directory": str(Path.cwd()),
        "portable_command": "python3 -B /absolute/path/to/software_example/run_example.py",
        "python": platform.python_version(),
        "diagnostic_elapsed_ns": elapsed,
        "timing_scope": "One local functional execution including input checks and imports; not a performance benchmark.",
        "case_sha256": case_hash,
        "code_manifest_sha256": digest_file(manifest_path),
        "code_sha256": code_hashes,
        "code_hashes_match_copied_author_manifest": True,
        "same_supplied_task_passed_to_patch_and_checker": True,
        "original_definition_passed_to_patch_or_checker": False,
        "source_read_boundary": "Sibling author_case.json, code_manifest.json and copied author modules only; standard-library imports also occur.",
        "v6_source_files_read_during_execution": False,
        "network_used": False,
        "third_party_raw_used": False,
        "new_external_events": 0,
        "constructed_software_examples": 1,
        "artifacts": artifacts,
    }
    receipt_ref = save("execution_receipt.json", receipt)
    summary = {
        "schema": "audit-current-software-example-summary",
        "case_id": case["case_id"],
        "family": "current_software_examples",
        "case_origin": "fully_author_constructed",
        "execution_status": "PASS",
        "certificate_schema": certificate["schema"],
        "asserted_authority_complete": task["contract"]["complete"],
        "patch_answered": prediction["answered"],
        "checker_valid": verdict["valid"],
        "checker_protocol_status": verdict["protocol_status"],
        "checker_failure": verdict["failure"],
        "current_matches_constructed_original": comparison["current_matches_constructed_original"],
        "output_matches_constructed_original": comparison["output_matches_constructed_original"],
        "output_matches_supplied_authority_projection": comparison["output_matches_constructed_asserted_authority_projection"],
        "output_differs_from_current": comparison["output_differs_from_current"],
        "original_intent_basis": "author_literal_definition_only",
        "business_truth": "UNKNOWN",
        "removed_occurrences": comparison["removed_occurrences"],
        "added_occurrences": comparison["added_occurrences"],
        "preserved_occurrences": comparison["preserved_occurrences"],
        "interpretation": "The current checker accepts consistency with the same supplied but deliberately wrong qualifier authority, while the output differs from the author's literal original definition. This is the intended authority boundary, not evidence of an implementation defect.",
        "constructed_examples": 1,
        "new_external_events": 0,
        "pooled_with_legacy_32946_854_144": False,
        "third_party_raw_used": False,
        "code_sha256": code_hashes,
        "source_refs": [{"path": "author_case.json", "sha256": case_hash},
                        {"path": "code_manifest.json", "sha256": digest_file(manifest_path)},
                        receipt_ref, *artifacts],
        "legacy_context_only": manifest["legacy_context_only"],
    }
    summary_ref = save("result_summary.json", summary)
    print(json.dumps({"execution_status": "PASS", "result_summary": summary_ref,
                      "checker_valid": verdict["valid"],
                      "output_matches_constructed_original": comparison["output_matches_constructed_original"]}))


if __name__ == "__main__":
    main()
