# Protocol: extended BART generator runs

Frozen on 2026-10-22 before the main runs. Local timestamped record; not externally registered.

## Purpose
The original generator audit observed one event-bearing configuration (six Random events) and no constraint-driven events. This extension tests whether its endpoints hold over repeated runs, under constraint-driven (VioGen) error generation, and on a larger table.

## Software
BART at commit 354f503f401d5360e9a6957f4edd096d3dc413f6 (all 237 pinned source and dependency files verified against the recorded SHA-256 values), compiled with the original build script. The applied observation harness is unchanged except for its completion token. OpenJDK 21. Each run uses a fresh JVM and BART's default random number generator; no seed is set or selected.

## Tasks (main memory only)
- **T1** `employees-random-egtask.xml`: the shipped task, unchanged (8 rows; random errors on name, salary and manager at 10%).
- **T2** `employees-viogen-egtask.xml`: the shipped `employees-egtask.xml` with only its empty configuration replaced by `errorPercentages/defaultPercentage = 25`, which enables BART's constraint-driven violation generation for the five shipped denial constraints (8 rows).
- **T3** `employees50-viogen-random-egtask.xml`: the shipped 50-tuple employee and manager data (`xml/50tuples_emp.xml`, `xml/50tuples_md.xml`) converted to BART's main-memory GENERATE syntax, the shipped denial constraints, `defaultPercentage = 5` and random errors at 5% on name, salary and manager (50 rows).

## Runs
30 runs per task. Every completed run is analysed; runs that fail to complete are reported with their reason and are not replaced.

## Endpoints (identical to the original audit)
Per run, with the unchanged per-case checker: unexplained changes, unrealized non-noop events, event-value mismatches, mismatches of the exported event file against the documented and the implemented field order, positional cell differences and reordered rows, and the wrapper controls.
CSV-only matching: computed from the clean and dirty CSV files only and hashed before native identities are read. Exact minimum-total-Hamming assignment; for every dirty row, the set of clean rows it is matched to in at least one optimal assignment. Tables of at most 12 rows use the original subset dynamic program; larger tables use a forced-pair test with the Hungarian algorithm, which yields the same set exactly. Semantic recovery is supported for a run when every cell has a unique supported target and label and these equal the native targets and labels.

## Pre-freeze checks
One feasibility run per task was executed before this protocol was frozen, to confirm that each task parses and completes. These pilot runs are retained, reported separately and excluded from the endpoints.
