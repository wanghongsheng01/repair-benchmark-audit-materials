# Reproduce the external consumer audit

Read `RESULTS.md`, `PROTOCOL_FROZEN.md`, `IMPLEMENTATION_PRE_DATA.md` and `A1_POSITIONAL_SCHEMA_CLARIFICATION.md` before interpreting outputs. The initial strict-header failure is retained under `initial_strict_header_attempt`; final results are under `results`. The original pre-freeze inventory proposal is preserved unchanged because the executed scripts consume its fixed roster; its historical proposed-status field does not supersede the subsequent frozen protocol and receipts.

## Inputs and boundaries

The fixed official Raha commit is `7be1334b8c7bbdac3f47ef514fb3e1e8c5fc181c`. `restoration_manifest.json` records all fourteen CSV URLs, sizes, Git blob identities and SHA-256 digests, plus the inspected official `raha/dataset.py`. Its source hash is `43805c3daeca0addeed1ca1b8fb4927ccedf6b98994856deea93dc0c4756ac1b`.

The third-party CSVs and source under `local_source`, normalized exports under `local_roundtrip`, and candidate source inspection files are local only and must not be included in a distributable archive or backup. The root Apache-2.0 license is recorded separately from unresolved per-dataset rights provenance. `candidate_source_manifest.json` retains source inspection URLs and hashes without source content. DataHub canonical registration was paused by task scope; no publication, service change, push or third-party contact occurred.

## Actual reproduction commands

Use a separate copy of this audit directory to preserve the original execution receipts. Full recomputation requires the public third-party inputs; the saved aggregates alone cannot reconstruct their values. Source acquisition makes read-only HTTPS requests to the exact pinned official URLs:

```sh
python3 restore_inputs.py --fetch
```

The downloader validates published Git blob identities and frozen SHA-256/size records. Without `--fetch` it verifies already restored files and makes no network requests. It never imports upstream source. A platform denial is a stop condition, not permission to switch identities or mirrors.

In the distributed ZIP, first run `python3 verify_package.py` to validate every manifest-listed file. An offline reviewer with a previously authorized input cache can instead restore exact source bytes using:

```sh
python3 restore_from_cache.py --cache /path/to/authorized/local_source
```

This copies only the fifteen fixed, checksum-matched input files. Cache access is an explicit prerequisite; no raw source is bundled. Full native execution still requires restoring both the official module and the fourteen CSVs. Replay rewrites runtime receipts, so verify package integrity first and retain the unmodified ZIP as the original execution record.

The native audit requires an existing Python environment with pandas supporting `DataFrame.map`. The verified execution used Python 3.9.6 and pandas 2.3.3. No dependencies were installed for this study. Review the restored native module before execution; it imports only `re`, `sys`, `html` and `pandas`. Then:

```sh
python3 replay_audit.py
```

The orchestrator runs `run_native_audit.py`, then `verify_independent.py`, records actual invocations and preserves stdout/stderr hashes. Success ends with `FROZEN_SEVEN_PAIR_AUDIT_OK`. It directly loads only the reviewed `dataset.py`; no package initializer, detector, model, generator or benchmark suite is executed. Results and native exports are written locally. `verify_independent.py` imports neither pandas nor the upstream implementation nor the native harness.

Optional explanatory witness regeneration, still without raw cell text in its output:

```sh
python3 derive_adapter_witnesses.py
```

The official normalizer passes `re.UNICODE` as the fourth positional argument of `re.sub`; Python interprets this as `count=32`. A literal reproduction must preserve this. Do not substitute unlimited whitespace replacement or alter the upstream code. Clean and dirty headers may differ: the official evaluator compares row/column positions, while the audit records both original headers and does not claim externally authenticated entity alignment.

## Evidence contents

- `results/*_native.json`: every final native case, dimensions, both schemas, coordinate/target/table hashes, E1–E4 and all score arrays.
- `results/run_native_audit_invocation.json` and `results/verify_independent_invocation.json`: actual execution, timestamps, code/input fingerprints and exit status.
- `results/independent_verification.json`: independently reconstructed per-case and per-stratum counts; all checked fields match.
- `results/adapter_witnesses.json`: six Rayyan coordinate/hash witnesses, plus explicit zero counts for the other six cases.
- `initial_strict_header_attempt`: superseded attempt and wrapper; not pooled as additional observations.

Default-five, tax-extension and toy-control denominators must remain separate. All negative primary endpoints are part of the result. Complete-clean dictionaries are adapter/oracle probes, not repair-method evaluations. No new defect prevalence or published-ranking effect is established.
