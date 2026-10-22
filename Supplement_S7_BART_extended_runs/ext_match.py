#!/usr/bin/env python3
"""CSV-only matching for the extension runs. Reads only clean_*.csv and dirty_*.csv
(enforced by a fail-closed audit hook) and writes one sealed result file.

Exact minimum-total-Hamming assignment. For each dirty row, the set of clean rows it
is matched to in at least one optimal assignment: subset dynamic program for <= 12 rows
(original control), forced-pair Hungarian test for larger tables. Both are run on every
table of <= 12 rows and must agree."""
import argparse, csv, hashlib, io, json, os, sys
from pathlib import Path
import numpy as np
from scipy.optimize import linear_sum_assignment
linear_sum_assignment(np.zeros((2, 2)))  # load native code before the read guard
import importlib.util
ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('csv_only_dp', ROOT / 'csv_only_dp.py')
dp = importlib.util.module_from_spec(spec); spec.loader.exec_module(dp)

def read_csv(p):
    data = p.read_bytes(); rows = list(csv.reader(io.StringIO(data.decode('utf-8-sig'), newline='')))
    return rows[0], rows[1:], hashlib.sha256(data).hexdigest()

def forced_pair_support(cost):
    c = np.array(cost); n = len(c); r, k = linear_sum_assignment(c); best = int(c[r, k].sum())
    support = [set() for _ in range(n)]
    for i in range(n):
        for j in range(n):
            rest = np.delete(np.delete(c, i, 0), j, 1)
            if rest.size:
                rr, kk = linear_sum_assignment(rest); val = int(c[i, j] + rest[rr, kk].sum())
            else:
                val = int(c[i, j])
            if val == best: support[i].add(j)
    return best, support

def analyze(case_dir, table):
    h, clean, cs = read_csv(case_dir / f'clean_{table}.csv'); h2, dirty, ds = read_csv(case_dir / f'dirty_{table}.csv')
    assert h == h2 and len(clean) == len(dirty)
    cost = [[sum(a != b for a, b in zip(d, c)) for c in clean] for d in dirty]
    best, support = forced_pair_support(cost)
    out = {'case_id': case_dir.name, 'rows': len(clean), 'cells': len(clean) * len(h), 'input_sha256': {'clean': cs, 'dirty': ds},
           'optimal_total_hamming_cost': best, 'method': 'forced-pair Hungarian'}
    if len(clean) <= 12:
        ex = dp.exact_assignment(clean, dirty, h)
        dp_support = [set(j - 1 for j in b['clean_rows_1based']) for b in ex['possible_row_bindings']]
        assert ex['optimal_total_hamming_cost'] == best, 'DP and Hungarian optimum differ'
        assert dp_support == support, 'DP and Hungarian support differ'
        out['method'] = 'subset DP, cross-checked by forced-pair Hungarian'
        out['optimal_assignment_count'] = ex['optimal_assignment_count']
    cells = []
    for i, d in enumerate(dirty):
        for k, attr in enumerate(h):
            vals = sorted({clean[j][k] for j in support[i]}); labels = sorted({d[k] != v for v in vals})
            cells.append({'dirty_row': i, 'attribute': attr, 'targets': vals, 'labels': labels})
    out['row_support'] = [sorted(s) for s in support]; out['cells_detail'] = cells
    out['material_ambiguity_cells'] = sum(len(c['targets']) > 1 or len(c['labels']) > 1 for c in cells)
    out['positional_changed_cells'] = sum(clean[i][k] != dirty[i][k] for i in range(len(clean)) for k in range(len(h)))
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--runs-root', type=Path, required=True); ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args(); root = a.runs_root.resolve(); output = a.output.resolve()
    cases = []
    for task in sorted(p for p in root.iterdir() if p.is_dir()):
        for case in sorted(p for p in task.iterdir() if p.is_dir()):
            cases.append(case)
    allowed = {str(c / f'{s}_emp.csv') for c in cases for s in ('clean', 'dirty')}
    def hook(event, args):
        if event != 'open': return
        path, mode, flags = args
        if not isinstance(path, (str, bytes, os.PathLike)): return
        p = os.path.abspath(os.fsdecode(path)); writing = flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
        if writing:
            if p != str(output): raise PermissionError('write outside sealed result: ' + p)
        elif p not in allowed and not p.endswith('.py') and '/site-packages/' not in p and '/lib/python' not in p:
            raise PermissionError('read outside clean/dirty CSVs: ' + p)
    sys.addaudithook(hook)
    results = [dict(task=c.parent.name, **analyze(c, 'emp')) for c in cases]
    with output.open('x') as f: json.dump({'phase': 'CSV-only matching, before native identities are read', 'cases': results}, f, indent=1, sort_keys=True); f.write('\n')
if __name__ == '__main__': main()
