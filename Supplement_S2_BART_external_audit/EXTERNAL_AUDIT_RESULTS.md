# External BART audit: completed bounded case study

The native applied pipeline passed the paired-change invariant on all four audited examples. The audit also identified two ways an adapter can produce a wrong conclusion: comparing CSV row positions after legal row reordering, and treating the second event-CSV field as the clean value according to the current official wiki. This is an external audit of interface assumptions; it is not a claim that BART's internally consistent generator/scorer is defective.

## Selection, chronology, and independent expected basis

The first protocol was locally frozen at actual host UTC 2026-10-08T09:25:33.349047+00:00, before candidate inspection. `protocol_freeze_receipt.json` pins its hash. This is not an externally timestamped preregistration. BART was the first prespecified candidate. The official project identifies it as an error-generation tool and links its author repository. The separately published 2016 sample ZIP contains clean inputs/configurations but no dirty/event result corpus; its complete file inventory and checksum are retained locally. HoloClean's repository file listing was inspected as the predefined fallback, but no HoloClean experiment was run and no outcome-driven benchmark substitution occurred.

The BART repository was pinned at commit `354f503f401d5360e9a6957f4edd096d3dc413f6`. A1 fixed all four non-DBMS `*-egtask.xml` examples under the engine's resources before native execution. These are independently authored upstream examples, not inputs designed for this study's diagnostic. They contain 30 **target** rows and 118 **target** cells across the four runs; repeated employees examples are not statistically independent datasets. Original source/master rows are separate and remained unchanged.

An initial instrumentation attempt (`native_run_01`) incorrectly required a materialized dirtyTarget while the original configurations default to `applyCellChanges=false`; all four failures and observations remain preserved. The repaired observation harness (`native_run_02`) used the native CSV overlay API on proposal events. These are component observations, excluded from the materialized-pair endpoint. Their one random-event run emitted three proposals; they are not pooled with the final six events. The error and retry were documented before retry; no result-selected seed reruns were used.

A2 was locally frozen at 2026-10-08T09:46:21.700369+00:00, after those observations and before its own results. **A2 is explicitly exploratory**, not retroactively preregistered. It retained all four original input/dependency/rate/strategy specifications and only enabled the official native apply and clean/dirty/event export options. The default delta application and clone configuration remained unchanged. One fresh JVM ran each example. All four completed; none was excluded. The actual APrioriGenerator control flow produced the applied database and three exports.

Expected changes came from independently observed native `ICellChange` objects, including the original and new value and OID/attribute. They were not synthesized from the dirty/clean diff. Original XML is retained locally with exact restoration paths/hashes; before-state, original event records, actual applied state, source/master snapshots, exports, command/clock receipts, and hashes are retained per case in the supplement. The audit parser is newly authored Python standard-library code; it does not call the repairer, BART parser/scorer, or a diff-derived event generator.

## Actual results

| Original case | Target rows/cells | Events | Identity-aligned changes | Unexplained / unrealized / wrong-value | Positional differences |
|---|---:|---:|---:|---:|---:|
| employees | 8 / 32 | 0 | 0 | 0 / 0 / 0 | 24 |
| employees-random | 8 / 32 | 6 | 6 | 0 / 0 / 0 | 25 |
| employees-symmetrictest | 12 / 48 | 0 | 0 | 0 / 0 / 0 | 31 |
| synthetic_01 | 2 / 6 | 0 | 0 | 0 / 0 / 0 | 0 |

The six non-noop events were all realized, with correct values and no collateral change. The three zero-event native cases are proper negative controls. A naive row-position comparison would flag two of those three cases, reporting 24 and 31 apparent changes, because native delta materialization changed record order. This is a false alarm of that comparison rule, not a BART data corruption. Four additional identical-copy controls and four single-unrecorded-cell sensitivity controls were executed separately; they are checker controls and do not enlarge the external sample denominator.

BART's CSV table exporter omits OIDs. This study therefore preserves native iterator/OID sidecars; it does not assert that arbitrary users can recover identities from the CSV alone. Both clean sidecars were sampled before APrioriGenerator, and both dirty sidecars after it; the legacy filenames containing “before/after_export” are not literal observations bracketing the export. The independent checker verifies exact CSV agreement with the observed row sequences, and aligns states by table/OID/attribute. Identical duplicate rows in the symmetric case have distinct native OIDs; permutations within equal-value groups cannot change the evaluated value invariant, but the CSV alone does not authenticate their identity. Scope is nonnull textual `ConstantValue` cells. Unsupported value types, duplicate JSON keys, duplicate identities, ambiguous event references, receipt drift, source drift, and schema drift are rejected.

## Event-schema consequence, actually scored

The official wiki describes a three-field event record as cell reference, clean value, dirty value. At the pinned version, `ExportCellChangesCSV` emits cell reference, **dirty value, clean value**, and `DAOCSVRepair`/`Repair` interpret it consistently that way. All six observed records disagree with the wiki's value ordering and agree with the implementation's ordering. This is a documentation/adapter contract mismatch; no allegation is made that the native scorer internally reverses gold.

Two probes use the same six actual event identities. The snapshot probe supplies the independently observed original value. The documentation probe treats CSV field two as clean, following the wiki. The unmodified native `ComputeQualityOfRepairs` produces:

| Probe | Value precision / recall / F1 | Cell precision / recall / F1 |
|---|---|---|
| Original-snapshot clean values | 1 / 1 / 1 | 1 / 1 / 1 |
| Documented clean-column interpretation | 0 / 0 / **NaN** | 1 / 1 / 1 |

The native zero/zero F1 is undefined (`NaN`), recorded as JSON null plus the literal native text, not replaced by zero. Both probes localize exactly the same cells; only value semantics differ. These are controlled adapter probes, not competing repair algorithms or an estimated effect on published BART results. A genuine deterministic scorer-only rerun saved exact commands, actual timestamps, input/output hashes, and stdout; it did not rerun the generator or change the scientific sample.

## Supported claim and limits

Verified: on a bounded independently authored native corpus, identity-aligned event auditing agrees with the applied output, preserves correct negative controls, and exposes concrete identity/schema assumptions that otherwise change labels or value scoring. The main desired anomaly endpoint was negative: no unauthorized native applied change was observed. The nonzero-event evidence is six changes in one small example; it does not estimate BART-wide or field-wide defect prevalence. No independent business gold, natural enterprise corruption, repair superiority, performance advantage, or deployment benefit is claimed. The audit supplies the selected M1 external-evidence route at this limited case-study scope; it does not itself establish general novelty or guarantee journal acceptance.

## Reproduction and provenance

Run `python3 verify_delivery.py` in the unzipped supplement. It verifies checksums, replays all 118 cell decisions in a fresh temporary directory, and independently checks the frozen native scorer results without Java, network access, or ancestor inputs. Optional native regeneration requires restoring the pinned author source archive and its dependency hashes, then compiling/running the clearly separated commands in README. The upstream generator's default randomness was not seeded or rewritten; a fresh generation may produce a different number of random events. The six-event claim is exactly reproducible from the frozen observed artifacts, not promised for every fresh execution.

Primary sources: [official BART project](https://db.unibas.it/projects/bart/), [pinned repository](https://github.com/dbunibas/BART/tree/354f503f401d5360e9a6957f4edd096d3dc413f6), [official evaluation-format wiki](https://github.com/dbunibas/BART/wiki/How-to-evaluate-a-data-cleaning-tool). `source_manifest.json` contains full source URLs/checksums and the preserved MIT license. Original XML task/data files are also excluded because their redistribution is not licensed here; their source content is recovered and verified through the pinned archive. Third-party JAR dependencies and the separately licensed/unspecified sample ZIP are excluded from the delivery. No external configuration registry was edited, and nothing was shared publicly, pushed, submitted, or sent to third parties.
