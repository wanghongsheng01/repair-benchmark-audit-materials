# External paired-benchmark audit protocol

Status: FROZEN before external candidate page/source/data/results inspection in this delegated task.
Freeze time (local system UTC): 2026-10-08T09:25:33.349047+00:00
This is a local preregistration, not an externally timestamped registration. The receipt records the actual system clock; no earlier time is claimed.

## Question and atomic claim
Does an independently authored public corruption benchmark preserve the clean input outside its declared corruption events, and can a portable paired-invariant audit distinguish a correct construction from an intentionally mismatched pair? This audits benchmark construction/provenance, not business truth or repair superiority.

## Candidate selection fixed before inspection
1. First inspect the official BART candidate https://db.unibas.it/projects/bart/ without presuming any defect. Independently authored means not authored or adapted by the study author.
2. Prefer the complete bounded shipped sample/test corpus of a pinned release/commit, with original clean input, corrupted output, and independently produced event/change metadata. Preserve all eligible cases; no selection by audit result.
3. BART is eligible for the primary paired audit only where stable row/attribute identities and event semantics are recoverable and at least one actual before/after pair is obtainable. If execution is needed, inspect relevant source and dependencies first and request mandatory platform approval; do not execute upstream code after denial.
4. If BART lacks obtainable compatible pair/event artifacts or execution is blocked, record the reason and evaluate an independently authored public benchmark with released clean/dirty tables and authoritative error/change labels (official author source only). Limit candidates to BART, HoloClean public datasets, and REIN benchmark datasets in that order. Do not silently change the estimand to achieve a finding.
5. Public readability does not confer redistribution rights. Preserve license/provenance. When permission is unclear ship original author-authored restoration code plus URL/commit/hash and derived non-content results; do not redistribute upstream raw data.

## Primary endpoint (not guaranteed by benchmark definition)
For every eligible shipped case, independently parse the actual clean and dirty artifacts. Align rows by declared identity, preserving value types and multiplicity where present. Let Δ be all cells/occurrences whose actual values differ. Let A be the set/multiset of changes independently recorded/authorized by upstream events or authoritative labels. Report (a) unexplained realized changes Δ\A, (b) recorded changes not realized A\Δ, and (c) value/identity inconsistencies. When events permit no-op replacements, A\Δ is reported separately as no-op rather than a defect. The primary endpoint is the fraction and count of eligible original cases with nonempty unexplained changes. Event records must not be generated from the observed diff being tested. If only clean/dirty truth is published, event-concordance is not identifiable: report that endpoint as unavailable and use a separately named secondary endpoint, never claim primary success.

## Secondary endpoints and material consequence
Report identity uniqueness, shape/schema alignment, clean-cell preservation outside event targets, duplicate/ambiguous/missing event references, exact before/after agreement with event values, and label precision/recall relative to independent actual diff when independently supplied labels exist. Record complete denominators. A discrepancy is evidence of an artifact-contract mismatch, not automatically a benchmark implementation defect. Trace causality to source/documentation before naming a defect. Where event oracles are absent, parse upstream independently authored expected test assertions and label them as such; no fabricated gold.

## Controls fixed in advance
Correct negative controls: (i) clean input paired with its byte-identical copy and an empty event list; (ii) an actual clean/dirty pair with upstream events (if the original passes), retaining full original identities. A deliberately mismatched clean control is a sensitivity control, not external evidence: perturb one permitted scalar value outside the original event target set using a author-written wrapper and record its exact input/event hashes and expected discrepancy. Prefer at least one native correct benchmark case; wrapper cases do not count toward external cases. A dirty table compared against itself plus empty events must pass but is only a parser/control check. Never count definition-guaranteed controls as scientific primary evidence.

## Complete reporting and stopping
Record official URLs, resolved version, fetch timestamps, SHA-256, license assessment, every selected/excluded case, input schema and hashes, event/expected basis, all endpoint results, parser exceptions, and environment. No performance superiority or cross-benchmark prevalence claims. Stop at the full bounded shipped test/sample corpus or first eligible official released dataset group (whichever candidate is first feasible); state exact coverage. Do not cherry-pick a failing seed. If no eligible primary case is obtainable, say M1 remains partially satisfied and explain the missing evidence.

## Analysis implementation
Use newly authored standard-library parser/checker code wherever possible. Keep its implementation independent of the repair code. The checker must fail closed on duplicate IDs, incompatible schema, or unrecognized event syntax. Record program SHA-256 and re-run in a clean temporary directory using only the packaged source/manifests and authorized upstream input restoration. Preserve all originally frozen files. Any protocol amendment must have a new timestamp/hash before the affected result inspection, explain the need, and separate confirmatory and exploratory outcomes.

## Environment/data routing
`datahub list` was run before external source access. Existing catalog has no BART/HoloClean/REIN public benchmark module. Mapping: new read-only source requiring provenance registration; external source remains read-only. Registration work must not expand this manuscript task; report any missing registration prerequisite. User explicitly forbids push/public sharing, overriding generic backup instructions; preserve local outputs only and report backup status accurately.
