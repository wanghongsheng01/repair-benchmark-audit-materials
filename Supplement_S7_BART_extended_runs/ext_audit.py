#!/usr/bin/env python3
"""Audit extension runs with the unchanged per-case checker of the generator audit."""
from pathlib import Path
import argparse, json, sys, importlib.util
ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('audit_external', ROOT / 'audit_external.py')
ax = importlib.util.module_from_spec(spec); spec.loader.exec_module(ax)
def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--run-dir', type=Path, required=True); ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args(); a.out.mkdir(parents=True, exist_ok=True)
    manifest = ax.read(a.run_dir / 'run_manifest.json'); rows = []; failed = []
    for rec in manifest:
        ax.require(ax.read(a.run_dir / rec['case_id'] / 'run_receipt.json') == rec, 'receipt differs from manifest')
        if not rec['completed']: failed.append({'case_id': rec['case_id'], 'reason': rec.get('error', 'nonzero exit')}); continue
        try:
            row, ctrl = ax.audit_case(a.run_dir / rec['case_id'], a.out)
            row['execution_basis'] = 'extension run'; row['controls_passed'] = len(ctrl); rows.append(row)
        except Exception as e:
            failed.append({'case_id': rec['case_id'], 'reason': 'checker: ' + str(e)})
    (a.out / 'cases.json').write_text(json.dumps(rows, indent=2) + '\n')
    (a.out / 'failed.json').write_text(json.dumps(failed, indent=2) + '\n')
    for r in rows: print(r['case_id'], r['rows'], r['cells'], r['events'], r['realized_changes'], r['unexplained_changes'], r['unrealized_nonnoop_events'], r['event_value_mismatches'], r['noop_events'], r['wiki_contract_mismatches'], r['implementation_contract_mismatches'], r['positional_cell_differences'])
    print('failed', failed)
if __name__ == '__main__': main()
