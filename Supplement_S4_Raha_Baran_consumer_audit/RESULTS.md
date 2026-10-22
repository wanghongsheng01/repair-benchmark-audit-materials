# Frozen Raha/Baran consumer-contract audit

All seven fixed upstream pairs completed. The independent standard-library implementation agrees with the unchanged native loader, label extractor, export/reload path and scorer. The two primary endpoints are negative: normalization changes no error coordinates, and one native export/reload changes no normalized values, error coordinates or clean targets. A secondary adapter probe changes value scores on six existing Rayyan cells.

## Fixed corpus and actual results

The source is the [official Raha/Baran repository](https://github.com/BigDaMa/raha/tree/7be1334b8c7bbdac3f47ef514fb3e1e8c5fc181c), pinned at `7be1334b8c7bbdac3f47ef514fb3e1e8c5fc181c`. All seven `datasets/<name>/clean.csv` and `dirty.csv` pairs were selected from tree metadata before any CSV was downloaded. No upstream detector, model, corruption generator or stochastic process was run.

| Stratum / pair | Rows | Cells per side | Raw = native error labels | Label-set changes | Native reload value changes, dirty / clean | Raw-clean adapter EC F1 |
|---|---:|---:|---:|---:|---:|---:|
| Primary / beers | 2,410 | 26,510 | 4,362 | 0 | 0 / 0 | 1 |
| Primary / flights | 2,376 | 16,632 | 4,920 | 0 | 0 / 0 | 1 |
| Primary / hospital | 1,000 | 20,000 | 509 | 0 | 0 / 0 | 1 |
| Primary / movies_1 | 7,390 | 125,630 | 7,675 | 0 | 0 / 0 | 1 |
| Primary / rayyan | 1,000 | 11,000 | 948 | 0 | 0 / 0 | 0.9936708861 |
| Extension / tax | 200,000 | 3,000,000 | 121,219 | 0 | 0 / 0 | 1 |
| Demonstration / toy | 6 | 18 | 4 | 0 | 0 / 0 | 1 |

The default five datasets contain 14,176 rows, 199,772 cells per side and 18,414 error coordinates. The tax extension and toy control remain separate from this primary denominator. Across the complete inventory there are 214,182 rows, 3,199,790 cells per side and 139,637 error coordinates. These are corpus counts, not independent incident or field-prevalence estimates.

Normalization changes 222 dirty values and 188 clean values in the default five datasets, but those representation changes do not add or remove error coordinates. Tax and toy have no raw-to-native value changes. No existing value violates one-pass idempotence under the literal pinned normalizer; native export followed by native reload confirms the same negative finding. All fourteen self-pair controls have zero error labels and return the upstream all-zero score convention for empty predictions. Every correctly normalized complete-clean probe returns six ones.

## Native score consequence

The unchanged [Dataset implementation](https://github.com/BigDaMa/raha/blob/7be1334b8c7bbdac3f47ef514fb3e1e8c5fc181c/raha/dataset.py) normalizes tables during loading. Its dictionary evaluator compares submitted replacement strings directly against loaded clean values. The predefined Rayyan raw-clean adapter submits all 948 correct error coordinates, but six replacement values still contain whitespace differences removed by loading. Detection precision, recall and F1 remain 1; correction precision, recall and F1 are all `942/948 = 0.9936708860759493`. With normalized clean values all six scores are 1. Passing either dictionary through the official repaired-table materializer before extracting and scoring corrections also yields six ones.

The difference is approximately 0.633 percentage points, not a demonstrated change in any published algorithm's score. The probes intentionally use clean reference values and are not repair algorithms. This is a concrete input-contract consequence on existing source values; it is not evidence of an internally faulty scorer or incorrect clean reference. The six witnesses are recorded as coordinates and hashes in `results/adapter_witnesses.json`, with no raw cell text. Their whitespace mechanism was mechanically explained after the frozen endpoint finished; no additional outcome was selected.

## Chronology and schema limits

The root protocol was frozen locally at `2026-10-09T02:41:29.659426Z`, before downloading CSVs. It is not externally timestamped preregistration. An initial wrapper incorrectly required identical clean/dirty column names. This rejected beers, hospital and movies_1, while the other four cases completed. Their results and exact first wrapper are preserved in `initial_strict_header_attempt`.

The official evaluator defines coordinates by row and column position. A1 removed only the extra wrapper header-name equality condition, saved both headers, and reran all seven deterministic cases under one corrected wrapper. It did not change the roster, cells, native source, probes or endpoints. Differing header names are a structural observation, not a data-defect label; positional agreement does not independently authenticate column meaning or real-entity row identity.

Static review also clarified that the source's fourth positional `re.sub` argument means `count=32`, not a flags argument. The independent implementation was corrected before its first execution; the native source was never changed. Both corrections and their timing are explicit in the retained receipts. The result is neither an unamended first attempt nor an outcome-driven dataset replacement.

## Evidence and scope

Native execution used Python 3.9.6 and pandas 2.3.3, with the reviewed source loaded directly using `importlib`; the upstream package initializer and benchmark/detector programs were not imported. Actual commands, times, return codes and stdout/stderr/code hashes are retained. Independent stdlib-only parsing and normalization compare every exported cell, table fingerprints, error-coordinate and target fingerprints, all native score arrays and all controls. `results/independent_verification.json` reports `PASS` with no mismatches. This implementation cross-check is distinct from the parent's separate review.

The [Baran primary paper, Section 6.1](https://www.vldb.org/pvldb/vol13/p1948-mahdavi.pdf), identifies Hospital's errors as imposed randomly and Tax as synthetic; it describes Beers and Rayyan as real-world datasets cleaned by their owners. These are dataset-family provenance statements, not independent validation of each current source byte. Flights, movies_1 and toy error provenance remains unverified here. None supplies independent business-semantic gold for this study's metric-reference task.

Repository Apache-2.0 coverage does not establish a complete license chain for each underlying dataset. Third-party CSVs, source and derived normalized tables remain local and are excluded from redistribution; pinned URLs, Git blob/SHA-256 hashes, audit programs and aggregate results support restoration and replay. The main supported addition is a broader falsifiable consumer audit with retained negative results and one bounded score-input consequence, not a generator defect, repair superiority, business validation or general prevalence claim.
