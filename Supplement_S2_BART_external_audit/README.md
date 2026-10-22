# External BART audit supplement

This is a frozen, bounded external case study. Read `EXTERNAL_AUDIT_RESULTS.md` for results, exclusions, and limitations. The original preinspection protocol and later **exploratory** A1/A2 operationalization records are preserved. No BART-wide defect or repair-performance claim is made.

## Offline reproduction (recommended)

Requirements: Python 3.9 or later, standard library only. From any directory containing the unzipped package:

```
python3 verify_delivery.py
```

Expected final status: `EXTERNAL_AUDIT_REPLAY_OK`; 4 native applied cases, 118 target cells, 6 events, 1 nonempty native scorer case. This validates the package manifest, protocol hashes, exact four source-hash/task/harness/receipt bindings, all 118 cell decisions, event-value orientation, 8 separate wrapper controls, and an independent scorer calculation. It executes no downloaded code, requires no Java/network, and reads no ancestor working directory. Saved run receipts contain historical absolute commands as provenance; those paths are never used by offline replay.

`audit_results/all_cases.csv` is the compact table; case-specific `*_cells.jsonl` preserve every target cell and expected basis. `controls.json` separates actual native cases from authored copy/perturbation controls.

## Optional native regeneration

Regeneration is separate from deterministic replay. It downloads third-party source/dependencies and executes Java; obtain any required environment/platform approval before these steps. No script installs a JDK or changes system settings. Existing Java 21 was used in the recorded run.

```
python3 restore_upstream.py --download
python3 build_native.py --java-home /path/to/existing/jdk
python3 run_native.py --java /path/to/existing/jdk/bin/java --applied --run-id my_new_native_run
python3 audit_external.py --run-dir my_new_native_run --out my_new_audit
```

`restore_upstream.py --archive /path/to/BART_source.zip` is the offline alternative. It requires the exact pinned archive SHA, validates safe archive paths, extracts only engine/library inputs, and executes nothing. Compilation disables annotation processors. The run is restricted to the four original `GENERATE` examples, rejects external DB configuration, uses fresh JVMs, caps each at 120 seconds/512 MB, and refuses to overwrite runs. All original error rates, strategies, input/dependency text and native clone/delta defaults remain unchanged; only native apply and three export settings are enabled.

Default BART RNG was not rewritten or seeded. A new run can generate a different event count, which must be reported separately; do not replace or select among the frozen six-event run. `score_native_probes.py` replays the package's saved native scorer probes only, without new generation. After building native code:

```
python3 score_native_probes.py --java /path/to/existing/jdk/bin/java
```

This deliberately rewrites scorer outputs/receipts with real current timestamps; preserve the original package before using optional commands. It is not part of the immutable offline verifier.

## Identity, value projection and observation timing

Native CSV exports omit OIDs. The saved sidecars record native tuple iterator/OID observations and permit table/OID/attribute alignment. Both clean observations occurred before APrioriGenerator; both dirty observations occurred after it. The historical filenames `clean_crosswalk_after_export` and `dirty_crosswalk_before_export` must not be read as literal before/after bracketing. The checker requires exact CSV values/order to match observed sequences. Identical repeated rows have distinct OIDs; CSV alone cannot authenticate their identity. The supported projection is nonnull `speedy.model.database.ConstantValue` text. The checker rejects unsupported classes, duplicate JSON keys/IDs, unresolved event identities and shape/source/receipt drift.

## Complete attempt history and license

`native_run_01`: preserved observer failure, no valid materialized endpoint. `native_run_02`: unchanged upstream tasks, proposal/native-overlay API observations, excluded from applied endpoints. `native_applied_01`: the complete A2 native applied/exported case study. No exclusions in A2. These attempts are not pooled as independent samples.

The source archive is pinned in `source_manifest.json`. Original upstream XML inputs, including their inline synthetic data, are excluded because their redistribution is not licensed here even though the author repository supplies an MIT license; `LICENSE_BART_MIT.txt` is retained as provenance. Third-party dependency JARs, compiled classes, full source archive, and the separate 2016 example ZIP are not redistributed. Offline replay binds the saved task hash to the source manifest; actual original XML bytes are checked when the source archive is restored. Those source bytes were independently checked against the pinned archive locally. Restoration supplies author URLs and hashes; review applicable third-party licenses before any further distribution. author-written harness/checker/report files and generated observations are supplied for evaluation and reproduction. No external registry writes, public sharing, push, or third-party contact occurred.
