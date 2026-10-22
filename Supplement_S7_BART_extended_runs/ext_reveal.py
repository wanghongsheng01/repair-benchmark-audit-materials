#!/usr/bin/env python3
"""Reveal native identities after the CSV-only result is sealed, and score it."""
import argparse, csv, hashlib, json
from pathlib import Path
def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--sealed', type=Path, required=True); ap.add_argument('--sealed-sha256', required=True)
    ap.add_argument('--runs-root', type=Path, required=True); ap.add_argument('--output', type=Path, required=True); a = ap.parse_args()
    assert hashlib.sha256(a.sealed.read_bytes()).hexdigest() == a.sealed_sha256, 'sealed result changed'
    sealed = json.loads(a.sealed.read_text()); out = []
    for c in sealed['cases']:
        case = a.runs_root / c['task'] / c['case_id']
        clean_snap = json.loads((case / 'clean_snapshot.json').read_text())['emp']
        dirty_snap = json.loads((case / 'dirty_crosswalk_before_export.json').read_text())['emp']
        clean_rows = list(csv.reader((case / 'clean_emp.csv').open(newline='')))
        dirty_rows = list(csv.reader((case / 'dirty_emp.csv').open(newline='')))
        h = clean_rows[0]; clean = clean_rows[1:]; dirty = dirty_rows[1:]
        clean_index = {r['oid']: i for i, r in enumerate(clean_snap)}
        truth = [clean_index[r['oid']] for r in dirty_snap]   # dirty CSV row i -> clean CSV row (CSV order equals snapshot order, checked by the audit)
        native_in_support = all(truth[i] in c['row_support'][i] for i in range(len(dirty)))
        correct_labels = correct_targets = ambiguous = 0; fp = fn = 0
        for cell in c['cells_detail']:
            i = cell['dirty_row']; k = h.index(cell['attribute']); t = clean[truth[i]][k]; lab = dirty[i][k] != t
            if len(cell['targets']) > 1 or len(cell['labels']) > 1: ambiguous += 1; continue
            correct_targets += cell['targets'][0] == t; correct_labels += cell['labels'][0] == lab
            fp += cell['labels'][0] and not lab; fn += (not cell['labels'][0]) and lab
        true_changed = sum(dirty[i][k] != clean[truth[i]][k] for i in range(len(dirty)) for k in range(len(h)))
        identical_clean_rows = len(clean) - len({tuple(r) for r in clean})
        out.append({'task': c['task'], 'case_id': c['case_id'], 'rows': c['rows'], 'cells': c['cells'], 'true_changed_cells': true_changed,
                    'unique_cells': c['cells'] - ambiguous, 'ambiguous_cells': ambiguous, 'correct_targets': correct_targets, 'correct_labels': correct_labels,
                    'false_positive_labels': fp, 'false_negative_labels': fn, 'native_assignment_optimal': native_in_support,
                    'optimal_assignment_count': c.get('optimal_assignment_count'), 'duplicate_clean_rows': identical_clean_rows,
                    'semantic_recovery_supported': ambiguous == 0 and correct_targets == c['cells'] and correct_labels == c['cells'] and native_in_support})
    a.output.write_text(json.dumps(out, indent=1) + '\n')
if __name__ == '__main__': main()
