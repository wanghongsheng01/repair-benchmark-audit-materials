# Extended BART generator runs

Repeated, constraint-driven and larger-table runs of the BART generator audit: 90 runs over three main-memory tasks, audited with the unchanged per-case checker and the CSV-only matching control. Read `PROTOCOL_EXTENSION.md` first, then `EXTENSION_RESULTS.md`.

## Offline re-analysis (no Java, no network)
Requirements: Python 3.9+, NumPy and SciPy.
```
python3 ext_audit.py --run-dir runs/employees-random-egtask --out reaudit/employees-random-egtask
python3 ext_audit.py --run-dir runs/employees-viogen-egtask --out reaudit/employees-viogen-egtask
python3 ext_audit.py --run-dir runs/employees50-viogen-random-egtask --out reaudit/employees50-viogen-random-egtask
python3 ext_match.py --runs-root runs --output rematch.json
python3 ext_reveal.py --sealed rematch.json --sealed-sha256 "$(sha256sum rematch.json | cut -d' ' -f1)" --runs-root runs --output rematch_revealed.json
```
The audit outputs reproduce `audit/*/cases.json`; the matching outputs reproduce `match_sealed.json` and `match_revealed.json`.

## Regenerating runs (Java 21, network for the BART checkout)
```
git clone https://github.com/dbunibas/BART bart_src && git -C bart_src checkout 354f503f401d5360e9a6957f4edd096d3dc413f6
python3 restore_from_git.py --checkout bart_src
python3 build_native.py --java-home /path/to/jdk
python3 ext_run.py --java /path/to/jdk/bin/java --task upstream_local/source/Bart_Engine/misc/resources/employees/employees-random-egtask.xml --runs 30 --out new_runs/employees-random-egtask
python3 ext_run.py --java /path/to/jdk/bin/java --task ext_tasks/employees-viogen-egtask.xml --runs 30 --out new_runs/employees-viogen-egtask
python3 ext_run.py --java /path/to/jdk/bin/java --task ext_tasks/employees50-viogen-random-egtask.xml --runs 30 --out new_runs/employees50-viogen-random-egtask
python3 ext_scorer.py --java /path/to/jdk/bin/java --out new_scorer
```
BART's random number generator is not seeded, so new runs produce different events; report them separately and do not select among runs.

## Contents
- `runs/`: 90 run directories with native snapshots, events and exported CSV files; `pilot/`: the three pre-freeze feasibility runs.
- `audit/`, `pilot_audit/`: per-case checker outputs.
- `match_sealed.json` and its hash, `match_revealed.json`: CSV-only matching before and after identity revelation.
- `scorer/`: native scorer scores of the two orientation probes for the 86 event-bearing runs.
- `ext_tasks/`: the two derived task files. They contain data and constraints from the BART repository, redistributed under its MIT licence (`LICENSE_BART_MIT.txt`).
