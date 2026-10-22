# One current author-constructed software example

The current input matches a literal author-defined edge with qualifier `offset_window="1 month"`. The supplied declaration instead asserts `complete=true` and `offset_window="2 months"`. The copied current repairer receives that wrong authority; the copied independent checker receives the same task and the produced patch. Neither receives the original-intent definition. Both strings are opaque qualifiers here: no calendar semantics, dbt/MetricFlow execution, or real business judgment is tested.

This example checks that an output can be valid relative to the supplied authority while differing from the original defined by the construction. It demonstrates the authority boundary, not a checker implementation defect or an independently verified business error. All names, values, declarations and registry entries in `author_case.json` were written for this example. No third-party raw, external data, or upstream code execution is involved.

Run from any working directory with Python 3.9 or newer:

```sh
python3 -B /absolute/path/to/software_example/run_example.py
```

The script reads only sibling input/manifest/copied author modules and the Python standard library. It never opens the historical source paths named by the manifest. It checks the copied module hashes, runs one `patch` and one `check`, and writes its output beside the script. The output files are `input_task.json`, `patch_result.json`, `check_result.json`, `original_comparison.json`, `execution_receipt.json`, and `result_summary.json`. A later invocation replaces these example outputs with a new execution receipt; the functional result should remain the same.

`result_summary.json` is a small author-only record for a separate `current_software_examples` ledger. `execution_status=PASS` means the specified software witness occurred; it does not establish business truth. Expected fields are `checker_valid=true`, `output_matches_supplied_authority_projection=true`, `output_matches_constructed_original=false`, and `business_truth="UNKNOWN"`. One occurrence is removed and one added.

Do not add this case to the old 32,946 diagnostic calls, 854 basic tasks, or 144 extensions. It is one newly executed tiny software example, with no new external event or natural-defect observation. `code_manifest.json` also cites the legacy `v4_robustness_receipt.json` negative example by path/hash/pointer as historical context. That legacy receipt is not relabeled as a current execution; the new patch/check files provide the current evidence.
