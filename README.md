# Reproducibility materials: comparison contracts for benchmark evaluation

Hongsheng Wang and Xiubo Liang. Supplementary materials for the article *Comparison contracts for benchmark evaluation: attributing score discrepancies in data cleaning and outlier detection*, submitted to *Data Mining and Knowledge Discovery* (Springer). Version 1.0.0 accompanied an earlier version of the article titled *Auditing Data-Repair Benchmarks with Explicit Comparison Contracts*; version 1.1.0 adds Supplement S8 and updates the figure code. Section numbers below refer to the current article.

## Supplements and where they are used in the article
| Folder | Article section | Content |
|---|---|---|
| `Supplement_S1_reference_experiment` | Section 7 and Appendix A | Supplied-authority reference implementation: six methods, recovery manifest for the 29 pinned dbt sources, frozen and current predictions, independent scoring, per-case protocol checks |
| `Supplement_S2_BART_external_audit` | Sections 4.1–4.3 | BART generator audit: frozen protocol and amendments, observation and scoring harnesses, identity-aware checker, saved run evidence and controls |
| `Supplement_S3_BART_CSV_only_matching` | Section 4.4 | CSV-only matching control: matcher, complete optima, sealed outputs, native revelation checks |
| `Supplement_S7_BART_extended_runs` | Section 4.5 | Extended generator runs: frozen protocol, task configurations, 90 run directories, checker, matching and native-scorer outputs, regeneration scripts |
| `Supplement_S4_Raha_Baran_consumer_audit` | Section 5 | Raha/Baran consumer audit: protocol, amendments, author code, results and hashed recovery instructions for the seven pairs |
| `Supplement_S8_outlier_redistribution_audit` | Section 6, Tables 8–9, Fig. 2 | Outlier-detection redistribution audit: frozen protocol with amendments A1–A6, planted-cause validation, input hashes, NumPy detectors, correspondence, native-control, min-max and ranking results, ADBench-to-DAMI crosswalk, download script |
| `Supplement_S5_audit_decision_ledger` | Section 8.2 | Audit decision ledger: decision rules, source-linked summaries, replay outputs, constructed software checks |
| `Supplement_S6_figure_code` | Figs. 1, 3 and B.1 | Deterministic drawing script for the schematic figures |

Each folder has its own README with offline verification and, where applicable, regeneration commands.

## Public-release copy
These folders are the public-release copies of the study materials. File names, identifiers and paths were normalized for publication, and all manifests and hashes were regenerated for this copy; scientific content, data values and results are unchanged. Every folder's offline verification passes on this copy. The authors retain the original hashed working archives and can provide them on request.

## What is not included
## Notes on Supplement S7

- `protocol_extension_freeze_receipt.json` hashes the protocol, the run and audit scripts, the checker, the harness and the task files. The matching and scorer scripts (`ext_match.py`, `ext_scorer.py`) were written after the freeze; the methods they implement are fixed in the hashed protocol text.
- In `match_revealed.json`, `correct_labels` counts only cells whose correction target is unique (7,916). The four cells with two supported targets each have the single supported label recorded in `match_sealed.json`, and that label is correct, giving the 7,920 correct labels reported in the article.

Original third-party CSV files, YAML sources and upstream code are not redistributed; each folder explains how to restore them from pinned public sources under their own licences. The two BART task files in S7 are derived from the MIT-licensed BART repository and carry its licence. Commercially sensitive historical inputs derived from enterprise data are not included, so the historical diagnostics of Appendix B cannot be replayed from these materials.

## Licence
Author-owned code and documentation are released under the MIT License (`LICENSE`). Third-party materials keep their own licences.
