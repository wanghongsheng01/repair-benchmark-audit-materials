# Frozen follow-up control on saved BART CSVs

Status: frozen locally before running the new matcher; the exact UTC time,
input/code/schema hashes and this document's hash are recorded in FREEZE.json.
This is a follow-up exploratory control on known saved data, not an unseen-data
preregistration. The implementer had read the current independent review and external
BART manuscript section and inspected CSV header/row counts before freezing.
Those sources already disclose six native events and positional counts. Native
identity crosswalks and event records are withheld until the blind output is
written and sealed. Neither a positive finding nor a unique assignment is presumed.

## Fixed inputs and cost

Use all four native_applied_01 cases saved in external_audit:
employees-egtask (emp, 8 rows, 4 columns), employees-random-egtask (emp, 8, 4),
employees-symmetrictest-egtask (emp, 12, 4), synthetic_01-egtask (r, 2, 3).
There are eight CSV files, one clean/dirty pair per case, 30 rows/118 cells per
snapshot side. Copy their bytes to inputs/blind_csv; never modify current or the CSVs.
No additional cases, seeds, corruptions, natural truth, rerun of BART or upstream
execution is authorized or needed. The local portable package contains only
author-generated observations and new standard-library analysis, not upstream
XML, JAR, code or third-party dataset distributions.

Parse CSV as UTF-8 (optional BOM), preserve row multiplicity, and compare exact
decoded string values (no trimming, numeric conversion, null equivalence, fuzzy
matching, key selection or name-as-key assumption). Headers and sizes must agree.
Every column has unit weight. Match dirty row i to clean row j with cost equal
to the number of unequal columns, and minimize the sum over a bijection.

## Blind phase and fixed outputs

code/blind_matcher.py reads only the eight CSV files. A fail-closed Python open
audit hook records allowed reads and rejects other data reads; all standard
library imports occur before it is installed. The copied input directory contains
only those CSVs. The output is created exclusively and cannot overwrite a result.
No identity, native OID, sidecar, event record, scoring reference or reveal code
is accessible through matcher file opens. This protects data access in the
executed implementation; it is not an OS sandbox or a claim that the analyst
was unaware of the previously reported outcomes.

The three prespecified comparisons are:

1. Position: compare the ith dirty row with the ith clean row; report every
   unequal cell and apparent target value.
2. Duplicate-preserving row multiset: use exact row-tuple Counter differences;
   report equality and unmatched rows/multiplicities. Unequal bags alone do not
   supply cell labels or repair values; do not invent localization metrics.
3. One-to-one minimum-total-Hamming assignment: exact standard-library subset
   DP over used-clean-row masks; O(n^2 2^n) upper bound, n <= 12. Report the full
   cost matrix, optimum cost, exact number of optimum permutations and complete
   reachable optimal-assignment DAG. Store prefix/suffix counts, all supported
   dirty/clean bindings and their exact counts, and every cell's possible clean
   target strings and change labels. Enumerate every optimum if the count is
   <= 10,000; otherwise preserve the exact DAG and use DP for score bounds.

Cell coordinates are (dirty CSV data-row index, attribute); indexes start at 1
and exclude the header. A binding supplies clean[j][attribute] as target and
labels a change iff it differs from dirty[i][attribute]. Multiple assignments
of identical value rows are not material ambiguity when all supported bindings
give the same labels AND target values. Material ambiguity is any differing
label or actual target string, not merely multiple native identity bindings.

Write results/blind_results.json and then seals/BLIND_SEAL.json, recording
actual UTC and SHA-256 of the blind result and frozen inputs/code/protocol.
Read and verify that seal before opening any native identity/event files.
Announce the freeze to the parent immediately; do not announce new results
before the seal exists.

## Independent reveal and scoring

Only after sealing, read the saved author-generated native snapshot/export
crosswalks and native event JSON/CSV. Record exact hashes and reveal UTC. The
reveal adapter may then be implemented to the observed saved schema, with its
source hash recorded; it must not alter matcher inputs, code, costs or results.
Verify CSV export-position/value correspondence against native crosswalks.
Use table/OID/attribute as final reference; independently derive true changes
from clean/dirty native values and cross-check native event labels and values.
Report contradictory/missing identities/events rather than assuming consistency.

For each baseline with cell localization, score over ALL globally optimal
assignments (position has one). Report exact min/max TP, FP, FN, TN; changed-label
accuracy over all cells; precision/recall for changed cells; correctly repaired
changed cells (predicted label AND native change AND exact native clean target);
repair-value precision over predicted changed cells and repair-value recall over
native changes; and target-value accuracy over all cells. Because every optimum
has the same predicted changed-cell count (its cost), extrema of the additive
numerators give exact precision/recall bounds. Where a denominator is zero,
preserve null/undefined, and report counts separately. Compute exact bounds
by secondary additive DP restricted to the already sealed optimum DAG, not by
selecting a tie-break. Provide witness assignments attaining endpoints.

For every material ambiguity cell supply complete globally optimal witness
assignments with differing cell target values/labels, then identify which is
consistent with native values. If the unique optimum contradicts native
identity, provide the complete mapping and contradiction even if value-equal
duplicate rows hide a semantic discrepancy. Also report native identity mapping
cost and whether it is an optimum. All identity matching claims are distinct
from value/label recovery claims.

Primary conclusion rule: if all optima recover six changes and all negative
controls without semantic errors, conventional matching suffices for these
saved observations; this experiment cannot establish necessity of extra identity
observations. If ambiguity or a contradictory optimum exists, report the complete
witness and limit the conclusion to these CSVs and the prespecified cost model.
Either result leaves external sample size unchanged: one event-bearing random
case and three zero-event controls. Unique cost optimum does not certify true
identity. No finding proves broad prevalence, business truth, published-result
impact, native generator failure or algorithm superiority.

## Reproduction and verification

Retain raw frozen CSV copies, complete machine-readable outputs, code, local
chronology seals and reveal-only author observations. Run with Python 3.10+
standard library; no network, dependency installation or upstream execution.
Provide a clean local reproduction command that writes a new output directory
and verifies deterministic outcome equality after excluding UTC fields.
Independent review/recalculation is owned separately from implementation.
