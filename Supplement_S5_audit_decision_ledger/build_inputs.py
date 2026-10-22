"""Project pinned author result files into portable value-free evidence.

Reads saved JSON/JSONL only. Does not import upstream programs or rerun experiments.
Source hashes are required to match source_lock.json; no automatic lock refresh.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BART = 'Supplement_S2_BART_external_audit'
BLIND = 'Supplement_S3_BART_CSV_only_matching/bart_csv_only_matching'
CONSUMER = 'Supplement_S4_Raha_Baran_consumer_audit'
ROBUST = 'Supplement_S1_reference_experiment/results/robustness'
CONSUMERS = ['beers', 'flights', 'hospital', 'movies_1', 'rayyan', 'tax', 'toy']
COHORTS = ['valid', 'extended', 'refusal', 'tamper', 'idempotence', 'gold_independence']
SOURCE_PATHS = [
    BART + '/audit_results/all_cases.json', BART + '/audit_results/native_scorer_probes.json',
    BART + '/audit_results/native_scorer_execution_receipt.json', BART + '/native_applied_01/run_manifest.json',
    BLIND + '/results/blind_results.json', BLIND + '/results/reveal_results.json',
    BLIND + '/seals/BLIND_SEAL.json', BLIND + '/seals/REVEAL_SEAL.json',
    CONSUMER + '/raha_candidate_protocol_proposal.json', CONSUMER + '/PROTOCOL_FROZEN.md',
    CONSUMER + '/results/independent_verification.json',
    ROBUST + '/robustness_receipt.json', ROBUST + '/saved_records_recheck.json',
] + [CONSUMER + '/results/' + x + '_native.json' for x in CONSUMERS] + [ROBUST + '/' + x + '_cases.jsonl' for x in COHORTS]


def sha(b):
    return hashlib.sha256(b).hexdigest()


def unique_object(pairs):
    d = {}
    for k, v in pairs:
        if k in d:
            raise ValueError('duplicate JSON key: ' + k)
        d[k] = v
    return d


def parse(s):
    return json.loads(s, object_pairs_hook=unique_object,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError('nonfinite JSON constant ' + x)))


def load_pinned(root, lock):
    expected = {x['path']: x for x in lock['sources']}
    if set(expected) != set(SOURCE_PATHS):
        raise ValueError('lock does not cover exact source allowlist')
    data = {}
    for rel in SOURCE_PATHS:
        p = (root / rel).resolve()
        if root.resolve() not in p.parents:
            raise ValueError('source escaped root')
        b = p.read_bytes()
        if sha(b) != expected[rel]['sha256'] or len(b) != expected[rel]['bytes']:
            raise ValueError('source hash/size changed: ' + rel)
        data[rel] = b
    return data


def keyed(rows, field):
    out = {}
    for x in rows:
        if x[field] in out:
            raise ValueError('duplicate record identifier: ' + x[field])
        out[x[field]] = x
    return out


def optional_boolean(record, key):
    if key not in record:
        return None
    if type(record[key]) is not bool:
        raise ValueError('malformed optional boolean: ' + key)
    return record[key]


def main(root, output):
    lock = parse((HERE / 'source_lock.json').read_text())
    data = load_pinned(root, lock)
    source_map = {x['path']: x for x in lock['sources']}
    js = lambda p: parse(data[p])
    refs = lambda *paths: [source_map[p] for p in paths]
    records = []

    native_path = BART + '/audit_results/all_cases.json'
    blind_path, reveal_path = BLIND + '/results/blind_results.json', BLIND + '/results/reveal_results.json'
    native_rows = js(native_path)
    blind, reveal = js(blind_path), js(reveal_path)
    bmap, rmap = keyed(blind['cases'], 'case_id'), keyed(reveal['cases'], 'case_id')
    run_manifest_path = BART + '/native_applied_01/run_manifest.json'
    roster = [x['case_id'] for x in js(run_manifest_path)]
    if len(set(roster)) != len(roster) or set(keyed(native_rows, 'case_id')) != set(roster) or set(bmap) != set(roster) or set(rmap) != set(roster):
        raise ValueError('BART complete roster mismatch')
    if reveal['blind_results_sha256'] != sha(data[blind_path]):
        raise ValueError('reveal points to another blind result')
    for seal_name in ['BLIND_SEAL', 'REVEAL_SEAL']:
        for art in js(BLIND + '/seals/' + seal_name + '.json')['artifacts']:
            rel = BLIND + '/' + art['path']
            if rel in data and sha(data[rel]) != art['sha256']:
                raise ValueError('sealed input mismatch: ' + rel)
    probes_path = BART + '/audit_results/native_scorer_probes.json'
    probe_receipt_path = BART + '/audit_results/native_scorer_execution_receipt.json'
    probe_receipts = keyed(js(probe_receipt_path), 'case_id')
    for i, c in enumerate(native_rows):
        name, b, r = c['case_id'], bmap[c['case_id']], rmap[c['case_id']]
        if any(b['input_sha256'][k] != c['input_hashes'][k] for k in b['input_sha256']):
            raise ValueError('matching snapshots differ from native run')
        h = b['minimum_hamming']
        support = [{'cell_index': j + 1, 'label_options': x['possible_changed_labels'],
                    'target_option_count': len(set(x['possible_clean_target_values']))}
                   for j, x in enumerate(h['cell_target_and_label_support'])]
        ncon = r['native_concordance']
        n = {'events': c['events'], 'changes': c['realized_changes'], 'unexplained': c['unexplained_changes'],
             'unrealized': c['unrealized_nonnoop_events'], 'value_mismatches': c['event_value_mismatches'],
             'noop_events': c['noop_events'],
             'identity_crosswalk_valid': ncon['csv_crosswalk_order_and_values_equal'],
             'independent_events_present': ncon['event_json_csv_equal']}
        # Distinct saved event objects and changes must have the reported cardinalities.
        if len(r['native_events']) != n['events'] or len(r['native_changes']) != n['changes']:
            raise ValueError('native count disagrees with revealed event/change records')
        facts = {'rows': c['rows'], 'cells': c['cells'], 'columns': len(b['schema']), 'native': n,
                 'position': {**{k: r['position_scores']['counts'][k] for k in ['tp','fp','fn','tn','target_correct']},
                              'apparent_changes': c['positional_cell_differences']},
                 'matching': {'cost_matrix': h['cost_matrix_dirty_by_clean'], 'saved_cost': h['optimal_total_hamming_cost'],
                              'saved_optima': h['optimal_assignment_count'], 'all_optima_enumerated': h['all_optimal_assignments_enumerated'],
                              'cell_support': support, 'row_bags_equal': b['multiset']['equal']},
                 'reveal_bounds': {k: {z: x[z] for z in ['min','max']} for k, x in r['minimum_hamming_score_bounds']['counts'].items()},
                 'snapshot_hashes': c['input_hashes']}
        srcs = refs(native_path, blind_path, reveal_path)
        if name in probe_receipts:
            receipt, probes = probe_receipts[name], js(probes_path)
            if receipt['returncode'] != 0 or receipt['output_sha256'] != sha(data[probes_path]):
                raise ValueError('saved scorer probe receipt mismatch')
            facts['documentation'] = {'probe_cells': c['exported_events'], 'wiki_mismatches': c['wiki_contract_mismatches'],
                                      'implementation_mismatches': c['implementation_contract_mismatches'],
                                      'snapshot_probe': probes['snapshot_clean_probe'], 'documented_probe': probes['documented_clean_column_probe']}
            srcs += refs(probes_path, probe_receipt_path)
        records.append({'case_id': name, 'family': 'generator',
                        'requested_claims': ['native_event_fidelity','position_semantic_equivalence','csv_all_optima_determinacy',
                                             'csv_all_optima_native_agreement','documented_value_equivalence'],
                        'scope': 'One saved exploratory native apply/export run at pinned BART; exact decoded CSV strings; no new run.',
                        'source_refs': srcs, 'facts': facts,
                        'evidence_index': {'native': native_path + '#/' + str(i), 'matching': blind_path + '#/cases/' + str(i) + '/minimum_hamming',
                                           'cell_support_transform': 'For each saved support, retain label options and distinct target cardinality; omit all values.',
                                           'position_and_bounds': reveal_path + '#/cases/' + str(i)}})

    ivpath = CONSUMER + '/results/independent_verification.json'
    imap = keyed(js(ivpath)['cases'], 'name')
    inventory_path = CONSUMER + '/raha_candidate_protocol_proposal.json'
    consumer_roster = [x['name'] for x in js(inventory_path)['roster']]
    if set(consumer_roster) != set(CONSUMERS) or set(imap) != set(CONSUMERS):
        raise ValueError('consumer inventory mismatch')
    for name in consumer_roster:
        p = CONSUMER + '/results/' + name + '_native.json'
        c, ind = js(p), imap[name]
        if c['status'] != 'completed' or ind['native_file_sha256'] != sha(data[p]):
            raise ValueError('consumer final result/independent receipt mismatch')
        e1, e2, e3, e4 = [c[x] for x in ['E1','E2','E3','E4']]
        raw, norm = e3['native_coordinates_raw_clean'], e3['native_coordinates_native_clean']
        facts = {'rows': c['rows'], 'cells': c['cells_per_pair_side'], 'columns': c['columns'],
                 'stratum': c['stratum'], 'positional_interface': True,
                 'labels': {'raw': e1['raw_labels']['count'], 'native': e1['native_labels']['count'],
                            'removed': e1['label_delta']['removed_count'], 'added': e1['label_delta']['added_count'],
                            'common': e1['label_delta']['common_count'],
                            'raw_coordinates_sha256': e1['raw_labels']['coordinates_sha256'],
                            'native_coordinates_sha256': e1['native_labels']['coordinates_sha256']},
                 'persistence': {'dirty_nonidempotent': ind['nonidempotent_dirty_values'], 'clean_nonidempotent': ind['nonidempotent_clean_values'],
                                 'dirty_value_changes': e2['dirty_value_changes']['count'], 'clean_value_changes': e2['clean_value_changes']['count'],
                                 'removed_labels': e2['label_delta']['removed_count'], 'added_labels': e2['label_delta']['added_count'],
                                 'target_changes': e2['common_error_target_changes']['count'],
                                 'dirty_digest_equal': c['native_dirty_table_sha256'] == e2['reloaded_dirty_table_sha256'],
                                 'clean_digest_equal': c['native_clean_table_sha256'] == e2['reloaded_clean_table_sha256'],
                                 'labels_digest_equal': e1['native_labels']['coordinates_sha256'] == e2['reloaded_labels']['coordinates_sha256'],
                                 'targets_digest_equal': e1['native_labels']['target_values_sha256'] == e2['reloaded_labels']['target_values_sha256']},
                 'probes': {'normalized_direct_scores': norm['native_scores'], 'normalized_materialized_scores': norm['materialized_native_scores'],
                            'raw_direct_scores': raw['native_scores'], 'raw_materialized_scores': raw['materialized_native_scores'],
                            'raw_to_materialized_target_changes': raw['common_target_changes'],
                            'raw_normalized_coordinates_equal': raw['dictionary']['coordinates_sha256'] == norm['dictionary']['coordinates_sha256']},
                 'selfpairs': {'dirty_labels': e4['dirty_self_pair']['labels']['count'], 'clean_labels': e4['clean_self_pair']['labels']['count'],
                               'dirty_empty_scores': e4['dirty_self_pair']['empty_probe_scores'], 'clean_empty_scores': e4['clean_self_pair']['empty_probe_scores']}}
        records.append({'case_id': name, 'family': 'consumer',
                        'requested_claims': ['raw_native_label_equivalence','official_persistence','native_probe_exactness','raw_direct_value_equivalence','selfpair_zero_labels'],
                        'scope': 'All cells of one fixed released pair under official row/column positions and normalizer; no independently certified entity identity or business truth.',
                        'source_refs': refs(p, ivpath), 'facts': facts,
                        'evidence_index': {'labels': p + '#/E1', 'persistence': p + '#/E2', 'probes': p + '#/E3',
                                           'selfpairs': p + '#/E4', 'idempotence': ivpath + '#/cases[name=' + name + ']'}})

    receipt_path = ROBUST + '/robustness_receipt.json'
    receipt = js(receipt_path)
    certificate_records = []
    all_ids = set()
    for cohort in COHORTS:
        path = ROBUST + '/' + cohort + '_cases.jsonl'
        if receipt['files'][Path(path).name]['sha256'] != sha(data[path]):
            raise ValueError('certificate receipt hash mismatch')
        stat = Counter()
        available = Counter()
        kinds, statuses, failures = Counter(), Counter(), Counter()
        ids = set()
        base_ids = set()
        exceptions = []
        for line_number, line in enumerate(data[path].splitlines(), 1):
            x = parse(line)
            ident, check, pred = x['case_id'], x['checker'], x['prediction']
            if ident in ids or ident in all_ids:
                raise ValueError('duplicate certificate case')
            ids.add(ident); all_ids.add(ident)
            base_ids.add(x['base_id'])
            stat['records'] += 1
            for field in ['valid']:
                if type(check[field]) is not bool:
                    raise ValueError('nonboolean checker outcome')
            if type(pred['answered']) is not bool or type(x['expected_valid']) is not bool:
                raise ValueError('nonboolean prediction/expectation')
            stat['checker_valid'] += int(check['valid'])
            stat['answered'] += int(pred['answered'])
            stat['resolved'] += int(check['protocol_status'] == 'RESOLVED')
            stat['certificate_present'] += int(pred['certificate'] is not None)
            stat['expected_checker_agreement'] += int(check['valid'] == x['expected_valid'])
            stat['expected_valid_true'] += int(x['expected_valid'])
            for field in ['input_preserved','patch_exact','rebuild_exact']:
                optional_boolean(x, field)
            stat['input_preserved'] += int(x.get('input_preserved') is True)
            available['input_preserved'] += int('input_preserved' in x)
            if check['valid'] != x['expected_valid']:
                exceptions.append(line_number)
            for field in ['patch_exact','rebuild_exact']:
                stat[field] += int(x.get(field) is True)
                available[field] += int(field in x)
            if 'direct_rebuild' in x:
                available['same_edges'] += 1
                # Canonicalize whole bindings including qualifiers; sort without losing duplicates.
                canon = lambda edges: sorted(json.dumps(e, sort_keys=True, separators=(',', ':')) for e in edges)
                stat['same_edges'] += int(canon(x['direct_rebuild']['edges']) == canon(pred['edges']))
            kinds[x['kind']] += 1
            statuses[check['protocol_status']] += 1
            failures[str(check['failure'])] += 1
        if stat['records'] != receipt['files'][Path(path).name]['records']:
            raise ValueError('certificate cohort count mismatch')
        fields = ['records','checker_valid','answered','resolved','certificate_present','expected_valid_true','expected_checker_agreement','input_preserved','patch_exact','rebuild_exact','same_edges']
        facts = {'certificate_index': {**{k: stat[k] for k in fields}, 'cohort': cohort, 'unique_case_ids': len(ids),
                                       'unique_base_ids': len(base_ids),
                                       'field_available': {k: available[k] for k in ['patch_exact','rebuild_exact','same_edges','input_preserved']},
                                       'kinds': dict(kinds), 'protocol_statuses': dict(statuses), 'checker_failures': dict(failures),
                                       'exception_line_numbers': exceptions, 'source_line_range': [1, stat['records']]}}
        certificate_records.append({'case_id': 'reference/' + cohort, 'family': 'reference_certificate',
                                    'requested_claims': (['given_authority_exactness'] if cohort in ['valid','extended'] else []) + ['saved_protocol_checks'],
                                    'scope': 'Previously executed constructed software checks of supplied complete-authority projection; reused declarations, not external incidents.',
                                    'source_refs': refs(path, receipt_path), 'facts': facts,
                                    'evidence_index': {'all_rows': path + '#lines=1-' + str(stat['records']),
                                                       'transform': 'Stream all rows; aggregate typed outcome fields and full binding equality, retaining multiplicity. No source names, bindings or values copied.'}})
    if len(all_ids) != receipt['unique_cases']:
        raise ValueError('certificate global case count mismatch')
    # One separately executed, fully authored current example. It is neither
    # an additional external case nor part of the historical regression cohorts.
    sw = HERE / 'software_example'
    summary = parse((sw / 'result_summary.json').read_text())
    for item in summary['source_refs']:
        if sha((sw / item['path']).read_bytes()) != item['sha256']:
            raise ValueError('current software example source changed: ' + item['path'])
    a = parse((sw / 'author_case.json').read_text())
    task = parse((sw / 'input_task.json').read_text())
    prediction = parse((sw / 'patch_result.json').read_text())
    check = parse((sw / 'check_result.json').read_text())
    if task != a['task_with_incorrect_asserted_authority']:
        raise ValueError('constructed input differs from declared example')
    canon = lambda edges: sorted(json.dumps(e, sort_keys=True, separators=(',', ':')) for e in edges)
    original_match = canon(prediction['edges']) == canon(a['constructed_original']['expected_edges'])
    supplied_match = canon(prediction['edges']) == canon(a['constructed_asserted_authority_projection'])
    for field in ['valid']:
        optional_boolean(check, field)
    optional_boolean(prediction, 'answered')
    software_refs = []
    for name in ['author_case.json','input_task.json','patch_result.json','check_result.json','execution_receipt.json','code_manifest.json']:
        bb = (sw / name).read_bytes()
        software_refs.append({'path': 'software_example/' + name, 'sha256': sha(bb), 'bytes': len(bb)})
    software_record = {'case_id': summary['case_id'], 'family': 'reference_certificate',
                       'requested_claims': ['constructed_supplied_authority_acceptance','constructed_original_agreement'],
                       'scope': 'One current fully author-constructed software example, separate from eleven external cases and all historical software cohorts.',
                       'source_refs': software_refs,
                       'facts': {'constructed_authority': {'verifier_valid': check['valid'], 'answered': prediction['answered'],
                                  'protocol_status': check['protocol_status'], 'certificate_schema': prediction['certificate']['schema'],
                                  'complete_assertion': task['contract']['complete'],
                                  'matches_constructed_original': original_match, 'matches_supplied_projection': supplied_match,
                                  'intent_basis': 'author_constructed_original',
                                  'added_occurrences': len(prediction['certificate']['added']),
                                  'removed_occurrences': len(prediction['certificate']['removed'])}},
                       'evidence_index': {'actual_check': 'software_example/check_result.json',
                                          'actual_output_vs_authored_original': 'software_example/patch_result.json#/edges versus software_example/author_case.json#/constructed_original/expected_edges',
                                          'original_intent_limit': 'Literal author definition only; never supplied to patch/checker; no business gold.'}}
    bundle = {'schema': 'audit-contract-evidence', 'source_lock_sha256': sha((HERE / 'source_lock.json').read_bytes()),
              'scope': 'Bounded reinterpretation of saved results; not a new empirical study or a general repair tool.',
              'expected_inventory': {'generator': roster, 'consumer': consumer_roster,
                                     'reference_certificate': ['reference/' + x for x in COHORTS] + [summary['case_id']]},
              'records': records, 'certificate_evidence_index': certificate_records,
              'current_software_examples': [software_record],
              'legacy_wrong_authority_context': summary['legacy_context_only'],
              'provenance': {'sources': lock['sources'], 'source_hashes_verified_at_extraction': True,
                             'third_party_raw_copied': False, 'extractor_sha256': sha(Path(__file__).read_bytes()),
                             'portable_boundary': 'Author result counts, hashes, distance matrices and support cardinalities; no CSV rows, cell strings, metric declarations or bindings.'}}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(bundle, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'output': str(output), 'sha256': sha(output.read_bytes()), 'empirical_cases': len(records),
                      'certificate_cohorts': len(certificate_records), 'saved_software_records_indexed': len(all_ids), 'current_software_examples': 1}))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo-root', type=Path, required=True)
    ap.add_argument('--output', type=Path, default=HERE / 'inputs' / 'saved_evidence.json')
    args = ap.parse_args()
    main(args.repo_root, args.output)
