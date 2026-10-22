# Public reproduction artifact

This bundle contains the complete author code, 29-source pinned recovery manifest, all 5,124 frozen predictions, all 5,124 current predictions, independent scorer, and per-case current checks. The public experiment is a synthetic declaration-projection test on one official example and four developer fixtures from dbt Labs. Its labels are generated before mutation. They do not establish natural defects, query semantics, business truth, or performance superiority.

## Requirements and source recovery

Python 3.9 or later is sufficient for scoring, repair, certificate verification and all constructed checks. The YAML-to-task adapter additionally needs PyYAML 6.0.3 (the tested version). No installation is performed by these scripts. If PyYAML is absent, install it in your approved environment before running the adapter.

Original third-party YAML is deliberately omitted. The generated task records also contain upstream declaration descriptions, so they are omitted from the ZIP and reconstructed byte-exact from pinned originals. Every source has repository, commit, path, URL, SHA-256, byte size, and license-status fields in `provenance/public_sources.json`. No enterprise archive is distributed.

From the extracted bundle, choose an authorized source recovery route:

```bash
# Existing source cache contains jaffle-shop/ and metricflow/ subdirectories.
python3 code/restore_sources.py --cache /path/to/authorized-source-cache

# Alternatively, personal authenticated GitHub read-only retrieval.
# Supply a token securely through AUDIT_GITHUB_TOKEN; never paste it into this bundle.
python3 code/restore_sources.py --github-user YOUR_PERSONAL_GITHUB_USERNAME

python3 code/generate_public.py --output-dir data
```

The generator requires all 29 pinned hashes, produces 158 clean controls and 696 mutation tasks, and refuses a byte-level mismatch against the two fixed input hashes. It executes no dbt/MetricFlow code, models, SQL, or network request.

## Exact reproduction commands

```bash
python3 code/score_public.py --mode frozen
python3 code/run_public.py
python3 code/score_public.py
python3 code/test_scorer.py
python3 code/run_robustness.py --input-dir data --output-dir results/robustness_rerun
```

All commands use paths inside the extracted bundle. `--root`, `--output-dir`, and `--predictions` expose explicit path choices. No script searches for an ancestor working tree or a developer home directory. The six-method runner must match the final adjacency in all 5,124 frozen predictions. The scorer refuses missing, duplicate and unknown task IDs, method substitutions, false correctness flags, mixed input hashes, mismatched timing samples and invalid current certificates. It imports the sole independent declaration checker, never the repair implementation or gold-producing adapter. The historical frozen branch checks frozen arithmetic against recorded gold and is explicitly not independent current authority validation.

The old frozen tables contain saved per-task medians of five calls; those individual old timing samples do not exist. They are frozen historical measurements. New current results save every nanosecond sample and are scored separately. Neither is an execution-time superiority claim.

Expected mutation exact counts are 0, 0, 99, 365, 696, 696 for no change, held-out constant, expression scan, unqualified rebuild, declaration rebuild and multiset patch. Their clean exact counts are 158, 0, 116, 100, 158, 158. The scorer reconstructs 72 public rows, 30 mutation/category rows, and mutation certificate totals of 696 added, 486 removed and 389 preserved occurrences.

## Verification and packaging

`results/cold_start_receipt.json` records execution in a fresh temporary directory after ZIP extraction and explicit source-cache restoration. That run proves portable source regeneration and scoring from authorized pinned bytes. It does not claim a fresh online GitHub download or validate a newly issued access token.

```bash
python3 code/cold_start_verify.py --source-cache /path/to/authorized-source-cache
python3 code/export_bundle.py --output Supplement_S1_reference_experiment.zip
```

Use this exporter when sharing the reviewer ZIP. It deliberately excludes `data/`, `sources/`, caches and nested ZIPs; recovery and exact-generation commands replace source-derived files. The bundle manifest hashes every distributed file. Source and historical restrictions appear in `provenance/LICENSE_AND_DATA_BOUNDARIES.md`.
