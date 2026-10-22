# Frozen external consumer-audit protocol

Study: repair-benchmark audit, scoped benchmark-audit claims.
Primary source: official BigDaMa/raha (Raha and Baran), commit 7be1334b8c7bbdac3f47ef514fb3e1e8c5fc181c.
This new consumer-contract study is separate from the current BART generator event-concordance study. It does not infer independently recorded corruption events from clean/dirty differences.

## Sampling and evidence status before outcomes

Freeze all seven paired CSV families inventoried from the official tree: beers, flights, hospital, movies_1, rayyan, tax, toy. No CSV contents or computed audit outcomes have been inspected for selecting this study. Source README, tree metadata and loader/scorer code were inspected for suitability. Five datasets are the default official benchmark subset; tax is an extension and toy is a demonstration control. Report these strata separately; do not select only favorable datasets. An inaccessible, malformed, too-large or unlicensed-to-access instance remains an explicit excluded row. There is no replacement chosen after inspecting outcomes.

Maximum local processing scope: all rows/cells of these seven fixed pairs, roughly40MB source size. Record source bytes/hash, dimensions, headers, NA policy and row identity contract. Upstream source code is Apache-2.0; dataset-specific origin and licenses require separate tracing. No third-party CSV is redistributed in the submission. Use authenticated authorized read-only source access and pinned restoration manifests; stop on platform denial without switching identity. Canonical DataHub registration remains paused by user scope; keep provenance local.

The sources are upstream-authored benchmark pairs, not seven natural-error gold sets. Hospital and tax have synthetic-error provenance; beers/rayyan natural-error provenance must be tied to the official research description. Unverified provenance stays unknown. No LLM or new author corruption supplies natural gold.

## Endpoints fixed before data inspection

E1, primary consumer label contract: compare raw CSV string inequality per agreed row/column with the unchanged official loader's normalization (HTML decoding, whitespace handling and stripping) and official error-label function. Independently implement parsing/normalization and verify every loaded cell and label. Count raw labels, native labels, removed/added label coordinates, affected rows/columns and source strata. Neither raw strings nor native normalization is assumed to define business truth. Differences are contract sensitivity, not automatically mislabeled benchmark defects.

E2, primary persistence contract: test N(N(x))=N(x) on the existing raw cells, then invoke an unchanged official export/load path when available. Measure every naturally present round-trip value and label change. If no export API is applicable, explicitly report a controlled CSV serialization probe rather than a native workflow. Do not invent a promise of idempotence absent from the source. Distinguish raw-to-native change from native-to-reloaded change.

E3, score consequence: evaluate a complete correctly normalized clean-value correction dictionary and a raw-clean-value adapter dictionary with the unchanged official evaluator, at the same native error coordinates. Also compare label-count consequences on the entire fixed raw/native coordinate set. Independently recompute detection and correction precision/recall/F1 under the same official contract. These are controlled adapter/oracle probes; they are not repair algorithms, new natural errors, operational performance or evidence that published rankings changed. For zero-denominator cases preserve the official return convention and record it.

E4, identity and correct controls: inspect whether a stable external row key is provided; if IDs are only positional, state that underlying real-entity alignment cannot be certified from the files. Native existing data is unmodified. A self-pair and correctly mapped normalized-clean probe provide deterministic negative/positive checker controls. Any constructed invalid coordinate or header-mapping controls are separately labeled as author sensitivity checks. Never independently permute an order-identified file and call the resulting invalid input a native bug.

## Execution and reporting

Read and hash all upstream executable code before execution; use existing approved runtimes/dependencies, no installation/account registration. Persist native method return values, independent results, all per-dataset outcomes and deterministic aggregate artifacts. Avoid storing raw source values in distributed reports when source redistribution rights are uncertain: use coordinates, hashes, counts and restoration/recomputation commands. Preserve implementation/version and full source manifests locally.

Success is complete auditable execution of eligible fixed cases and agreement between native and independent evaluation, not discovery of a positive defect. Any native disagreement, unexpected parser behavior or licensing restriction stops the affected inference and is investigated. All-negative results must be retained. No performance, business gold, prevalence, or actual downstream publication-impact claim follows from this study.
