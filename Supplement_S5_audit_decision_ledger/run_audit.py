"""Replay bounded audit decisions using only the portable summary input.

No original source path from provenance is opened. Run from any working directory.
"""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
from audit_rules import evaluate_record
from build_inputs import parse

HERE = Path(__file__).resolve().parent


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def validate_inventory(bundle, profile=None):
    issues = []
    if bundle.get('schema') != 'audit-contract-evidence':
        issues.append('unsupported input schema')
    expected = bundle.get('expected_inventory')
    if not isinstance(expected, dict) or set(expected) != {'generator','consumer','reference_certificate'}:
        return ['missing/unsupported explicit inventory']
    if profile is None:
        profile = parse((HERE / 'inventory_profile.json').read_text())
    if expected != profile.get('expected_inventory'):
        issues.append('input inventory differs from separately pinned scope profile')
    all_records = bundle.get('records', []) + bundle.get('certificate_evidence_index', []) + bundle.get('current_software_examples', [])
    for family, ids in expected.items():
        actual = [x.get('case_id') for x in all_records if x.get('family') == family]
        if not isinstance(ids, list) or len(ids) != len(set(ids)) or sorted(actual) != sorted(ids) or len(actual) != len(set(actual)):
            issues.append('missing/duplicate/unexpected case in ' + family)
    for x in all_records:
        if x.get('family') not in expected:
            issues.append('unknown evidence family')
        if not isinstance(x.get('requested_claims'), list) or not x['requested_claims'] or len(set(x['requested_claims'])) != len(x['requested_claims']):
            issues.append('missing/duplicate proposition selection')
        if not x.get('scope'):
            issues.append('missing scope')
    return issues


def summarize(bundle, evaluated):
    empirical = evaluated[:len(bundle['records'])]
    cert = evaluated[len(bundle['records']):len(bundle['records']) + len(bundle['certificate_evidence_index'])]
    generator = [(x, y) for x, y in zip(bundle['records'], empirical) if x['family'] == 'generator']
    consumer = [(x, y) for x, y in zip(bundle['records'], empirical) if x['family'] == 'consumer']
    def outcomes(rows):
        out = {}
        for _, y in rows:
            for k, v in y['decisions'].items():
                out.setdefault(k, Counter())[v['status']] += 1
        return {k: dict(v) for k, v in out.items()}
    # Summary counts come from decision measurements, not expected success constants.
    b = []
    for x, y in generator:
        d = y['decisions']
        b.append({'case_id': x['case_id'], 'rows': x['facts'].get('rows'), 'cells': x['facts'].get('cells'),
                  'events': d.get('native_event_fidelity', {}).get('measurements', {}).get('events'),
                  'position_fp': d.get('position_semantic_equivalence', {}).get('measurements', {}).get('fp'),
                  'position_differences': d.get('position_semantic_equivalence', {}).get('measurements', {}).get('apparent_changes'),
                  'zero_event_false_alarm': d.get('position_semantic_equivalence', {}).get('measurements', {}).get('zero_event_false_alarm'),
                  **d.get('csv_all_optima_determinacy', {}).get('measurements', {})})
    c = []
    for x, y in consumer:
        d = y['decisions'].get('raw_direct_value_equivalence', {})
        c.append({'case_id': x['case_id'], 'rows': x['facts'].get('rows'), 'cells': x['facts'].get('cells'),
                  'stratum': x['facts'].get('stratum'), 'raw_direct_equivalence': d.get('status'),
                  'raw_hits': d.get('measurements', {}).get('raw_hits'), 'native_labels': d.get('measurements', {}).get('native_labels'),
                  'target_changes': d.get('measurements', {}).get('target_changes')})
    return {'interpretation': 'Retrospective conclusion replay of existing saved results. Cases/cells/software calls are not pooled as a defect rate.',
            'empirical_case_count': len(empirical), 'bart_cases': b, 'bart_endpoint_status_counts': outcomes(generator),
            'consumer_cases': c, 'consumer_endpoint_status_counts': outcomes(consumer),
            'certificate_cohort_count': len(cert),
            'saved_constructed_software_records_indexed': sum(x['facts']['certificate_index']['records'] for x in bundle['certificate_evidence_index']),
            'current_constructed_software_examples': len(bundle.get('current_software_examples', [])),
            'current_software_outcomes': {x['case_id']: {k: v['status'] for k,v in x['decisions'].items()} for x in evaluated[len(empirical)+len(cert):]},
            'business_truth': 'UNKNOWN', 'new_external_events': 0, 'new_algorithm_experiments': 0}


def render_tex(summary):
    esc = lambda s: str(s).replace('_', r'\_')
    lines = [r'% Generated from saved_evidence.json by run_audit.py; retrospective, no new external cases.',
             r'\begin{tabular}{lrrrrr}', r'\toprule', r'BART case & Cells & Events & Position diff. & Min. cost & Optima \\', r'\midrule']
    for x in summary['bart_cases']:
        lines.append(' & '.join(esc(x.get(k, 'UNKNOWN')) for k in ['case_id','cells','events','position_differences','cost','optima']) + r' \\')
    lines += [r'\bottomrule', r'\end{tabular}', '', r'\begin{tabular}{lrrr}', r'\toprule',
              r'Consumer case & Cells & Native labels & Raw direct hits \\', r'\midrule']
    for x in summary['consumer_cases']:
        lines.append(' & '.join(esc(x[k]) for k in ['case_id','cells','native_labels','raw_hits']) + r' \\')
    lines += [r'\bottomrule', r'\end{tabular}', '% Native paths, equivalence decisions and unknowns are separate in the JSON ledger.']
    return '\n'.join(lines) + '\n'


def main(inp, out, expected_hash=None, profile_path=None):
    input_bytes = inp.read_bytes()
    actual_hash = hashlib.sha256(input_bytes).hexdigest()
    if expected_hash is None:
        if inp.resolve() != (HERE / 'inputs/saved_evidence.json').resolve():
            raise ValueError('custom input requires --expected-input-sha256')
        expected_hash = (HERE / 'inputs/saved_evidence.sha256').read_text().strip()
    if actual_hash != expected_hash:
        raise ValueError('portable input hash mismatch')
    bundle = parse(input_bytes)
    profile_path = profile_path or HERE / 'inventory_profile.json'
    profile_bytes = profile_path.read_bytes()
    profile = parse(profile_bytes)
    inventory_issues = validate_inventory(bundle, profile)
    if inventory_issues:
        raise ValueError('invalid inventory: ' + '; '.join(inventory_issues))
    evaluated = [evaluate_record(x) for x in bundle['records'] + bundle['certificate_evidence_index'] + bundle.get('current_software_examples', [])]
    summary = summarize(bundle, evaluated)
    ledger = {'schema': 'audit-audit-decision-ledger', 'input_sha256': actual_hash,
              'inventory_profile_id': profile['profile_id'], 'inventory_profile_sha256': hashlib.sha256(profile_bytes).hexdigest(),
              'code_sha256': {p: digest(HERE / p) for p in ['audit_rules.py','run_audit.py','build_inputs.py']},
              'source_files_reopened_during_replay': False, 'inventory_complete': True,
              'status_semantics': {'SUPPORTED': 'Selected bounded proposition follows from required saved evidence.',
                                   'CONTRADICTED': 'Selected equivalence/proposition fails; not automatically a producer or benchmark bug.',
                                   'UNKNOWN': 'Missing, malformed, ambiguous or insufficient evidence; no branch substitution.',
                                   'NOT_APPLICABLE': 'Declared test has no endpoint denominator for this case.'},
              'cases': evaluated[:len(bundle['records'])],
              'certificate_evidence_index': evaluated[len(bundle['records']):len(bundle['records'])+len(bundle['certificate_evidence_index'])],
              'current_software_examples': evaluated[len(bundle['records'])+len(bundle['certificate_evidence_index']):],
              'legacy_wrong_authority_context': bundle.get('legacy_wrong_authority_context'),
              'summary': summary}
    out.mkdir(parents=True, exist_ok=True)
    for name, obj in [('case_ledger.json', ledger), ('numeric_summary.json', summary)]:
        (out / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    with (out / 'case_ledger.csv').open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['case_id','family','proposition','status','reason','scope','unknown'])
        for x in evaluated:
            for k, v in x['decisions'].items():
                w.writerow([x['case_id'], x['family'], k, v['status'], v['reason'], x['scope'], '; '.join(x['unknown'])])
    (out / 'audit_decision_table.tex').write_text(render_tex(summary))
    print(json.dumps({'ledger_sha256': digest(out / 'case_ledger.json'), 'empirical_cases': len(bundle['records']),
                      'certificate_cohorts': len(bundle['certificate_evidence_index']), 'source_files_reopened': False}))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input', type=Path, default=HERE / 'inputs/saved_evidence.json')
    ap.add_argument('--expected-input-sha256')
    ap.add_argument('--inventory-profile', type=Path, help='Explicit alternative declared scope; default is the fixed study inventory profile.')
    ap.add_argument('--output-dir', type=Path, default=HERE / 'results')
    args = ap.parse_args()
    main(args.input, args.output_dir, args.expected_input_sha256, args.inventory_profile)
