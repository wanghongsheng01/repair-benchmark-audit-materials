# BART blind matching control

The prespecified conventional minimum-Hamming matcher recovers every native
change label and repair value in these four saved cases. All optima recover the
same semantics: six changes in one random case, no changes in three controls.
The symmetric control has two optimum identity assignments, but its exchanged
rows have identical values; this is not material label/repair-value ambiguity.
This control therefore does **not** support the necessity of extra identity
observations for the observed CSVs. See [RESULTS.md](RESULTS.md).

## Local reproduction

Requirements: Python 3.10+ and its standard library. No network, upstream Java,
dependency installation, existing research workspace or absolute source path is
needed. From any copy/unpacked version of this directory:

```sh
python3 code/reproduce.py --output-dir replay
```

`replay` must not already exist. The command verifies frozen hashes and the
initial archived matcher; starts a fresh CSV-only guarded process; checks all
substantive results against the sealed result; seals the fresh blind output;
and then runs native-reference scoring in a separate process. UTC fields and
the resulting new blind-output digest are expected to differ. A successful run
writes `replay/REPRODUCTION_RESULT.json` with `status: PASS`.

To run the phases explicitly (output files must not exist):

```sh
python3 code/blind_matcher.py --input-root inputs/blind_csv --output fresh-blind.json
# Hash and record fresh-blind.json before running the reference scorer.
python3 code/reveal_and_score.py --package-root . --blind-results fresh-blind.json --output fresh-reveal.json
```

The explicit scorer verifies the original frozen experiment's seals. Use the
reproduction driver for an automatically recorded fresh blind-before-reveal seal.

## Package boundary

- `inputs/blind_csv/`: byte-preserved copies of exactly eight saved native CSVs
  (four clean/dirty pairs), 30 rows and 118 cells on each snapshot side.
- `code/blind_matcher.py`: position, Counter-based multiset, exact one-to-one
  minimum-Hamming matching. It opens only those eight data files and its output;
  contains no OID, event or identity adapter input.
- `results/blind_results.json`: complete cost matrices, optimal DAGs/counts,
  supported bindings/cell values/labels and all optima (counts are small here).
- `reveal/`: only author-generated native export crosswalks and event observations,
  copied after sealing. They supply reference identity for scoring, not matcher input.
- `code/reveal_and_score.py`: validates CSV/native observations and event
  concordance, then computes exact score bounds on the sealed DAG. Endpoint
  assignments and enumeration cross-checks are retained.
- `protocol/` and `seals/`: local, actual UTC chronology and SHA-256 chain.
- `RESULTS.md` and `results/summary.csv`: scoped findings and tabular summary.

No BART XML, JAR, source tree, dependency or third-party dataset distribution is
included. These are the already-authorized author-generated observations of
the four saved BART runs, plus newly authored analysis and reporting. Upstream
provenance is the original fixed BART commit
`354f503f401d5360e9a6957f4edd096d3dc413f6`; no upstream program was rerun here.
The original study files were not modified.

## Freeze amendment and interpretation

The initial frozen execution failed closed when system Python tried to lazily
load its optional-BOM codec after the read guard was installed. No matching
result was computed. Amendment A1 preloaded this standard-library codec and
used installed Python 3.12, meeting the declared Python 3.10+ requirement. All
inputs, costs and output rules were unchanged. `FREEZE.json` records the first
source hash; the exact first source is retained as
`protocol/blind_matcher_frozen_initial.py`. `FREEZE_A1.json` is the effective
full input/code manifest for the successful blind run. This is a transparently
logged operational amendment, not a hidden replacement of the original freeze.

The local freeze records were created before the new assignment results and
native reveal. The analyst already knew current's reported native and positional
counts. This is an exploratory follow-up, not an unseen-data preregistration;
hashes and local timestamps do not constitute an external trusted timestamp.
The saved native event contract is a reference for this experiment, not natural
business truth or proof that a unique cost optimum certifies real identity.
