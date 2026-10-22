# Bounded audit decisions from saved evidence

This supplement is a **retrospective derived ledger and conclusion replay**. It interprets three already measured contracts after selecting the proposition to test. It is not an independent external validation, a new benchmark, a new matching/repair algorithm, or a preregistered study.

It retains every saved BART case (4) and every released consumer pair in the audited inventory (7), including native negative results. Six separate indexes cover all 32,946 previously executed constructed certificate checks. **One newly executed, fully author-constructed current wrong-authority example is separate from both groups.** None of these denominators are pooled into a natural-defect rate.

## Run without the original repository

Python 3.9+ and its standard library suffice. No installation, network, dataset restoration, service or ancestor repository is needed. From any working directory:

```sh
python3 -B /absolute/path/to/contract_audit/run_audit.py --output-dir /tmp/audit-audit-ledger
python3 -B /absolute/path/to/contract_audit/test_audit.py
```

The replay reads the sibling portable input and inventory profile, checks the input SHA-256, computes decisions, and writes four files to the selected output directory. Paths to /current appear only as provenance metadata; the replay never opens them. `case_ledger.json` contains all endpoints and unknowns; `case_ledger.csv` is a flat rendering; `numeric_summary.json` and `audit_decision_table.tex` are generated numerical summaries.

`inventory_profile.json` independently fixes the intended scope. Removing a case and also editing the input's self-reported inventory fails the default profile check. An alternative caller-defined scope can be supplied with `--inventory-profile`, but it is identified separately and does not claim the fixed census. A custom input requires `--expected-input-sha256`; that digest binds the supplied bytes, not their real-world truth or authorship.

## Select a proposition, then supply its own evidence

Each input record has `case_id`, `family`, `requested_claims`, `scope`, `source_refs`, `evidence_index`, and `facts`. The outer object declares its inventory; the separate profile fixes which cases that declaration must include. The record structure is reusable, while the implemented predicates describe only the measured interfaces below. Unsupported propositions return UNKNOWN; this is not an all-purpose benchmark checker.

| Evidence family / selected proposition | Required evidence and interpretation |
|---|---|
| Generator: native event fidelity | Identity crosswalk validation, independently saved native event witness, and accounted change/event/value discrepancy counts. Missing event evidence means UNKNOWN. It does not select a certificate branch. |
| Generator: position equivalence | Complete cell confusion accounting and target agreement against native correspondence. CONTRADICTED concerns position pairing; it does not assert unauthorized producer corruption. |
| Generator: CSV all-optima determinacy | Exact-string Hamming cost matrix, complete saved optimal-assignment support and all cell support cardinalities. Different identity assignments are harmless if all labels and target strings agree. Material semantic ambiguity means UNKNOWN. |
| Generator: all-optima native agreement | The preceding evidence plus revealed native reference and mutually consistent score bounds. Agreement only covers these saved pairs; it does not prove tuple sidecars necessary. |
| Generator: documented value equivalence | Fixed-event snapshot-value and documented-field scorer probes, plus implementation-orientation counts. Zero-event cases remain NOT_APPLICABLE for this endpoint. Native consistency remains a separate endpoint. |
| Consumer: label and persistence equivalence | Released positional interface, dimensions, raw/native label accounting and digests, normalized-value idempotence, official export/load changes and target checks. This does not certify real entity identity. |
| Consumer: direct/materialized probe equivalence | Nonempty native label denominator, native score vectors and target-change counts at equal coordinates. Lower raw/direct correction scores can coexist with correct official materialization. These dictionaries are adapter probes, not repair algorithms. |
| Consumer: self-pair negatives | Saved zero-label counts and native empty-case score convention. The six zero scores for an empty probe are not six failed predictions. |
| Reference: given-authority exactness | Saved checker status, answered state, exactness flags and complete binding-multiset equality for the ordinary/extended cohorts. This is conditional projection agreement, not business truth. |
| Reference: saved protocol checks | All saved rows are indexed; typed observed verifier outcomes are compared with software-test expectations. A valid refusal has `answered=false` and no certificate. It is not an accepted repair. |
| Current constructed authority example | Copied, hash-checked current repairer/checker actually receive the same wrong-but-complete qualifier authority. Output is compared separately with the explicitly authored original. This is one local software witness, not domain gold. |

SUPPORTED and CONTRADICTED concern the **named proposition**, not the system globally. UNKNOWN marks missing, malformed, contradictory or ambiguous evidence. NOT_APPLICABLE marks the absent endpoint denominator. Native consistency and an adapter inequivalence can therefore both be recorded for the same case. Every record keeps business truth, population prevalence, generalization and effects on published algorithm rankings unknown. Reference records additionally leave real-world authority completeness, authenticity and independently intended targets unknown.

## What is recomputed, and what is cited

`build_inputs.py` reads the exact files pinned in `source_lock.json`, verifies source hashes and saved receipt links, and derives the portable input through a whitelist. It copies author result counts, hashes, Hamming distances, label-support booleans and target-support cardinalities. It omits CSV rows, cell strings, OIDs, metric names, native source code, declarations, bindings and qualifiers from the pre-existing third-party-derived studies. Certificate indexes retain file SHA, line ranges, per-kind counts, distinct-base counts and available-field counts. A zero true-count with availability zero means **not supplied**, not a measured false result.

The replay **recomputes minimum Hamming cost and number of optimal assignments from the saved numeric matrix** using a small subset DP. It does not reread raw CSVs or independently reconstruct the matrix. Semantic support and actual native event agreement are derived from locked saved outputs that were independently checked in the preceding audit. This replay does not claim to repeat that raw-data verification. Likewise, certificate index aggregation does not rerun the 32,946 historical checker calls. Source hashes are integrity/provenance pointers, not signatures or business validation.

For maintainers with the authorized existing repository only, the extraction command is:

```sh
python3 -B /absolute/path/to/contract_audit/build_inputs.py \
  --repo-root /absolute/path/to/original-repository \
  --output /tmp/derived-saved-evidence.json
```

This optional extraction stage deliberately reads pinned results; the standalone replay above does not. Extraction fails on source drift and never refreshes the lock automatically. No original third-party raw is distributed. The only literal declarations/edges shipped here are the tiny newly authored software example.

## Complete observed outcomes

The generated ledger retains the four BART cases with 30 rows/118 cells and 6 saved events: native concordance holds in all four; positional equivalence fails in three, including false alarms in two zero-event cases. Saved-matrix optimum costs/counts are 0/1, 6/1, 0/2, 0/1; every case's saved all-optima semantic support agrees with the native reference. The two symmetric assignments do not create semantic ambiguity. The event-bearing documentation probe disagrees at the value endpoint while native cell detection remains exact; its undefined native value F1 remains JSON null with text `NaN`.

All seven consumer pairs retain label, persistence and official materialized-route agreement. Rayyan alone has 942/948 raw/direct target hits; its six target differences disappear through the official materialization route. This is a bounded adapter result, not a native bug or observed ranking reversal. All other raw/direct probes agree. The 854 ordinary and 144 extended reference checks retain DR=MP projected outputs; the extension reuses 48 bases. Refusal/tamper/idempotence/saved-gold checks keep their own denominators and software interpretation.

In `software_example/`, one original qualifier is literally defined as `1 month` and a supplied complete authority says `2 months`. These strings are opaque payloads; no temporal semantics is tested. The recorded current checker accepts the patch under that same authority, and the resulting edge differs from the constructed original. One occurrence is removed and one added. `legacy_wrong_authority_context` separately points to the historical frozen receipt; it is not relabeled as this current execution. See the example's input, patch, checker output, comparison and timestamped execution receipt.

To rerun that **single** authored example, first copy `software_example/` to a temporary directory, then run its `run_example.py`. It writes a fresh timestamped receipt beside itself. Keep the distributed evidence snapshot intact; a new execution receipt is not silently substituted into the locked ledger input.

## Software verification and delivery boundary

`test_audit.py` contains 35 constructed software tests: small exhaustive assignment oracles; preserved negative cases; missing witness and semantic ambiguity; omitted/duplicate cases; invalid hashes, dimensions, counts and score vectors; impossible confusion accounting; missing exactness fields; correct refusal versus repair; malformed booleans; wrong-family requests; no-partial-output input-hash rejection; and complete UNKNOWN rendering. Tests neither generate new upstream cases nor estimate scientific accuracy. The separately executed wrong-authority example is not multiplied by the unit-test assertions that inspect its saved result.

`logs/` records extraction, tests and a fresh-directory portable replay. A Python audit hook denied original-user-tree file access, sockets and subprocess creation during that replay and its 35 tests; all four regenerated outputs were byte-identical. This is a Python-level guard, not an operating-system sandbox: the attempted OS sandbox was unavailable and its failure is recorded in `logs/portable_receipt.json`. The public file manifest excludes internal reviewer notes and Python caches. Technical execution and ledger consistency do not settle scientific novelty or acceptance.
