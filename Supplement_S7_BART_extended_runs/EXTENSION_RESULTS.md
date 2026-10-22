# Results: extended BART generator runs

All 90 planned runs (30 per task) completed; none was excluded or replaced. The protocol is `PROTOCOL_EXTENSION.md`; its freeze receipt is `protocol_extension_freeze_receipt.json`. Machine-readable totals: `extension_summary.json`.

| Task | Rows | Runs | Native events | Event types | Zero-event runs | Unexplained | Unrealized non-noop | Value mismatches |
|---|---|---|---|---|---|---|---|---|
| T1 shipped random task | 8 | 30 | 70 (0–6 per run) | Random 70 | 4 | 0 | 0 | 0 |
| T2 constraint-driven | 8 | 30 | 270 (9 per run) | VioGen 270 | 0 | 0 | 0 | 0 |
| T3 50 rows, constraint-driven and random | 50 | 30 | 564 (15–24 per run) | VioGen 356, Random 208 | 0 | 0 | 0 | 0 |

**Event concordance.** Every one of the 904 native events is realized in the dirty table with the recorded value, and no cell changes without an event.

**Row order.** Every run reorders rows between the clean and dirty exports (all 8 rows in T1 and T2, 48 of 50 rows in T3). Positional comparison reports 24–27, 26 and 191–195 apparent changed cells per run; all four zero-event runs are flagged.

**Event-field orientation.** All 904 exported events follow the implemented order (cell, dirty value, clean value) and none follows the documented order. Additional analysis with the unmodified native scorer on the 86 event-bearing runs: the implemented-order probe obtains value precision and recall of 1 in all 86 runs, the documented-order probe obtains 0 (native F1 NaN) in all 86, and both obtain cell precision and recall of 1.

**CSV-only matching.** Computed from the CSV files only and hashed (`match_sealed.sha256`) before native identities were read. The native identity assignment is optimal in all 90 runs, and the changed/unchanged label of all 7,920 cells is unique and correct. Targets are unique and correct for 7,916 cells. In 2 of the 30 T1 runs, two rows that differ only in salary both received a random salary error, so two optimal assignments exchange them and each of the 4 affected cells has two supported targets; semantic target recovery under the matcher is therefore undetermined for those cells, while native identities resolve them. For tables of at most 12 rows, the subset dynamic program and the forced-pair Hungarian test agree on every run.

**Wrapper controls.** All 180 controls (a clean self-pair and one out-of-event perturbation per run) return the expected verdict.

**Pre-freeze checks.** One feasibility run per task (`pilot/`) was executed before the protocol was frozen and is excluded from these results.
