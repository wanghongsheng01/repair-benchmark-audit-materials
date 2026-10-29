# Supplement S8: comparison-contract audit of a redistributed outlier-detection benchmark

Supplement to "Comparison contracts for benchmark evaluation: attributing score discrepancies in data
cleaning and outlier detection" (H. Wang, X. Liang), Section 6, Tables 8 and 9 and Fig. 2.
Corresponding author: Hongsheng Wang, wanghongsheng@zju.edu.cn.

The audit compares the 19 `Classical` files of ADBench (commit 3dac8221081e190f157d78e93bfa8867f90d0965) that
share a dataset name with the DAMI outlier-evaluation repository of Campos et al. (DMKD 30(4), 2016) against
every DAMI variant of the same name, reproduces the published native ELKI results with an independent NumPy
implementation, and measures how the correspondence between names and variants moves scores and rankings.
No third-party data are redistributed; `code/fetch_inputs.sh` downloads them and checks their hashes.

## Contents
| Path | What it is |
|---|---|
| `protocol/PROTOCOL_S8.md` | Protocol frozen on 29 Oct 2026 before any data file was parsed, with amendments A1-A5 (all made on the same day) |
| `protocol/input_hashes_at_freeze.sha256` | SHA-256 of the DAMI tarballs and the 19 ADBench files, recorded at freezing |
| `code/fetch_inputs.sh` | Downloads all public inputs (about 135 MB) and verifies the hashes |
| `code/s8_lib.py` | ARFF/NPZ readers, multiset matching, KNN/KNNW detectors, ROC AUC with ties counted one half |
| `code/e1_e2_inventory_correspondence.py` | E1 inventory and E2 correspondence |
| `code/e3_e4_scores.py` | E3 native control and E4 score sensitivity |
| `code/e5_minmax.py` | E5, amendment A3: scores after whole-file min-max scaling |
| `code/e6_rankings.py` | E6, amendment A4: rankings of the twelve native detectors (native results only) |
| `code/analyze.py`, `code/make_outputs.py` | Summaries, Table 8 rows, Fig. 2 and `results/headline.json` |
| `code/e3b_residuals.py` | E3b: are non-exact native values associated with tied detector scores? |
| `code/e6b_rankings_robust.py` | E6b, amendment A5: best-detector changes with a replicate noise floor, tolerance 0.01, three measures (replaces E6 in the paper) |
| `code/e7_planted.py` | E7, amendment A5: 98 planted perturbations with known causes |
| `code/e8_aloi_rows.py` | E8: the 27 ALOI rows that differ from the deduplicated DAMI variant |
| `code/lof.py` | A LOF re-implementation that did not reproduce the native values; kept, not used |
| `results/` | All outputs: `e1_e2.json`, `e3_e4.json`, `e5_minmax.json`, `e6_rankings.json`, `summary.json`, `headline.json`, `e3b_residuals.json`, `e6b_rankings_robust.json`, `e7_planted.json`, `e8_aloi_rows.json`, `table_s8.tex`, `Fig2.pdf`, `crosswalk_adbench_to_dami.csv`, `native_eval_hashes.sha256` |

## Reproduce
Requires Python 3.9+ with NumPy and Matplotlib, `curl`, `tar` and `shasum`.
```
sh code/fetch_inputs.sh
python3 code/e1_e2_inventory_correspondence.py
python3 code/e3_e4_scores.py          # about 10 minutes on a laptop
python3 code/e5_minmax.py
python3 code/e6_rankings.py
python3 code/e6b_rankings_robust.py
python3 code/e3b_residuals.py
python3 code/e7_planted.py
python3 code/e8_aloi_rows.py
python3 code/analyze.py
python3 code/make_outputs.py
```
The native evaluation files are served by the DAMI web site and were not hashed at freezing; their hashes at
download time are in `results/native_eval_hashes.sha256`.

## Licences
Code in this supplement: MIT. DAMI data and results: see https://www.dbs.ifi.lmu.de/research/outlier-evaluation/DAMI/.
ADBench: BSD-2-Clause, https://github.com/Minqi824/ADBench.

## Use of AI tools
Claude (Anthropic) wrote and executed the scripts under the authors' supervision; the authors reviewed the code
and results.
