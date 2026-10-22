# CSV-only BART matching control

**Observed result: conventional minimum-Hamming relation matching suffices for
all four saved cases.** Every optimal assignment recovers all six native change
labels and their clean target values, and all three zero-event controls have
zero false-positive cells. This experiment provides no material ambiguity
witness and does not establish that additional identity observations are
necessary to obtain these semantic results.

This is one exploratory follow-up to the existing current A2 observations, not four
new runs or an increase in external sample size. The data remain one nonzero
random-injection case and three zero-event controls (30 rows, 118 cells per
snapshot side). There was no upstream execution, new corruption, seed choice,
synthetic substitute for natural truth or modification of the original study files.

## Frozen inputs and chronology

All times below are actual local UTC observations on 2026-10-09; the records
are not externally registered or trusted timestamps. Before the initial
freeze the implementer had read the independent current review and BART manuscript
section and inspected the saved CSV headers/row counts. Those texts already
reported native event and positional counts; new minimum-assignment results
were not available. No OID, sidecar or native event was read until after sealing.

| Event | UTC | Record |
|---|---|---|
| Initial input/code/protocol freeze | 02:52:39.013684Z | `protocol/FREEZE.json` |
| Operational amendment A1 frozen | 02:53:20.399154Z | `protocol/FREEZE_A1.json` |
| Blind result sealed | 02:53:37.211589Z | `seals/BLIND_SEAL.json` |
| Native reveal started after seal verification | 02:54:02.726707Z | `seals/REVEAL_START.json` |
| Reveal/scoring result sealed | 02:55:43.885037Z | `seals/REVEAL_SEAL.json` |
| Fresh local reproduction passed | 02:57:20.821927Z | `verification/local_replay/REPRODUCTION_RESULT.json` |

The initial execution failed closed when a lazy standard-library UTF-8-BOM
codec import attempted a file read after the guard was installed. No comparison
result was computed. A1 preloads that codec and uses installed Python 3.12,
meeting the declared Python 3.10+ requirement. No input, cost or output rule
changed. Both frozen versions and their hashes remain available.

- Effective freeze SHA-256: `4926308703775fb71fe9b0f6ad669d26ef669771b276ed62687e3281e47fa66e`.
- Sealed blind result SHA-256: `92f40a813cc1f33f5bf0090d783d64d8663d220a9f1167833295fd46e878e882`.
- Sealed reveal result SHA-256: `223161956f166151ef39726bc2e30f9f2aab97ed60b7be72eba92ca31018872b`.

The eight copied CSVs have byte-level hashes in the effective freeze. The
matcher records exactly those eight data reads. Its fail-closed open audit hook
rejects other data files; standard-library imports occur before the guard.
The later reveal adapter is a separate process. This is an auditable information
boundary in the executed code, not an OS sandbox or analyst-unawareness claim.

## Prespecified methods and complete optimum retention

Position pairs the ith clean and dirty row. The multiset baseline uses Counter
over complete row tuples and preserves duplicates; it reports bag equality and
unmatched multiplicities, without pretending to locate cells for unequal bags.
The assignment baseline minimizes total unit-weight, exact-string Hamming
distance over bijective dirty-to-clean row mappings, using every column and no
chosen key, normalization or event information. The maximum case has 12 rows.

The standard-library subset DP stores the complete globally optimal assignment
DAG, exact path count, prefix/suffix counts, all supported row bindings and
each cell's possible targets/change labels. All optima are also enumerated here
(the maximum count is two). Reveal scoring uses additive minimum/maximum DP
restricted to that sealed DAG, with endpoint witness assignments; exhaustive
enumeration independently checks those score extrema within the scorer.

## Results

| Case | Rows / cells | Native events | Position unequal cells | Multiset equal | Minimum Hamming cost | Optimal assignments | Materially ambiguous cells |
|---|---:|---:|---:|:---:|---:|---:|---:|
| employees | 8 / 32 | 0 | 24 | yes | 0 | 1 | 0 |
| employees-random | 8 / 32 | 6 | 25 | no | 6 | 1 | 0 |
| employees-symmetric | 12 / 48 | 0 | 31 | yes | 0 | 2 | 0 |
| synthetic-01 | 2 / 6 | 0 | 0 | yes | 0 | 1 | 0 |

The random case's multiset difference contains five unmatched rows on each
side. This is a row-bag inequality result, not six localized cell edits.
All three controls have equal multisets and no bag-level alarms.

The reference adapter verifies that each clean/dirty CSV row exactly agrees
with its saved native export crosswalk, that clean/dirty native OID sets agree,
and that native event JSON, exported event CSV and identity-aligned actual
changes agree. All checks pass. The true identity assignment is an optimum in
every case; no unique optimum contradicts the native identity reference.

For minimum-Hamming matching, every metric bound collapses to one value:

| Endpoint | employees | random | symmetric | synthetic |
|---|---:|---:|---:|---:|
| Correct change labels / cells | 32/32 | 32/32 | 48/48 | 6/6 |
| Correct clean target values / cells | 32/32 | 32/32 | 48/48 | 6/6 |
| TP / FP / FN | 0 / 0 / 0 | 6 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| Correct changed-cell repair values | 0 | 6 | 0 | 0 |

On the random case, cell precision/recall and repair-value precision/recall are
all 1 for every optimum. On zero-event cases their zero-denominator precision
and recall values remain JSON `null`, alongside zero predicted changes and
zero errors; undefined rates are not converted to one. Label and all-cell
target-value accuracy are defined and equal to one on all cases.

The positional comparator has 24, 19, 31 and 0 false-positive cells respectively.
On the random case it labels all six actual changes but also 19 other cells;
only one of its 25 proposed cell targets correctly repairs a true changed cell.
Thus its cell precision is 6/25 and recall is 1; repair-value precision is 1/25
and recall is 1/6. These scores concern saved observations, not cleaning methods.

The exact native six-change witness is:

| Dirty CSV row | Native OID | Attribute | Dirty string | Clean target string |
|---:|---:|---|---|---|
| 2 | 36 | salary | `1000.0-*` | `1000.0` |
| 3 | 21 | name | `Bob-*` | `Bob` |
| 3 | 21 | manager | `John-*` | `John` |
| 6 | 51 | name | `Frank-*` | `Frank` |
| 7 | 31 | name | `John-*` | `John` |
| 8 | 41 | salary | `2000.0-*` | `2000.0` |

## Why the two symmetric optima are not material ambiguity

The complete dirty-to-clean assignments (1-based data-row indices) are:

```text
[11, 2, 4, 10, 12, 1, 6, 8, 7, 9, 3, 5]
[12, 2, 4, 10, 11, 1, 6, 8, 7, 9, 3, 5]
```

They exchange clean rows 11 and 12, both exactly
`[Jess, Shipping, 1500, Carl]`, at dirty rows 1 and 5. Native OIDs are 71 and 76;
the first assignment preserves all native IDs, while the second preserves
10/12. Both preserve all 48 clean values and all 48 unchanged labels. The data
therefore leave a duplicate-row identity permutation unresolved, while leaving
no uncertainty in any tested label or repair value. Counting that permutation
as material ambiguity would overstate the result.

## Implication for the manuscript

The existing positional failure is reproducible, but defeating position
comparison does not show that the paper's extra identity observation is
necessary. Duplicate-preserving multisets already eliminate all zero-event
false alarms here; standard one-to-one minimum-Hamming matching additionally
recovers all six event labels and target values. The manuscript should report
that conventional matching suffices for these saved cases and remove the
inference that they establish necessity of an identity sidecar.

Native identities still provide an independent scoring reference and distinguish
the two identical tuples; that is different from proving their necessity for
recovering the observed value changes. A unique minimum-cost assignment is only
unique under its model, not a certificate of real identity in arbitrary data.
The version-specific event-column documentation/adapter finding remains a
separate evidence claim. This control establishes neither broad prevalence,
native generator error, affected published results, business truth nor production
utility. No favorable result was required for the control to count as complete.

## Deliverables and remaining gates

`results/summary.csv` supplies the manuscript table. The full blind/reveal JSONs
retain all case outputs, exact bounds and witness assignments. The README gives
a local portable reproduction command, and the fresh replay passes with all
substantive outputs identical. The portable archive includes only this new
analysis and authorized author-generated observations, not upstream XML/JAR/code.
Independent implementation review and workspace backup are coordinated by the
parent task; this report does not claim either is already complete.
